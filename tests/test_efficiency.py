"""Measure reduced work, while testing cache correctness and worker recovery."""
import json
from datetime import datetime,timezone
from email.utils import format_datetime
from unittest.mock import patch
import httpx
import pytest
from sqlalchemy import select,event,func
from backend.db import Source,Story,Article,Session,engine,now
from backend.sources import RSSAdapter,FetchResult,SourceBatch,source_key,fetch_bytes,parse_feed,SourceBudgetExceeded
from backend.monitor import run_monitor
from backend.editorial import research
from test_workflows import configure


def rss():
    return ('<rss version="2.0"><channel><title>Test</title><item><title>India science policy announced</title><link>https://example.com/story</link><description>Attributed programme announcement</description><pubDate>'+format_datetime(datetime.now(timezone.utc))+'</pubDate></item></channel></rss>').encode()


def test_conditional_poll_skips_unchanged_download_parsing_and_duplicate_work(db):
    configure(db)
    enabled=list(db.scalars(select(Source).where(Source.enabled==True)))
    for source in enabled[1:]:source.enabled=False
    db.commit()
    requests=[]
    def serve(request):
        requests.append(request)
        return httpx.Response(304) if len(requests)>1 else httpx.Response(200,content=rss(),headers={'etag':'"v1"','last-modified':'Wed, 21 Oct 2026 00:00:00 GMT'})
    real_client=httpx.Client
    with patch('backend.sources.public_url'),patch('backend.sources.httpx.Client',side_effect=lambda **kw:real_client(transport=httpx.MockTransport(serve),**kw)),patch('backend.sources.parse_feed',wraps=parse_feed) as parser:
        first=run_monitor();second=run_monitor()
    assert first['status']==second['status']=='success'
    assert first['articles']==1 and second['articles']==second['new_stories']==0
    assert second['sources'][0]['status']=='not_modified'
    assert requests[1].headers['if-none-match']=='"v1"'
    assert requests[1].headers['if-modified-since']=='Wed, 21 Oct 2026 00:00:00 GMT'
    assert parser.call_count==1
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(Article))==1
    assert db.get(Source,enabled[0].id).fetch_state['etag']=='"v1"'


def test_source_option_changes_invalidate_old_validators_and_apply_discovery_mode():
    source=Source(kind='rss',url='https://example.com/feed',options={})
    source.fetch_state={'config_key':source_key(source),'etag':'"before"'}
    source.options={'headlines_only':True}
    with patch('backend.sources.fetch_bytes',return_value=FetchResult(rss(),validators={'etag':'"after"'})) as fetch:
        batch=RSSAdapter().collect(source)
    assert fetch.call_args.args[1]=={}
    assert batch and batch[0]['summary']==''
    assert batch.fetch_state['etag']=='"after"'


def test_cached_304_still_recovers_research_interrupted_after_ingestion(db):
    configure(db)
    enabled=list(db.scalars(select(Source).where(Source.enabled==True)))
    for source in enabled[1:]:source.enabled=False
    db.commit();calls=[]
    def serve(request):
        calls.append(request)
        return httpx.Response(304) if len(calls)>1 else httpx.Response(200,content=rss(),headers={'etag':'"recover"'})
    real_client=httpx.Client
    with patch('backend.sources.public_url'),patch('backend.sources.httpx.Client',side_effect=lambda **kw:real_client(transport=httpx.MockTransport(serve),**kw)):
        with patch('backend.monitor.build_research',side_effect=RuntimeError('interrupted')):
            assert run_monitor()['status']=='failed'
        recovered=run_monitor()
    db.expire_all()
    assert recovered['status']=='success' and recovered['articles']==0
    assert recovered['sources'][0]['status']=='not_modified'
    assert db.scalar(select(Story)).research['provider']=='extractive'


