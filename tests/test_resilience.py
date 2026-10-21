"""Failure-path checks for ingestion, outbox delivery, schema readiness and settings."""
import json
from unittest.mock import patch
import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from backend.api import SourceBody
from backend.config import env
from backend.db import Source,Story,Article,Notification,Setting
from backend.monitor import run_monitor
from backend.sources import JSONAdapter,fetch_bytes
from backend import telegram
from test_workflows import configure,FixtureAdapter


def test_json_adapter_keeps_valid_entries_in_mixed_response():
    rows=[None,7,'bad',[],{'title':'Missing link'},
          {'title':'Science programme announced','url':'https://example.com/good','publishedAt':'2026-10-21T00:00:00Z'}]
    source=Source(url='https://example.com/feed',options={})
    with patch('backend.sources.fetch_bytes',return_value=json.dumps({'articles':rows}).encode()):
        result=JSONAdapter().collect(source)
    assert len(result)==1 and result[0]['url']=='https://example.com/good'


def test_https_feed_redirect_cannot_downgrade_and_leak_credentials():
    seen=[]
    def handle(request):
        seen.append(request)
        return httpx.Response(302,headers={'location':'http://example.com/plain'})
    client=httpx.Client(transport=httpx.MockTransport(handle))
    with patch('backend.sources.public_url'),patch('backend.sources.httpx.Client',return_value=client):
        with pytest.raises(ValueError,match='remain HTTPS'):
            fetch_bytes('https://example.com/feed',{'Authorization':'Bearer fixture-token'})
    assert len(seen)==1


def test_feed_redirect_to_another_origin_strips_authorization():
    seen=[]
    def handle(request):
        seen.append(request)
        return httpx.Response(302,headers={'location':'https://other.example/feed'}) if len(seen)==1 else httpx.Response(200,content=b'feed')
    client=httpx.Client(transport=httpx.MockTransport(handle))
    with patch('backend.sources.public_url'),patch('backend.sources.httpx.Client',return_value=client):
        assert fetch_bytes('https://example.com/feed',{'Authorization':'Bearer fixture-token'})==b'feed'
    assert seen[0].headers.get('Authorization')=='Bearer fixture-token'
    assert 'Authorization' not in seen[1].headers


@pytest.mark.parametrize('status,payload,expected',[
    (502,'<html>gateway unavailable</html>','pending'),
    (429,'not json','pending'),
    (429,'{"parameters":{"retry_after":null}}','pending'),
    (429,'{"parameters":{"retry_after":999999999}}','failed'),
    (200,'<html>unreadable success</html>','uncertain'),
    (200,'[]','uncertain'),
    (200,'{"ok":"false"}','failed'),
])
def test_malformed_telegram_responses_do_not_crash_worker(monkeypatch,status,payload,expected):
    monkeypatch.setattr(env,'telegram_bot_token','fixture-private-token')
    monkeypatch.setattr(env,'telegram_chat_ids','123')
    with patch('httpx.Client.post',return_value=httpx.Response(status,text=payload)):
        state,error,delay=telegram.send('123','News')
    assert state==expected and 'fixture-private-token' not in error
    if status==429 and state=='pending': assert 1<=delay<=86400


def test_pending_alert_is_suppressed_if_it_no_longer_meets_threshold(db,monkeypatch):
    configure(db)
    monkeypatch.setattr(env,'telegram_bot_token','fixture')
    monkeypatch.setattr(env,'telegram_chat_ids','123')
    run_monitor({'rss':FixtureAdapter()},lambda *_:('pending','temporary failure',1))
    note=db.scalar(select(Notification));note.next_attempt='2000-01-01T00:00:00+00:00'
    settings=db.get(Setting,'monitoring');settings.value={**settings.value,'alert_threshold':100};db.commit()
    sent=[]
    run_monitor({'rss':FixtureAdapter()},lambda *_:(sent.append(True) or ('sent','',0)))
    db.expire_all()
    assert sent==[] and db.get(Notification,note.id).status=='suppressed'


def test_health_requires_current_schema_and_bootstrapped_settings(db,client):
    cfg=Config('alembic.ini')
    command.stamp(cfg,'002')
    result=client.get('/health')
    assert result.status_code==503 and result.json()['detail']=='Database migration required'
    command.stamp(cfg,'head')
    assert client.get('/health').json()=={'status':'ok'}
    db.delete(db.get(Setting,'picture_template'));db.commit()
    assert client.get('/health').status_code==503


def test_source_update_normalizes_url_and_prevents_duplicates(db,client):
    source=client.get('/api/sources').json()[0]
    source['url']='https://example.com/updated?utm_source=ignore&b=2#ignore'
    with patch('backend.api.public_url'):
        result=client.put('/api/sources/'+source['id'],json=source)
        assert result.status_code==200
        assert result.json()['url']=='https://example.com/updated?b=2'
        source['name']='Duplicate source';source['url']='https://example.com/updated?b=2'
        assert client.post('/api/sources',json=source).status_code==409


@pytest.mark.parametrize('options',[
    {'headlines_only':'false'}, {'fields':[]}, {'fields':{'title':None}},
    {'items_key':42}, {'api_key_env':[]}, {'terms_url':'javascript:alert(1)'},
])
def test_invalid_adapter_options_are_rejected_before_a_monitor_run(options):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SourceBody(name='Test source',url='https://example.com/feed',options=options)


def test_monitoring_rejects_empty_or_duplicate_categories(client):
    config=client.get('/api/settings').json()['monitoring']['value']
    for categories in [[],[''],['national','national']]:
        assert client.put('/api/settings/monitoring',json={**config,'categories':categories}).status_code==422
