from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import select
from .config import env
from .db import Notification, Story, Article, now

def recipients():
    return [c.strip() for c in env.telegram_chat_ids.split(',') if c.strip()]

def message(story,articles,language='en'):
    r=story.research
    label='GLOBAL INFORMATION ALERT' if story.region=='global' else ('ENTERTAINMENT NEWS' if story.category=='entertainment' else 'INDIAN NEWS')
    intro='सूचना अलर्ट — स्रोतों की समीक्षा आवश्यक।\n' if language=='hi' else ''
    if language=='hi':
        draft=r.get('ai_draft',{})
        intro+=('AI अनुवाद (समीक्षा आवश्यक): '+draft['summary']+'\n' if draft.get('summary') else 'हिंदी अनुवाद उपलब्ध नहीं; नीचे मूल स्रोत का सार है।\n')
    lines=[label,intro+story.title,r.get('summary',''), 'Why it matters: '+r.get('why_it_matters',''), 'Evidence: '+r.get('evidence_status','Attributed reports'),f'Selection: score {story.score}; independent origins {story.scoring.get("independent_origins",0)}; primary source {story.scoring.get("primary_source",False)}', 'Event: '+str(next((a.event_at for a in articles if a.event_at), 'unknown')), 'Published: '+str(next((a.published_at for a in articles if a.published_at),'unknown'))]
    if story.category=='entertainment':
        lines+=['Film/person: '+r.get('entity','Not yet extracted'), 'Release: '+str(r.get('release_date') or 'unconfirmed')]
        for f in r.get('box_office',[])[:2]:
            lines.append(f"Figure (attributed): {f.get('amount')} {f.get('unit')} {f.get('currency') or 'currency unknown'}; {f.get('territory') or 'territory unknown'} {f.get('measure') or 'measure unknown'}; period {f.get('period') or 'unknown'}; {f.get('estimate_type')}")
    if story.region=='global':
        lines+=['Awaiting your direction. No video prompt generated.','India implications require editorial assessment.']
    else:
        lines+=['Hindi documentary angle: '+r.get('angle','')]
    lines+=['Uncertainty: '+'; '.join(r.get('uncertainties',[])[:2])]
    # Bound each section to keep source links and dashboard link inside Telegram's limit.
    body='\n\n'.join(str(x)[:500] for x in lines)[:2600]
    links='\n'.join(a.publisher+': '+a.url[:350] for a in articles[:2])
    return body+'\n\n'+links+'\n\nDashboard: '+env.dashboard_url.rstrip('/')+'/?story='+story.id

def send(chat_id,text):
    if chat_id not in recipients():
        return 'failed','Unauthorized recipient',0
    if not env.telegram_bot_token:
        return 'pending','Telegram token not configured',3600
    try:
        with httpx.Client(timeout=15,trust_env=False) as client:
            response=client.post('https://api.telegram.org/bot'+env.telegram_bot_token+'/sendMessage',json={'chat_id':chat_id,'text':text[:4096],'link_preview_options':{'is_disabled':True}})
        data=response.json()
        if response.status_code==429:
            return 'pending','Telegram rate limited',max(1,int(data.get('parameters',{}).get('retry_after',60)))
        if response.status_code>=500:
            return 'pending','Telegram temporary server failure',60
        if response.status_code==200 and data.get('ok'):
            return 'sent','',0
        return 'failed','Telegram rejected request; check token/chat permissions',0
    except (httpx.TimeoutException,httpx.NetworkError):
        # Delivery may have happened before response loss. Do not silently resend.
        return 'uncertain','Network response lost; check Telegram before manually retrying',0
    except (ValueError,KeyError):
        return 'failed','Invalid Telegram response',0

def queue(db,story):
    for chat_id in recipients():
        if not db.scalar(select(Notification).where(Notification.story_id==story.id,Notification.chat_id==chat_id)):
            db.add(Notification(story_id=story.id,chat_id=chat_id))
    db.commit()

def deliver(db,language='en',sender=send):
    for note in db.scalars(select(Notification).where(Notification.status=='pending',Notification.next_attempt<=now()).limit(30)):
        if note.attempts>=5:
            note.status='failed'
            continue
        story=db.get(Story,note.story_id)
        if story.status in ('rejected','archived','dismissed'):
            note.status='suppressed'
            continue
        if note.chat_id not in recipients():
            note.status='suppressed'
            continue
        if not env.telegram_bot_token:
            continue
        note.status='sending'
        note.attempts+=1
        db.commit()
        articles=list(db.scalars(select(Article).where(Article.story_id==story.id)))
        state,error,delay=sender(note.chat_id,message(story,articles,language))
        note.status=state
        note.error=error
        note.updated_at=now()
        note.next_attempt=(datetime.now(timezone.utc)+timedelta(seconds=max(delay,60*2**note.attempts))).isoformat()
        db.commit()
    db.commit()
