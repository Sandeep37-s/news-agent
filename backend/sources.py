import html
import ipaddress
import os
import re
import socket
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin
import feedparser
import httpx

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
    for attempt in range(3):
        try:
            with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
                current = url
                for _ in range(5):
                    public_url(current)
                    with client.stream('GET', current, headers={'User-Agent':'HindiNewsStudio/1.0 (RSS reader)', **(headers or {})}) as response:
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
                            content.extend(chunk)
                            if len(content)>2_000_000:
                                raise ValueError('Source response exceeds 2 MB')
                        return bytes(content)
                raise ValueError('Too many source redirects')
        except (httpx.TimeoutException,httpx.NetworkError):
            if attempt==2:
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
        rows=parse_feed(fetch_bytes(source.url))
        if source.options.get('headlines_only'):
            # Discovery mode retains a link and minimal feed metadata, not article
            # excerpts, images, transcripts or footage for downstream republishing.
            rows=[{**row,'summary':''} for row in rows]
        return rows

class JSONAdapter:
    """Licensed API/search adapter: JSON list under items_key, configurable field map."""
    def collect(self, source):
        import json
        options=source.options
        key=os.environ.get(options.get('api_key_env',''),'')
        data=json.loads(fetch_bytes(source.url, {'Authorization':f'Bearer {key}'} if key else None))
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
        return [r for r in result if r['title']]

ADAPTERS={'rss':RSSAdapter(), 'json':JSONAdapter()}
