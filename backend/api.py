import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from string import Template
from typing import Literal
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy import select, func, text, and_, or_
from .config import env
from .db import Session, Story, Article, Source, Run, Notification, Setting, Prompt, Audit, audit, now
from .sources import canonical, public_url
from .locking import AlreadyRunning, monitoring_lock
from .monitor import run_monitor
from .telegram import recipients, send

@asynccontextmanager
async def lifespan(app):
    if len(env.admin_password)<16 or len(env.session_secret)<32:
        raise RuntimeError('Set ADMIN_PASSWORD (16+ chars) and SESSION_SECRET (32+ chars) in .env')
    yield

app=FastAPI(title='Hindi News Discovery Studio',lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
attempts=defaultdict(deque)

def limit(key,maximum,window=60):
    bucket=attempts[key]
    while bucket and bucket[0]<time.time()-window: bucket.popleft()
    if len(bucket)>=maximum: raise HTTPException(429,'Too many requests; try again later')
    bucket.append(time.time())

def signature(value):
    return hmac.new(env.session_secret.encode(),value.encode(),hashlib.sha256).hexdigest()

def authorized(request:Request):
    cookie=request.cookies.get('studio_session','')
    try:
        expires,nonce,sig=cookie.split('.')
        if int(expires)<time.time() or not hmac.compare_digest(signature(expires+'.'+nonce),sig): raise ValueError()
    except (ValueError,TypeError):
        raise HTTPException(401,'Sign in required')
    if request.method not in ('GET','HEAD') and request.headers.get('x-studio-action')!='1':
        raise HTTPException(403,'Missing same-origin action header')
    limit('admin',240)

def db_session():
    with Session() as db: yield db

def serialize(obj):
    return {c.name:getattr(obj,c.name) for c in obj.__table__.columns}

def get_story(db,id):
    story=db.get(Story,id)
    if not story: raise HTTPException(404,'Story not found')
    return story

def visible_story_filter(db):
    threshold=db.get(Setting,'monitoring').value['global_threshold']
    return or_(Story.region=='india',and_(Story.scoring['eligible'].as_boolean()==True,Story.score>=threshold),Story.status.in_(['selected','research_requested','interested']))

class Login(BaseModel):
    password: str = Field(max_length=300)

@app.post('/api/login')
def login(body:Login,request:Request,response:Response):
    limit('login',15,300)
    if not env.admin_password or not hmac.compare_digest(body.password.encode(),env.admin_password.encode()):
        raise HTTPException(401,'Incorrect password')
    token=str(int(time.time()+8*3600))+'.'+secrets.token_hex(16)
    response.set_cookie('studio_session',token+'.'+signature(token),httponly=True,secure=env.cookie_secure,samesite='strict',max_age=8*3600,path='/')
    return {'ok':True}

@app.post('/api/logout',dependencies=[Depends(authorized)])
def logout(response:Response):
    response.delete_cookie('studio_session',path='/')
    return {'ok':True}

@app.get('/health')
def health():
    try:
        with Session() as db: db.execute(text('SELECT 1'))
        return {'status':'ok'}
    except Exception:
        raise HTTPException(503,'Database unavailable')

@app.get('/api/overview',dependencies=[Depends(authorized)])
def overview(db=Depends(db_session)):
    run=db.scalar(select(Run).order_by(Run.started_at.desc()).limit(1))
    settings=db.get(Setting,'monitoring').value
    last=serialize(run) if run else None
    next_run=(datetime.fromisoformat(run.started_at)+timedelta(minutes=settings['interval_minutes'])).isoformat() if run else None
    counts={r:db.scalar(select(func.count()).select_from(Story).where(Story.region==r,visible_story_filter(db))) for r in ['india','global']}
    counts['entertainment']=db.scalar(select(func.count()).select_from(Story).where(Story.category=='entertainment'))
    notifications=dict(db.execute(select(Notification.status,func.count()).group_by(Notification.status)).all())
    return {'last_run':last,'next_run_estimate':next_run,'schedule_note':'Estimate only. External scheduler must be installed; dashboard does not run a timer.','counts':counts,'notifications':notifications,'telegram_configured':bool(env.telegram_bot_token and recipients()),'timezone':settings['timezone']}

@app.get('/api/stories',dependencies=[Depends(authorized)])
def stories(q:str='',region:str='',category:str='',subcategory:str='',status:str='',offset:int=0,include_below_threshold:bool=False,db=Depends(db_session)):
    query=select(Story)
    if not include_below_threshold: query=query.where(visible_story_filter(db))
    for field,value in [(Story.region,region),(Story.category,category),(Story.subcategory,subcategory),(Story.status,status)]:
        if value: query=query.where(field==value)
    if q: query=query.where(Story.title.ilike('%'+q[:200]+'%'))
    return [serialize(s) for s in db.scalars(query.order_by(Story.score.desc(),Story.updated_at.desc()).offset(max(0,offset)).limit(100))]

@app.get('/api/stories/{id}',dependencies=[Depends(authorized)])
def detail(id:str,db=Depends(db_session)):
    story=get_story(db,id)
    return {**serialize(story),'articles':[serialize(a) for a in db.scalars(select(Article).where(Article.story_id==id))]}

class Decision(BaseModel):
    status: Literal['interested','selected','rejected','archived','dismissed','research_requested']

@app.patch('/api/stories/{id}/decision',dependencies=[Depends(authorized)])
def decision(id:str,body:Decision,db=Depends(db_session)):
    story=get_story(db,id)
    story.status=body.status
    audit(db,'editorial_decision',id,status=body.status)
    db.commit()
    return serialize(story)

class ResearchEdit(BaseModel):
    confirmed_facts: str = Field(default='',max_length=15000)
    uncertainties: str = Field(default='',max_length=15000)
    summary: str = Field(default='',max_length=15000)
    sources: str = Field(default='',max_length=15000)
    angle: str = Field(default='',max_length=5000)
    additional_instructions: str = Field(default='',max_length=10000)
    image_instructions: str = Field(default='I will attach story images separately. Ask for any missing permanent references.',max_length=5000)

@app.get('/api/stories/{id}/prompt-form',dependencies=[Depends(authorized)])
def prompt_form(id:str,db=Depends(db_session)):
    story=get_story(db,id)
    r=story.research
    articles=list(db.scalars(select(Article).where(Article.story_id==id)))
    return r.get('editorial_review') or ResearchEdit(summary=r.get('summary',''),confirmed_facts='\n'.join(r.get('confirmed_facts',[])),uncertainties='\n'.join(r.get('uncertainties',[])),sources='\n'.join(a.url for a in articles),angle=r.get('angle','')).model_dump()

@app.put('/api/stories/{id}/research',dependencies=[Depends(authorized)])
def save_research(id:str,body:ResearchEdit,db=Depends(db_session)):
    story=get_story(db,id)
    story.research={**story.research,'editorial_review':body.model_dump()}
    audit(db,'research_edit',id)
    db.commit()
    return {'saved':True}

@app.post('/api/stories/{id}/prompt',dependencies=[Depends(authorized)])
def generate(id:str,body:ResearchEdit,db=Depends(db_session)):
    story=get_story(db,id)
    if story.status!='selected':
        raise HTTPException(409,'Explicitly select this story for video before generating a prompt')
    channel=db.get(Setting,'channel')
    template=db.get(Setting,'template')
    data={'headline':story.title,'region':story.region,'category':story.category,'saved_research':story.research,'editorial_review':body.model_dump(),'source_metadata':[serialize(a) for a in db.scalars(select(Article).where(Article.story_id==id))]}
    content=Template(template.value['markdown']).substitute(channel_version=channel.version,channel_rules=channel.value['markdown'],story_data=json.dumps(data,ensure_ascii=False,indent=2),image_instructions=body.image_instructions,additional_instructions=body.additional_instructions or 'None')
    prompt=Prompt(story_id=id,content=content,channel_version=channel.version)
    db.add(prompt)
    story.research={**story.research,'editorial_review':body.model_dump()}
    audit(db,'prompt_generated',id,channel_version=channel.version)
    db.commit()
    return serialize(prompt)

@app.get('/api/prompts/{id}/download',dependencies=[Depends(authorized)])
def download(id:str,db=Depends(db_session)):
    p=db.get(Prompt,id)
    if not p: raise HTTPException(404,'Prompt not found')
    return PlainTextResponse(p.content,headers={'Content-Disposition':f'attachment; filename="video-prompt-{p.id}.md"'})

@app.get('/api/settings',dependencies=[Depends(authorized)])
def settings(db=Depends(db_session)):
    return {s.key:{'value':s.value,'version':s.version} for s in db.scalars(select(Setting).where(Setting.key.in_(['monitoring','channel','template'])))}

@app.get('/api/connections',dependencies=[Depends(authorized)])
def connections():
    # Expose setup status only. Secret values never leave the server.
    return {'prompt_builder':True,'telegram':bool(env.telegram_bot_token and recipients()),'ai_research':bool(env.ai_api_key and env.ai_model)}

class MonitoringSettings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    interval_minutes: int = Field(default=60,ge=60,le=1440,multiple_of=60)
    timezone: str = 'Asia/Kolkata'
    notification_language: Literal['en','hi']='en'
    alert_threshold: float=Field(default=55,ge=0,le=100)
    global_threshold: float=Field(default=75,ge=0,le=100)
    max_age_hours: int=Field(default=72,ge=1,le=168)
    min_independent_sources: int=Field(default=2,ge=2,le=10)
    categories: list[str]
    weights: dict[str,float]
    ai_enabled: bool=False
    ai_daily_call_limit: int=Field(default=10,ge=0,le=1000)
    ai_daily_budget_usd: float=Field(default=1,ge=0,le=1000)
    ai_reserved_cost_per_call_usd: float=Field(default=0.1,gt=0,le=100)
    ai_input_usd_per_million: float=Field(default=0,ge=0)
    ai_output_usd_per_million: float=Field(default=0,ge=0)

    @field_validator('timezone')
    @classmethod
    def timezone_valid(cls,v):
        try: ZoneInfo(v)
        except Exception: raise ValueError('Unknown timezone')
        return v

    @field_validator('weights')
    @classmethod
    def weights_valid(cls,v):
        expected={'freshness','coverage','growth','independence','importance','india','evidence','explainability'}
        if set(v)!=expected or any(x<0 or x>100 for x in v.values()) or sum(v.values())<=0:
            raise ValueError('Provide all eight nonnegative ranking weights with a positive total')
        return v

def update_setting(db,key,value):
    s=db.get(Setting,key)
    audit(db,'settings_version',key,previous=s.value,version=s.version)
    s.value=value
    s.version+=1
    db.commit()
    return {'saved':True,'version':s.version}

@app.put('/api/settings/monitoring',dependencies=[Depends(authorized)])
def update_monitoring(body:MonitoringSettings,db=Depends(db_session)):
    result=update_setting(db,'monitoring',body.model_dump())
    return {**result,'schedule_note':'If interval changed, update the Azure Job or local Task Scheduler to match.'}

class Markdown(BaseModel):
    markdown:str=Field(min_length=100,max_length=30000)

@app.put('/api/settings/{key}',dependencies=[Depends(authorized)])
def update_markdown(key:str,body:Markdown,db=Depends(db_session)):
    if key not in ('channel','template'): raise HTTPException(404,'Unknown setting')
    if key=='template':
        template=Template(body.markdown)
        expected={'channel_version','channel_rules','story_data','image_instructions','additional_instructions'}
        if not template.is_valid() or set(template.get_identifiers())!=expected:
            raise HTTPException(422,'Template must retain all five required placeholders')
    return update_setting(db,key,body.model_dump())

class SourceBody(BaseModel):
    name:str=Field(min_length=2,max_length=200)
    url:str=Field(max_length=2000)
    kind:Literal['rss','json']='rss'
    region:Literal['india','global']='india'
    category:str=Field(default='national',max_length=50)
    enabled:bool=True
    primary:bool=False
    origin_group:str=Field(default='unknown',max_length=100)
    options:dict=Field(default_factory=dict)

@app.get('/api/sources',dependencies=[Depends(authorized)])
def sources(db=Depends(db_session)):
    return [serialize(s) for s in db.scalars(select(Source))]

@app.post('/api/sources',dependencies=[Depends(authorized)])
def add_source(body:SourceBody,db=Depends(db_session)):
    try: public_url(body.url)
    except Exception: raise HTTPException(422,'Use a reachable public HTTP(S) feed URL')
    url=canonical(body.url)
    if db.scalar(select(Source.id).where(Source.url==url)): raise HTTPException(409,'Source already exists')
    source=Source(**{**body.model_dump(),'url':url})
    db.add(source)
    db.commit()
    return serialize(source)

@app.put('/api/sources/{id}',dependencies=[Depends(authorized)])
def update_source(id:str,body:SourceBody,db=Depends(db_session)):
    source=db.get(Source,id)
    if not source: raise HTTPException(404,'Source not found')
    try: public_url(body.url)
    except Exception: raise HTTPException(422,'Use a public HTTP(S) feed URL')
    duplicate=db.scalar(select(Source.id).where(Source.url==canonical(body.url),Source.id!=id))
    if duplicate: raise HTTPException(409,'Source already exists')
    for key,value in body.model_dump().items(): setattr(source,key,value)
    for article in db.scalars(select(Article).where(Article.source_id==id)):
        article.origin_group=body.origin_group
    audit(db,'source_updated',id)
    db.commit()
    return serialize(source)

@app.post('/api/run',dependencies=[Depends(authorized)])
def manual_run():
    limit('manual_run',1,60)
    try: return run_monitor()
    except AlreadyRunning: raise HTTPException(409,'A monitoring run is already active')

@app.get('/api/runs',dependencies=[Depends(authorized)])
def runs(db=Depends(db_session)):
    return [serialize(r) for r in db.scalars(select(Run).order_by(Run.started_at.desc()).limit(50))]

@app.get('/api/notifications',dependencies=[Depends(authorized)])
def notifications(db=Depends(db_session)):
    return [{k:v for k,v in serialize(n).items() if k!='chat_id'} for n in db.scalars(select(Notification).order_by(Notification.updated_at.desc()).limit(100))]

@app.post('/api/notifications/{id}/retry',dependencies=[Depends(authorized)])
def retry(id:str,db=Depends(db_session)):
    try:
        with monitoring_lock():
            n=db.get(Notification,id)
            if not n: raise HTTPException(404,'Notification not found')
            if n.status=='sent': raise HTTPException(409,'Already delivered')
            n.status='pending'; n.attempts=0; n.next_attempt=now()
            audit(db,'notification_retry',id)
            db.commit()
    except AlreadyRunning: raise HTTPException(409,'Wait for active monitor to finish')
    return {'queued':True}

@app.post('/api/telegram/test',dependencies=[Depends(authorized)])
def test_telegram():
    limit('telegram_test',1,60)
    if not recipients() or not env.telegram_bot_token: raise HTTPException(409,'Configure Telegram in the server environment first')
    return [{'status':send(chat,'Hindi News Studio connection test — no video production triggered.')[0]} for chat in recipients()]

@app.get('/api/audit',dependencies=[Depends(authorized)])
def audit_log(db=Depends(db_session)):
    return [serialize(a) for a in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(100))]