def test_empty_feeds_do_not_acquire_a_successful_cache_validator():
    source=Source(kind='rss',url='https://example.com/feed',options={})
    with patch('backend.sources.fetch_bytes',return_value=FetchResult(b'<rss version="2.0"><channel><title>Empty</title></channel></rss>',validators={'etag':'"empty"'})):
        batch=RSSAdapter().collect(source)
    assert batch==[] and batch.fetch_state=={} and not batch.not_modified


def test_unexpected_304_does_not_masquerade_as_a_successful_feed():
    real_client=httpx.Client
    with patch('backend.sources.public_url'),patch('backend.sources.httpx.Client',side_effect=lambda **kw:real_client(transport=httpx.MockTransport(lambda _:httpx.Response(304)),**kw)):
        with pytest.raises(ValueError,match='without a cached validator'):
            fetch_bytes('https://example.com/feed')


def test_source_time_budget_stops_stream_processing_without_retries():
    calls=[]
    def serve(request):
        calls.append(request);return httpx.Response(200,content=b'content')
    real_client=httpx.Client
    with patch('backend.sources.public_url'),patch('backend.sources.time.monotonic',side_effect=[0,0,0,31]),patch('backend.sources.httpx.Client',side_effect=lambda **kw:real_client(transport=httpx.MockTransport(serve),**kw)):
        with pytest.raises(SourceBudgetExceeded):
            fetch_bytes('https://example.com/feed')
    assert len(calls)==1


def test_old_stories_are_ranked_with_two_article_reads_for_300_stories(db):
    configure(db)
    source=db.scalar(select(Source).where(Source.enabled==True))
    staged=[]
    for index in range(300):
        story=Story(id=f'cost-{index:04d}',title=f'India science policy {index}',fingerprint=f'cost-{index:04d}',region='india',category='national',research={'provider':'extractive'})
        db.add(story)
        staged.append(Article(story_id=story.id,source_id=source.id,title=story.title,summary='',url=f'https://example.com/{index}',publisher=source.name,published_at=now(),origin_group='unknown'))
    db.flush();db.add_all(staged)
    db.commit()
    reads=[]
    def count_reads(conn,cursor,statement,*args):
        if statement.lstrip().lower().startswith('select') and 'from articles' in statement.lower():reads.append(statement)
    class Empty:
        def collect(self,source):return []
    event.listen(engine,'before_cursor_execute',count_reads)
    try:run_monitor({'rss':Empty()})
    finally:event.remove(engine,'before_cursor_execute',count_reads)
    assert len(reads)==2
    db.expire_all()
    assert all(s.scoring.get('age_hours') is not None for s in db.scalars(select(Story)))


def test_ingestion_commits_per_source_instead_of_per_article(db):
    configure(db)
    class Many:
        def collect(self,source):
            return [{'title':f'India science policy {n}','summary':'Attributed statement','url':f'https://example.com/{source.id}/{n}','published_at':now(),'event_at':None} for n in range(60)]
    commits=[];before_research=[]
    def count_commit(session):commits.append(True)
    def review(db,story,articles,settings):
        if not before_research:before_research.append(len(commits))
        return research(story,articles)
    event.listen(Session.class_,'after_commit',count_commit)
    try:
        with patch('backend.monitor.build_research',side_effect=review):result=run_monitor({'rss':Many()})
    finally:event.remove(Session.class_,'after_commit',count_commit)
    assert result['status']=='success' and result['articles']==120 and result['new_stories']==60
    assert before_research==[3]  # Start record + one commit for each of the two feeds.
    assert len(commits)<=6  # Batched research, outbox and final run state; AI is off.


def test_cache_is_internal_and_source_edits_clear_it(db,client):
    source=db.scalar(select(Source));source.fetch_state={'config_key':source_key(source),'etag':'"old"'};db.commit()
    body=next(row for row in client.get('/api/sources').json() if row['id']==source.id)
    assert 'fetch_state' not in body
    body['options']={**body['options'],'headlines_only':True}
    with patch('backend.api.public_url'):
        assert client.put('/api/sources/'+source.id,json=body).status_code==200
    db.expire_all();assert db.get(Source,source.id).fetch_state=={}
