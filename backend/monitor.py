import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from .db import Session, Run, Story, Article, Source, Setting, Notification, audit, now
from .locking import monitoring_lock, AlreadyRunning
from .sources import ADAPTERS
from .editorial import classify, fingerprint, similar, rank
from .research import build_research
from .telegram import queue, deliver

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
        changed={story.id for story in db.scalars(select(Story)) if not story.research.get('provider')}
        cutoff=(datetime.now(timezone.utc)-timedelta(hours=settings['max_age_hours'])).isoformat()
        try:
            for source in sources.values():
                if not source.enabled or source.category not in settings['categories']:
                    continue
                try:
                    rows=adapters[source.kind].collect(source)
                    added=0
                    for row in rows:
                        if row['published_at'] and (row['published_at']<cutoff or row['published_at']>now()):
                            continue
                        if db.scalar(select(Article.id).where(Article.url==row['url'])):
                            continue
                        region,category,sub=classify(row['title'],source)
                        fp=fingerprint(row['title'],region)
                        story=db.scalar(select(Story).where(Story.fingerprint==fp))
                        if not story:
                            candidates=db.scalars(select(Story).where(Story.region==region,Story.category==category,Story.updated_at>=cutoff))
                            story=next((s for s in candidates if similar(s.title,row['title'])),None)
                        if not story:
                            story=Story(title=row['title'],fingerprint=fp,region=region,category=category,subcategory=sub,status='awaiting_direction' if region=='global' else 'new')
                            db.add(story)
                            db.flush()
                            run.new_stories+=1
                        db.add(Article(**row,source_id=source.id,story_id=story.id,publisher=source.name,origin_group=source.origin_group))
                        db.flush()
                        changed.add(story.id)
                        run.articles+=1
                        added+=1
                        db.commit()
                    results.append({'source':source.name,'status':'ok' if rows else 'empty','retrieved':len(rows),'added':added})
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    results.append({'source':source.name,'status':'error','error':type(exc).__name__})
                    audit(db,'source_error',source.id,error=type(exc).__name__,run_id=run.id)
                    db.commit()
            for story_id in changed:
                story=db.get(Story,story_id)
                if not story:
                    continue
                articles=list(db.scalars(select(Article).where(Article.story_id==story_id).order_by(Article.retrieved_at.desc())))
                if not articles:
                    continue
                story.score,story.scoring=rank(story,articles,sources,settings)
                previous=story.research
                story.research=build_research(db,story,articles,settings)
                if previous.get('editorial_review'):
                    story.research={**story.research,'editorial_review':previous['editorial_review']}
                story.updated_at=now()
                db.commit()
            # Re-evaluate all recent stories so configuration changes can enable an alert without re-ingestion.
            for story in db.scalars(select(Story).where(Story.updated_at>=cutoff)):
                articles=list(db.scalars(select(Article).where(Article.story_id==story.id)))
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
            good=sum(r['status']=='ok' for r in results)
            run.status='success' if good and all(r['status']=='ok' for r in results) else ('partial' if good else 'failed')
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
