import html
import hashlib
import json
import ipaddress
import os
import re
import socket
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin
import feedparser
import httpx
from .config import env


class SourceBudgetExceeded(ValueError):
    pass


class FetchResult(bytes):
    def __new__(cls,content=b'',*,validators=None,not_modified=False):
        obj=super().__new__(cls,content)
        obj.validators=validators or {}
        obj.not_modified=not_modified
        return obj


class SourceBatch(list):
    def __init__(self,rows=(),*,fetch_state=None,not_modified=False):
        super().__init__(rows)
        self.fetch_state=fetch_state or {}
        self.not_modified=not_modified


def source_key(source):
    value=json.dumps([source.url,source.kind,source.options or {}],sort_keys=True)
    return hashlib.sha256(value.encode()).hexdigest()


def conditional_headers(source):
    state=getattr(source,'fetch_state',None) or {}
    if state.get('config_key')!=source_key(source):
        return {}
    return {header:state[key] for header,key in [('If-None-Match','etag'),('If-Modified-Since','last_modified')] if state.get(key)}


def source_batch(source,body,rows=()):
    not_modified=getattr(body,'not_modified',False)
    validators=getattr(body,'validators',{})
    if not_modified:
        validators={**(getattr(source,'fetch_state',None) or {}),**validators}
    state={'config_key':source_key(source),**{key:validators[key] for key in ('etag','last_modified') if validators.get(key)}}
    return SourceBatch(rows,fetch_state=state if rows or not_modified else {},not_modified=not_modified)

def clean(value, limit=600):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', '', str(value or '')))).strip()[:limit]

def canonical(url):
    p = urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:
        raise ValueError('Invalid public HTTP source URL')
    query = [(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')]
    return urlunsplit((p.scheme,p.netloc.lower(),p.path or '/',urlencode(sorted(query)),''))

def public_url(url):
    p = urlsplit(canonical(url))
    if p.port not in (None,80,443):
        raise ValueError('Only public HTTP ports are permitted')
    addresses = socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Private and special-use source destinations are blocked')
    return url

def fetch_bytes(url, headers=None):
    # Every redirect is validated. Production also requires outbound network restrictions.
    deadline=time.monotonic()+env.source_fetch_budget_seconds
    for attempt in range(env.source_max_attempts):
        try:
            with httpx.Client(timeout=env.source_request_timeout_seconds, follow_redirects=False, trust_env=False) as client:
                current = url
                for _ in range(5):
                    remaining=deadline-time.monotonic()
                    if remaining<=0:
                        raise SourceBudgetExceeded('Source fetch time budget exceeded')
                    public_url(current)
                    remaining=deadline-time.monotonic()
                    if remaining<=0:
                        raise SourceBudgetExceeded('Source fetch time budget exceeded')
                    with client.stream('GET', current, timeout=min(remaining,env.source_request_timeout_seconds), headers={'User-Agent':'HindiNewsStudio/1.0 (RSS reader)', **(headers or {})}) as response:
                        validators={}
                        for key,header in [('etag','etag'),('last_modified','last-modified')]:
                            value=response.headers.get(header,'')
                            if value and len(value)<=1024 and value.isascii() and '\r' not in value and '\n' not in value:
                                validators[key]=value
                        if response.status_code==304:
                            if not any(key.lower() in ('if-none-match','if-modified-since') for key in (headers or {})):
                                raise ValueError('Unexpected not-modified response without a cached validator')
                            return FetchResult(validators=validators,not_modified=True)
                        if response.is_redirect:
                            target=urljoin(current,response.headers['location'])
                            old_origin,new_origin=urlsplit(current),urlsplit(target)
                            if old_origin.scheme=='https' and new_origin.scheme!='https':
                                raise ValueError('HTTPS source redirects must remain HTTPS')
                            if (new_origin.scheme,new_origin.netloc)!=(old_origin.scheme,old_origin.netloc):
                                headers = None
                            current=target
                            continue
                        response.raise_for_status()
                        content=bytearray()
                        for chunk in response.iter_bytes():
                            if time.monotonic()>deadline:
                                raise SourceBudgetExceeded('Source fetch time budget exceeded')
                            content.extend(chunk)
                            if len(content)>2_000_000:
                                raise ValueError('Source response exceeds 2 MB')
                        return FetchResult(content,validators=validators)
                raise ValueError('Too many source redirects')
        except (httpx.TimeoutException,httpx.NetworkError):
            if attempt==env.source_max_attempts-1:
                raise
            time.sleep(2**attempt)

def parsed_date(value):
    if not value:
        return None
    try:
        if isinstance(value, str):
            dt=datetime.fromisoformat(value.replace('Z','+00:00'))
            if not dt.tzinfo:
                return None
            return dt.astimezone(timezone.utc).isoformat()
        return datetime(*value[:6], tzinfo=timezone.utc).isoformat()
    except (TypeError,ValueError,OverflowError):
        return None

def parse_feed(content):
    feed=feedparser.parse(content)
    if feed.bozo and not feed.entries:
        raise ValueError('Invalid RSS or Atom document')
    result=[]
    for e in feed.entries[:100]:
        try:
            url=canonical(e.get('link',''))
        except ValueError:
            continue
        title=clean(e.get('title'),300)
        if title:
            result.append({'title':title,'summary':clean(e.get('summary',''),500),'url':url,'published_at':parsed_date(e.get('published_parsed') or e.get('updated_parsed')),'event_at':None})
    return result

class RSSAdapter:
    def collect(self, source):
        body=fetch_bytes(source.url,conditional_headers(source))
        if getattr(body,'not_modified',False):
            return source_batch(source,body)
        rows=parse_feed(body)
        if source.options.get('headlines_only'):
            # Discovery mode retains a link and minimal feed metadata, not article
            # excerpts, images, transcripts or footage for downstream republishing.
            rows=[{**row,'summary':''} for row in rows]
        return source_batch(source,body,rows)

class JSONAdapter:
    """Licensed API/search adapter: JSON list under items_key, configurable field map."""
    def collect(self, source):
        import json
        options=source.options
        key=os.environ.get(options.get('api_key_env',''),'')
        headers={**conditional_headers(source),**({'Authorization':f'Bearer {key}'} if key else {})}
        body=fetch_bytes(source.url,headers)
        if getattr(body,'not_modified',False):
            return source_batch(source,body)
        data=json.loads(body)
        rows=data.get(options.get('items_key','articles'),[]) if isinstance(data,dict) else data
        if not isinstance(rows,list):
            raise ValueError('API result must be a list')
        mapping=options.get('fields',{})
        result=[]
        for row in rows[:100]:
            if not isinstance(row,dict):
                continue
            try:
                result.append({'title':clean(row.get(mapping.get('title','title')),300),'summary':clean(row.get(mapping.get('summary','description')),500),'url':canonical(row.get(mapping.get('url','url'),'')),'published_at':parsed_date(row.get(mapping.get('published_at','publishedAt'))),'event_at':parsed_date(row.get(mapping.get('event_at','eventAt')))})
            except ValueError:
                continue
        return source_batch(source,body,[r for r in result if r['title']])

ADAPTERS={'rss':RSSAdapter(), 'json':JSONAdapter()}
