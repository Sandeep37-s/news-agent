import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select,or_
from .db import Session, Run, Story, Article, Source, Setting, Notification, audit, now,uid
from .locking import monitoring_lock, AlreadyRunning
from .sources import ADAPTERS
from .editorial import classify, fingerprint, similar, rank
from .research import build_research
from .telegram import queue, deliver
from .worker_queries import ranking_batches,research_batches

def run_monitor(adapters=None,sender=None):
    adapters=adapters or ADAPTERS
    with monitoring_lock(), Session() as db:
        # Acquiring the process/database lock proves any previous running owner has exited.
        for stale in db.scalars(select(Run).where(Run.status=='running')):
            stale.status='interrupted'
            stale.finished_at=now()
        for n in db.scalars(select(Notification).where(Notification.status=='sending')):
            n.status='uncertain'
            n.error='Worker restarted during delivery; verify before retrying'
        run=Run()
        db.add(run)
        db.commit()
        settings=db.get(Setting,'monitoring').value
        sources={s.id:s for s in db.scalars(select(Source))}
        results=[]
        # A crash may have committed article records before research was written.
        # Resume that work even when the next feed fetch only contains known URLs.
        changed=set(db.scalars(select(Story.id).where(or_(Story.research['provider'].as_string().is_(None),Story.research['provider'].as_string()==''))))
        cutoff=(datetime.now(timezone.utc)-timedelta(hours=settings['max_age_hours'])).isoformat()
        try:
            for source in sources.values():
                if not source.enabled or source.category not in settings['categories']:
                    continue
                try:
                    rows=adapters[source.kind].collect(source)
                    if getattr(rows,'not_modified',False):
                        source.fetch_state=rows.fetch_state
                        results.append({'source':source.name,'status':'not_modified','retrieved':0,'added':0})
                        db.commit()
                        continue
                    added=0
                    valid=[row for row in rows if not row['published_at'] or cutoff<=row['published_at']<=now()]
                    known_urls=set(db.scalars(select(Article.url).where(Article.url.in_([row['url'] for row in valid])))) if valid else set()
                    identities={fingerprint(row['title'],classify(row['title'],source)[0]) for row in valid if row['url'] not in known_urls}
                    exact={story.fingerprint:story for story in db.scalars(select(Story).where(Story.fingerprint.in_(identities)))} if identities else {}
                    candidate_cache={}
                    pending_articles=[]
                    for row in valid:
                        if row['url'] in known_urls:
                            continue
                        region,category,sub=classify(row['title'],source)
                        fp=fingerprint(row['title'],region)
                        story=exact.get(fp)
                        if not story:
                            key=(region,category)
                            if key not in candidate_cache:
                                with db.no_autoflush:
                                    candidate_cache[key]=list(db.scalars(select(Story).where(Story.region==region,Story.category==category,Story.updated_at>=cutoff)))
                            candidates=candidate_cache[key]
                            story=next((s for s in candidates if similar(s.title,row['title'])),None)
                        if not story:
                            story=Story(id=uid(),title=row['title'],fingerprint=fp,region=region,category=category,subcategory=sub,status='awaiting_direction' if region=='global' else 'new')
                            db.add(story)
                            candidate_cache[(region,category)].append(story)
                            run.new_stories+=1
                        exact[fp]=story
                        pending_articles.append(Article(**row,source_id=source.id,story_id=story.id,publisher=source.name,origin_group=source.origin_group))
                        known_urls.add(row['url'])
                        changed.add(story.id)
                        run.articles+=1
                        added+=1
                    # Flush parents first: PostgreSQL enforces these foreign keys.
                    # This is a flush inside one source transaction, not a row commit.
                    db.flush()
                    db.add_all(pending_articles)
                    if hasattr(rows,'fetch_state'):
                        source.fetch_state=rows.fetch_state
                    results.append({'source':source.name,'status':'ok' if rows else 'empty','retrieved':len(rows),'added':added})
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    results.append({'source':source.name,'status':'error','error':type(exc).__name__})
                    audit(db,'source_error',source.id,error=type(exc).__name__,run_id=run.id)
                    db.commit()
            for stories,grouped in research_batches(db,changed):
                for story in stories:
                    articles=grouped[story.id]
                    if not articles:
                        continue
                    story.score,story.scoring=rank(story,articles,sources,settings)
                    previous=story.research
                    story.research=build_research(db,story,articles,settings)
                    if previous.get('editorial_review'):
                        story.research={**story.research,'editorial_review':previous['editorial_review']}
                    story.updated_at=now()
                db.commit()
            # Age every stored score, including unchanged stories that have now expired.
            # Otherwise old global alerts can remain visible with a stale eligible flag.
            for stories,grouped in ranking_batches(db):
                for story in stories:
                    articles=grouped[story.id]
                    if articles:
                        _,story.category,story.subcategory=classify(story.title,sources[articles[0].source_id])
                    story.score,story.scoring=rank(story,articles,sources,settings)
                    threshold=settings['global_threshold'] if story.region=='global' else settings['alert_threshold']
                    if story.scoring['eligible'] and story.score>=threshold and story.category in settings['categories'] and story.status not in ('rejected','dismissed','archived'):
                        queue(db,story)
            if sender:
                deliver(db,settings['notification_language'],sender)
            else:
                deliver(db,settings['notification_language'])
            good=sum(r['status'] in ('ok','not_modified') for r in results)
            run.status='success' if good and good==len(results) else ('partial' if good else 'failed')
        except Exception as exc:
            db.rollback()
            run.status='failed'
            audit(db,'run_error',run.id,error=type(exc).__name__)
        run.source_results=results
        run.finished_at=now()
        db.commit()
        print(json.dumps({'run_id':run.id,'status':run.status,'new_stories':run.new_stories,'articles':run.articles}))
        return {'id':run.id,'status':run.status,'new_stories':run.new_stories,'articles':run.articles,'sources':results}

if __name__=='__main__':
    import sys
    try:
        outcome=run_monitor()
        sys.exit(1 if outcome['status']=='failed' else 0)
    except AlreadyRunning:
        print('{"status":"skipped","reason":"another run is active"}')
