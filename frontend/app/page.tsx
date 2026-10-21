'use client';
import {useEffect,useRef,useState} from 'react';
import {api,StudioApiError,blank,textFields,formLimits,saveDraft,recoverDraft,discardDraft} from '../lib/studio';
import type {Form} from '../lib/studio';

type Article={id:string;title:string;publisher:string;url:string;published_at:string|null;event_at:string|null;retrieved_at:string;origin_group:string};
type Story={id:string;title:string;region:string;category:string;subcategory:string;status:string;score:number;updated_at:string;research:Record<string,any>;scoring:Record<string,any>;articles?:Article[]};
type PromptSummary={id:string;created_at:string;channel_version:number;has_picture:boolean};
const label=(s:string)=>s.replaceAll('_',' ');

export default function Studio(){
  const [signed,setSigned]=useState(false),[checking,setChecking]=useState(true),[password,setPassword]=useState('');
  const [view,setView]=useState('Overview'),[overview,setOverview]=useState<any>(null),[stories,setStories]=useState<Story[]>([]),[story,setStory]=useState<Story|null>(null);
  const [query,setQuery]=useState(''),[category,setCategory]=useState(''),[sub,setSub]=useState(''),[status,setStatus]=useState('');
  const [form,setForm]=useState<Form>(blank),[prompt,setPrompt]=useState<any>(null),[settings,setSettings]=useState<any>(null),[settingsText,setSettingsText]=useState('');
  const [sources,setSources]=useState<any[]>([]),[sourceEdit,setSourceEdit]=useState(''),[sourceId,setSourceId]=useState(''),[runs,setRuns]=useState<any[]>([]),[notes,setNotes]=useState<any[]>([]);
  const previewRef=useRef<HTMLElement>(null);
  const storyRequest=useRef(0),listRequest=useRef(0),pendingActions=useRef(0);
  const [draftState,setDraftState]=useState<'none'|'saved'|'memory_only'>('none');
  const [history,setHistory]=useState<PromptSummary[]>([]);
  const [recentStories,setRecentStories]=useState<Story[]>([]);
  const [copyStatus,setCopyStatus]=useState<{kind:string;message:string}|null>(null);
  const [promptTab,setPromptTab]=useState<'news_story'|'reference_picture'>('news_story');
  const [connections,setConnections]=useState<{prompt_builder:boolean;telegram:boolean;ai_research:boolean}|null>(null);
  const [busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[error,setError]=useState('');
  const date=(value:string|null|undefined)=>value?new Date(value).toLocaleString('en-IN',{timeZone:overview?.timezone||'Asia/Kolkata',dateStyle:'medium',timeStyle:'short'}):'Not established';

  async function refresh(){const [o,ss,c]=await Promise.all([api('/overview'),api('/settings'),api('/connections')]);setOverview(o);setSettings(ss);setConnections(c);setSettingsText(JSON.stringify(ss.monitoring.value,null,2));}
  async function loadStories(){const params=new URLSearchParams({q:query,category:view==='Entertainment'?'entertainment':category,region:view==='Global alerts'?'global':view==='Indian news'||view==='Entertainment'?'india':'',subcategory:sub,status});const request=++listRequest.current;const rows=await api('/stories?'+params);if(request===listRequest.current)setStories(rows);}
  function handleError(e:unknown){
    if(e instanceof StudioApiError&&e.status===401&&signed){setSigned(false);setError('Your session expired. Sign in again; any available draft will be restored.');}
    else setError(e instanceof Error?e.message:'An unexpected error occurred. Please try again.');
  }
  async function act(work:()=>Promise<void>){pendingActions.current++;setBusy(true);setError('');setNotice('');try{await work();}catch(e){handleError(e);}finally{pendingActions.current--;setBusy(pendingActions.current>0);}}
  function editForm(change:Partial<Form>){
    if(!story)return;
    const next={...form,...change};setForm(next);setPrompt(null);
    let stored=false;try{stored=saveDraft(sessionStorage,story.id,next);}catch{}
    setDraftState(stored?'saved':'memory_only');
  }
  function clearLocalDraft(id:string){try{discardDraft(sessionStorage,id);}catch{}setDraftState('none');}
  async function initializeSession(){
    await refresh();setSigned(true);
    const id=new URLSearchParams(location.search).get('story');if(id)await openStory(id);
  }
  async function openStory(id:string){
    const request=++storyRequest.current;
    const [s,f,h]=await Promise.all([api('/stories/'+id),api('/stories/'+id+'/prompt-form'),api('/stories/'+id+'/prompts')]);
    const latest=h.length?await api('/prompts/'+h[0].id):null;
    if(request!==storyRequest.current)return;
    let draft:Form|null=null;try{draft=recoverDraft(sessionStorage,id);}catch{}
    setRecentStories(previous=>[s,...previous.filter(item=>item.id!==s.id)].slice(0,10));
    setStory(s);setForm(draft||{...blank,...f});setDraftState(draft?'saved':'none');setHistory(h);setPrompt(draft?null:latest);
    const url=new URL(location.href);url.searchParams.set('story',id);window.history.replaceState(null,'',url);
  }
  useEffect(()=>{setCopyStatus(null);setPromptTab('news_story');if(prompt)previewRef.current?.scrollIntoView({behavior:'smooth',block:'start'});},[prompt]);
  async function generatePrompt(){
    if(!story)return;
    const currentForm={...form};
    if(story.status!=='selected'){
      await api('/stories/'+story.id+'/decision','PATCH',{status:'selected'});
      setStory({...story,status:'selected'});
    }
    const generated=await api('/stories/'+story.id+'/prompt','POST',currentForm);
    setPrompt(generated);
    clearLocalDraft(story.id);
    setHistory(await api('/stories/'+story.id+'/prompts'));
    setNotice('Your news-story and reference-picture prompts are ready. Copy either one or both into Claude.');
  }
  async function copyPrompt(kind:'news_story'|'reference_picture'|'complete'){
    if(!prompt)return;
    const title=kind==='complete'?'Both prompts':kind==='news_story'?'News-story prompt':'Reference-picture prompt';
    if(kind!=='news_story'&&!prompt.reference_picture_content)throw new Error('This older record has no picture prompt. Generate a new pair.');
    const content=kind==='complete'?prompt.content+'\n\n---\n\n'+prompt.reference_picture_content:kind==='news_story'?prompt.content:prompt.reference_picture_content;
    try{
      await navigator.clipboard.writeText(content);
      setCopyStatus({kind,message:title+' copied. Paste into your Claude video agent.'});
    }catch{
      setCopyStatus({kind,message:'Clipboard access failed. Use the matching Markdown download.'});
      throw new Error('Clipboard access failed. Use the Markdown download.');
    }
  }
  useEffect(()=>{initializeSession().catch(e=>{if(!(e instanceof StudioApiError&&e.status===401))handleError(e);}).finally(()=>setChecking(false));},[]);
  useEffect(()=>{if(!signed)return;let canceled=false;const timer=setTimeout(()=>{loadStories().catch(e=>{if(!canceled)handleError(e)});},200);return()=>{canceled=true;++listRequest.current;clearTimeout(timer)};},[signed,view,query,category,sub,status]);
  useEffect(()=>{if(!signed)return;act(async()=>{if(view==='Settings')setSources(await api('/sources'));if(view==='Activity'){const [r,n]=await Promise.all([api('/runs'),api('/notifications')]);setRuns(r);setNotes(n);}});},[view,signed]);

  if(checking)return <main className="login"><div className="brand">दृष्टि <span>DRISHTI</span></div><p>Opening your editorial desk…</p></main>;
  if(!signed)return <main className="login"><div className="login-card"><div className="brand">दृष्टि <span>DRISHTI</span></div><p className="eyebrow">HINDI NEWS DISCOVERY STUDIO</p><h1>A clearer view.<br/>A stronger story.</h1><p>Research Indian news, follow cinema, and prepare your next Hindi documentary.</p><form onSubmit={e=>{e.preventDefault();act(async()=>{await api('/login','POST',{password});setPassword('');await initializeSession();});}}><label>Administrator password<input type="password" required autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)}/></label><button className="primary" disabled={busy}>Open the studio →</button></form>{error&&<p role="alert" className="error">{error}</p>}<small>Private editorial workspace · Human approval at every stage</small></div></main>;

  const promptStories=Array.from(new Map([...(story?[story]:[]),...recentStories,...stories].map(item=>[item.id,item])).values());
  const navigate=(v:string)=>{setView(v);setCategory('');setSub('');setStatus('');setQuery('');};
  const select=async(value:string)=>{if(!story)return;await api('/stories/'+story.id+'/decision','PATCH',{status:value});setStory({...story,status:value});await loadStories();setNotice('Editorial decision saved. Your current form edits are retained.');};
  return <div className="shell">
    <aside className="sidebar"><div className="brand">दृष्टि <span>DRISHTI</span></div><p className="sidebar-caption">THE EDITORIAL DESK</p><nav>{['Overview','Indian news','Entertainment','Global alerts','Prompt builder','Activity','Settings'].map((v,i)=><button key={v} disabled={busy} className={view===v?'nav active':'nav'} onClick={()=>navigate(v)}><span>{['◫','◉','✦','◎','▤','↻','⚙'][i]}</span>{v}</button>)}</nav><div className="sidebar-bottom"><span className="live-dot"/> Phase 1 · Discovery<br/><small>Research. Review. Create with intent.</small><button className="text-button" onClick={()=>act(async()=>{await api('/logout','POST');setSigned(false);})}>Sign out ↗</button></div></aside>
    <main className="workspace"><header><div className="breadcrumb">WORKSPACE <span>/</span> {view.toUpperCase()}</div><div className="header-meta">Hindi channel <span className="avatar">हि</span></div></header>
      <section className="page-heading"><div><p className="eyebrow">EVIDENCE BEFORE THE EDIT</p><h1>{view==='Overview'?'Your next story starts here.':view}</h1><p>{view==='Overview'?'A considered view of India, cinema, and the developments that matter.':view==='Global alerts'?'Information alerts only. You decide what deserves further research.':view==='Prompt builder'?'Prepare the news-story and reference-picture prompts. Your Claude agent makes the video.':'Your research, source evidence, and editorial decisions in one place.'}</p></div><button className="primary" disabled={busy} onClick={()=>act(async()=>{const r=await api('/run','POST');await refresh();await loadStories();setNotice('Monitoring finished: '+r.status+'. '+r.new_stories+' new stories.');})}>{busy?'Working…':'↻ Run discovery'}</button></section>
      <div aria-live="polite">{notice&&<div className="notice">{notice}</div>}{error&&<div role="alert" className="error">{error}</div>}</div>
      {view==='Overview'&&<><div className="stats">{[['Indian candidates',overview?.counts.india||0,'Stories for your review'],['Entertainment',overview?.counts.entertainment||0,'Cinema & the industry'],['Global alerts',overview?.counts.global||0,'Awaiting your direction'],['Last run',overview?.last_run?.status||'Not run',date(overview?.last_run?.finished_at)]].map(([title,value,caption])=><div className="stat" key={title}><small>{title}</small><strong>{value}</strong><span>{caption}</span></div>)}</div><div className="overview-grid"><div className="editorial-banner"><p className="eyebrow">THE HUMAN STAYS IN THE LOOP</p><h2>From a developing story<br/>to an informed perspective.</h2><p>Explore the evidence, select a story, and build a complete production brief. Every decision remains yours.</p><button onClick={()=>navigate('Indian news')}>Explore Indian news ↗</button><div className="orb" aria-hidden="true">दृष्टि</div></div><div className="panel schedule"><div className="panel-title"><h3>Discovery pulse</h3><span className="tag">{settings?.monitoring.value.interval_minutes||60} min</span></div><p>Next run estimate</p><strong>{date(overview?.next_run_estimate)}</strong><small>{overview?.schedule_note}</small><hr/><p>Telegram</p><strong>{overview?.telegram_configured?'Configured':'Setup required'}</strong><small>{Object.entries(overview?.notifications||{}).map(([k,v])=>`${v} ${k}`).join(' · ')||'No notifications queued'}</small></div></div><div className="section-title"><h2>On the editorial radar</h2><span>Ranked by transparent signals</span></div></>}
      {['Overview','Indian news','Entertainment','Global alerts'].includes(view)&&<><div className="filters"><input aria-label="Search headlines" placeholder="Search stories, films, developments…" value={query} onChange={e=>setQuery(e.target.value)}/>{view!=='Entertainment'&&<select aria-label="Category" value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{(settings?.monitoring.value.categories||[]).map((c:string)=><option key={c}>{c}</option>)}</select>}{view==='Entertainment'&&<select aria-label="Entertainment topic" value={sub} onChange={e=>setSub(e.target.value)}><option value="">All entertainment</option>{['upcoming_releases','box_office','record_breaking','celebrity_industry','regional_cinema'].map(s=><option value={s} key={s}>{label(s)}</option>)}</select>}<select aria-label="Editorial status" value={status} onChange={e=>setStatus(e.target.value)}><option value="">All statuses</option>{['new','awaiting_direction','interested','selected','research_requested','rejected','dismissed','archived'].map(s=><option value={s} key={s}>{label(s)}</option>)}</select></div><div className="story-grid">{stories.map(s=><button className="story-card" disabled={busy} key={s.id} onClick={()=>act(()=>openStory(s.id))}><div className="card-top"><span className={'category '+(s.category==='entertainment'?'purple':'')}>{s.region==='global'?'GLOBAL ALERT':s.category.toUpperCase()}</span><span className="score">{s.score}<small> / 100</small></span></div><h3>{s.title}</h3><p>{s.research.summary}</p><div className="card-evidence">{s.scoring.publisher_count||1} publishers · {s.scoring.independent_origins||0} reviewed origins</div><div className="card-bottom"><span className="tag">{label(s.status)}</span><span>Review evidence ↗</span></div></button>)}</div>{stories.length===0&&<div className="empty"><span>◎</span><h2>No stories in this view yet.</h2><p>Run discovery or adjust your filters. Real source results will appear here.</p></div>}{stories.length===100&&<p>Showing the top 100 results. Narrow your search to find older stories.</p>}</>}
      {view==='Prompt builder'&&<div className="builder">
        <section className="panel">
          <h2>01 / Choose your story</h2>
          <p>Get two text prompts: the news story and its reference picture. Give them to your Claude video agent. No API token is needed to prepare these prompts.</p>
          <select aria-label="Choose story for prompt" value={story?.id||''} disabled={busy} onChange={e=>{if(e.target.value)act(()=>openStory(e.target.value));else{++storyRequest.current;setStory(null);setPrompt(null);setHistory([]);setDraftState('none');}}}>
            <option value="">Select a story…</option>{promptStories.map(s=><option value={s.id} key={s.id}>{s.title}</option>)}
          </select>
          {story&&<>
            <h3>{story.title}</h3>
            <p className="muted">{label(story.status)} · You choose the story. Claude handles the video.</p>
            {story.status!=='selected'&&<p className="notice">Review the fields below. The final button selects this story and prepares both prompts.</p>}
            <h2>02 / Edit the story and picture direction</h2>
            {draftState!=='none'&&<div className="draft-notice" role="status"><strong>{draftState==='saved'?'Unsaved draft protected in this browser tab':'Unsaved changes — browser draft storage unavailable'}</strong><p>{draftState==='saved'?'Your edits can be recovered after a refresh or when you return to this story in this tab. Use Save edits or generate prompts to save them to the studio.':'Keep this tab open and use Save edits to keep these changes in the studio.'}</p><button disabled={busy} onClick={()=>act(async()=>{const saved=await api('/stories/'+story.id+'/prompt-form');clearLocalDraft(story.id);setForm({...blank,...saved});setPrompt(null);setNotice('Restored the last saved story fields.');})}>Discard draft and restore saved fields</button></div>}
            <fieldset className="production-options" disabled={busy}>
              <legend>Video direction for Claude</legend>
              <p>These choices guide the prompts. Rendering tools and approved reference images are checked separately in Claude.</p>
              <div className="option-grid">
                <label>Target length<select value={form.target_duration_seconds} onChange={e=>{editForm({target_duration_seconds:Number(e.target.value)});}}>{Array.from(new Set([60,90,120,180,240,300,form.target_duration_seconds])).sort((a,b)=>a-b).map(n=><option key={n} value={n}>{n/60} minutes</option>)}</select></label>
                <label>Story structure<select value={form.story_format} onChange={e=>{editForm({story_format:e.target.value as Form['story_format']});}}><option value="auto">Choose for this story</option><option value="explainer">Background and explanation</option><option value="timeline">Chronological timeline</option><option value="news_update">Latest news update</option></select></label>
                <label>2D animation style<select value={form.animation_style} onChange={e=>{editForm({animation_style:e.target.value as Form['animation_style']});}}><option value="hybrid">Layered 2D + motion graphics</option><option value="motion_graphics">Maps, charts and motion graphics</option><option value="anchor_led">Anchor-led with story cutaways</option></select></label>
                <label>Anchor screen time<select value={form.anchor_presence} onChange={e=>{editForm({anchor_presence:e.target.value as Form['anchor_presence']});}}><option value="balanced">Balanced — intro, explanation, close</option><option value="minimal">Minimal — brief intro and close</option><option value="frequent">Frequent — between story sections</option></select></label>
              </div>
            </fieldset>
            {textFields.map(key=><label key={key}>{key==='image_instructions'?'Reference-picture direction':label(key)}<textarea disabled={busy} maxLength={formLimits[key]} rows={key==='summary'||key==='sources'?5:3} value={form[key]} onChange={e=>{editForm({[key]:e.target.value});}}/></label>)}
            <button disabled={busy} onClick={()=>act(async()=>{await api('/stories/'+story.id+'/research','PUT',form);clearLocalDraft(story.id);setNotice('Your story and picture direction are saved.');})}>Save edits</button>
            <details><summary>Permanent channel rules · version {settings?.channel.version}</summary><pre>{settings?.channel.value.markdown}</pre></details>
            <div aria-live="polite">{error&&<p className="error">{error}</p>}</div>
            <button className="primary wide" disabled={busy} onClick={()=>act(generatePrompt)}>{busy?'Preparing both prompts…':story.status==='selected'?'Generate both prompts →':'Select story & generate both prompts →'}</button>
          </>}
        </section>
        <section className="panel prompt-preview" ref={previewRef}>
          <p className="eyebrow">COPY INTO YOUR CLAUDE VIDEO AGENT</p>
          <h2>03 / Your two prompts</h2>
          <p>The picture prompt is text describing the reference illustration. Attach any actual anchor, newsroom or story images separately in Claude.</p>
          {history.length>0&&<label>Saved prompts — latest 20<select aria-label="Saved prompt versions" disabled={busy} value={prompt?.id||''} onChange={e=>{if(e.target.value)act(async()=>{setPrompt(await api('/prompts/'+e.target.value));setNotice('Saved snapshot opened. Your current form edits are unchanged.');});}}><option value="">Choose a saved snapshot…</option>{history.map(p=><option key={p.id} value={p.id}>{date(p.created_at)} · Channel v{p.channel_version}{p.has_picture?' · two prompts':' · story only'}</option>)}</select></label>}
          {prompt?<>
            <div className="notice" role="status">{prompt.reference_picture_content?'2 prompts ready · Saved together':'Older snapshot · News-story prompt only'}</div>
            <p className="muted">Saved {date(prompt.created_at)} · Channel rules v{prompt.channel_version}. This is a saved snapshot; generate again to apply current edits and rules.</p>
            {prompt.readiness?.warnings?.length>0&&<div className="research-gaps"><strong>Research gaps to resolve in Claude</strong><ul>{prompt.readiness.warnings.map((w:string)=><li key={w}>{w}</li>)}</ul></div>}
            <div className="actions"><button className="primary" disabled={!prompt.reference_picture_content} onClick={()=>act(()=>copyPrompt('complete'))}>Copy both prompts</button>{prompt.reference_picture_content&&<a className="button" href={'/api/prompts/'+prompt.id+'/download?kind=complete'}>Download both</a>}</div>
            {copyStatus?.kind==='complete'&&<p className="notice" role="status">{copyStatus.message}</p>}
            <div className="prompt-tabs" role="tablist" aria-label="Generated prompts">
              <button id="news-prompt-tab" role="tab" aria-selected={promptTab==='news_story'} aria-controls="news-prompt-panel" onClick={()=>setPromptTab('news_story')}>1. News-story prompt</button>
              <button id="picture-prompt-tab" disabled={!prompt.reference_picture_content} role="tab" aria-selected={promptTab==='reference_picture'} aria-controls="picture-prompt-panel" onClick={()=>setPromptTab('reference_picture')}>2. Reference-picture prompt</button>
            </div>
            <div id={promptTab==='news_story'?'news-prompt-panel':'picture-prompt-panel'} role="tabpanel" aria-labelledby={promptTab==='news_story'?'news-prompt-tab':'picture-prompt-tab'}>
              <h3>{promptTab==='news_story'?'News-story prompt':'Reference-picture prompt'}</h3>
              <small className="muted">{(promptTab==='news_story'?prompt.content:prompt.reference_picture_content).length.toLocaleString()} characters</small>
              <div className="actions"><button onClick={()=>act(()=>copyPrompt(promptTab))}>{promptTab==='news_story'?'Copy news-story prompt':'Copy reference-picture prompt'}</button><a className="button" href={'/api/prompts/'+prompt.id+'/download?kind='+promptTab}>Download Markdown</a></div>
              {copyStatus?.kind===promptTab&&<p className="notice" role="status">{copyStatus.message}</p>}
              <pre>{promptTab==='news_story'?prompt.content:prompt.reference_picture_content}</pre>
            </div>
          </>:<div className="empty"><span>▤</span><p>Select a story and generate both prompts. Your copyable news brief and reference-picture prompt will appear here.</p></div>}
        </section>
      </div>}
      {view==='Settings'&&settings&&<div className="settings-grid"><section className="panel"><h2>Channel Bible</h2><p>Permanent rules, version {settings.channel.version}. Previous versions remain in the audit log.</p><textarea rows={18} value={settings.channel.value.markdown} onChange={e=>setSettings({...settings,channel:{...settings.channel,value:{markdown:e.target.value}}})}/><button onClick={()=>act(async()=>{await api('/settings/channel','PUT',settings.channel.value);await refresh();setNotice('Channel Bible saved.');})}>Save channel rules</button><h2>Monitoring parameters</h2><p>The default is hourly. A changed interval also requires updating the external scheduler.</p><textarea className="code" rows={22} aria-label="Monitoring settings JSON" value={settingsText} onChange={e=>setSettingsText(e.target.value)}/><button onClick={()=>act(async()=>{const r=await api('/settings/monitoring','PUT',JSON.parse(settingsText));await refresh();setNotice(r.schedule_note);})}>Save parameters</button><h2>Tokens & service connections</h2><div className="source-row"><div><strong>Claude prompt builder: ready</strong><small>No token required. Copy the generated text into your own Claude project.</small></div></div><div className="source-row"><div><strong>Telegram: {connections?.telegram?'configured':'not configured'}</strong><small>Used only for sending news notifications.</small></div></div><div className="source-row"><div><strong>AI research: {connections?.ai_research?(settings.monitoring.value.ai_enabled?'configured and enabled':'key configured; currently disabled'):'not configured'}</strong><small>Optional AI-written summaries. Source excerpts and prompt generation work without it.</small></div></div><p>Put tokens in the private <code>.env</code> file in your project folder, then restart the studio. Never paste them into a story or a Claude prompt.</p><pre>{'TELEGRAM_BOT_TOKEN=your bot token\nTELEGRAM_CHAT_IDS=your authorized chat ID\n\n# Optional AI research\nAI_API_KEY=your provider key\nAI_MODEL=your model name'}</pre><p>Your Telegram bot token comes from BotFather. An AI key comes from the provider you choose. For AI research, also enable ai_enabled in the monitoring parameters above. Test messages go only to your authorized chat IDs.</p><button onClick={()=>act(async()=>{const results=await api('/telegram/test','POST');setNotice('Test result: '+results.map((r:any)=>r.status).join(', '));})}>Send test notification</button></section><section className="panel"><h2>Sources & provenance</h2><p>Connected feeds help you discover topics for your own researched stories. Headlines-only connections collect titles, dates, publishers and links. They do not import articles, clips or images or grant a commercial content licence. Leave origin_group as “unknown” unless you have reviewed independent reporting provenance; syndicated copies share one origin.</p>{sources.map(s=><div className="source-row" key={s.id}><div><strong>{s.name}</strong><small>{s.enabled?'Enabled':'Disabled'} · {s.region} · {s.category}{s.options?.headlines_only?' · Headlines & links only':''}</small><a href={s.url} target="_blank" rel="noreferrer">Open source ↗</a>{s.options?.terms_url&&<> · <a href={s.options.terms_url} target="_blank" rel="noreferrer">Publisher feed terms ↗</a></>}</div><button onClick={()=>{setSourceEdit(JSON.stringify(s,null,2));setSourceId(s.id);}}>Edit</button></div>)}<button onClick={()=>{setSourceId('');setSourceEdit(JSON.stringify({name:'',url:'',kind:'rss',region:'india',category:'entertainment',enabled:true,primary:false,origin_group:'unknown',options:{}},null,2));}}>+ Add permitted source</button>{sourceEdit&&<><textarea className="code" rows={16} aria-label="Source settings JSON" value={sourceEdit} onChange={e=>setSourceEdit(e.target.value)}/><button onClick={()=>act(async()=>{await api('/sources'+(sourceId?'/'+sourceId:''),sourceId?'PUT':'POST',JSON.parse(sourceEdit));setSources(await api('/sources'));setSourceEdit('');setNotice('Source saved.');})}>Save source</button></>}<details><summary>News-story prompt template</summary><textarea rows={25} aria-label="Prompt template" value={settings.template.value.markdown} onChange={e=>setSettings({...settings,template:{...settings.template,value:{markdown:e.target.value}}})}/><button onClick={()=>act(async()=>{await api('/settings/template','PUT',settings.template.value);await refresh();setNotice('Prompt template saved.');})}>Save template</button></details>{settings.picture_template&&<details><summary>Reference-picture prompt template</summary><textarea rows={20} aria-label="Reference-picture template" value={settings.picture_template.value.markdown} onChange={e=>setSettings({...settings,picture_template:{...settings.picture_template,value:{markdown:e.target.value}}})}/><button onClick={()=>act(async()=>{await api('/settings/picture_template','PUT',settings.picture_template.value);await refresh();setNotice('Reference-picture template saved.');})}>Save picture template</button></details>}</section></div>}
      {view==='Activity'&&<div className="settings-grid"><section className="panel"><h2>Monitoring history</h2>{runs.length===0&&<p>No runs recorded.</p>}{runs.map(r=><details key={r.id}><summary><span className="tag">{r.status}</span> {date(r.started_at)} · {r.new_stories} new</summary><p>Finished: {date(r.finished_at)}</p>{r.source_results.map((s:any,i:number)=><p key={i}>{s.source}: <strong>{s.status}</strong> {s.error||`${s.retrieved} retrieved · ${s.added} added`}</p>)}</details>)}</section><section className="panel"><h2>Telegram delivery</h2><p>Uncertain means the server lost the response. Check Telegram before retrying to avoid a duplicate.</p>{notes.length===0&&<p>No queued messages. Alerts require sufficient evidence and configured recipients.</p>}{notes.map(n=><div className="source-row" key={n.id}><div><strong>{n.status} · {n.attempts} attempts</strong><small>{n.error||date(n.updated_at)}</small><button className="text-button" onClick={()=>act(()=>openStory(n.story_id))}>View story</button></div>{['failed','uncertain'].includes(n.status)&&<button onClick={()=>act(async()=>{await api('/notifications/'+n.id+'/retry','POST');setNotes(await api('/notifications'));setNotice('Retry queued for the next run.');})}>Queue retry</button>}</div>)}</section></div>}
      <footer>DRISHTI / DISCOVERY STUDIO <span>Source-led research. Human-led decisions.</span></footer>
    </main>
    {story&&view!=='Prompt builder'&&<div className="modal-backdrop" onClick={()=>setStory(null)}><section className="detail" role="dialog" aria-modal="true" aria-label="Story research" onClick={e=>e.stopPropagation()}><button className="close" aria-label="Close story" onClick={()=>setStory(null)}>×</button><p className="eyebrow">{story.category.toUpperCase()} / {story.region.toUpperCase()}</p><h2>{story.title}</h2><p>{story.research.summary}</p><div className="actions">{['interested','selected','research_requested','rejected','dismissed','archived'].map(s=><button key={s} disabled={busy} onClick={()=>act(()=>select(s))}>{s==='selected'?'Select for video':label(s)}</button>)}</div><p className="tag">{label(story.status)}</p><h3>Evidence & uncertainty</h3><p>{story.research.evidence_status}</p>{['confirmed_facts','attributed_claims','conflicting_reports','unverified_information','uncertainties'].map(k=><details key={k} open={k==='attributed_claims'||k==='uncertainties'}><summary>{label(k)}</summary>{story.research[k]?.length?story.research[k].map((v:any,i:number)=><p key={i}>{typeof v==='string'?v:<>{v.text} <a href={v.url} target="_blank" rel="noreferrer">{v.source} ↗</a></>}</p>):<p>No entries established.</p>}</details>)}{story.research.ai_draft&&<details><summary>AI draft — review required</summary><pre>{JSON.stringify(story.research.ai_draft,null,2)}</pre></details>}{story.category==='entertainment'&&<><h3>Box-office figures & record claims</h3><p>Each figure is a separate attributed estimate. Missing fields are not inferred.</p><pre>{JSON.stringify({figures:story.research.box_office,records:story.research.record_claims},null,2)}</pre></>}<h3>Why this score?</h3><p>{story.scoring.explanation}</p><div className="score-bars">{Object.entries(story.scoring.contributions||{}).map(([k,v])=><div key={k}><span>{label(k)}</span><meter min={0} max={Math.max(1,settings?.monitoring.value.weights[k]||20)} value={Number(v)}/><strong>{String(v)}</strong></div>)}</div><p>{story.scoring.eligible?'Meets evidence eligibility':'Not eligible for automatic alert — evidence or significance checks unmet'}</p><h3>Source trail</h3>{story.articles?.map(a=><div className="source-row" key={a.id}><div><a href={a.url} target="_blank" rel="noreferrer">{a.publisher}: {a.title} ↗</a><small>Published {date(a.published_at)} · Event {date(a.event_at)}</small><small>Retrieved {date(a.retrieved_at)} · Origin: {a.origin_group}</small></div></div>)}<h3>Suggested Hindi angle</h3><p>{story.research.angle}</p><button className="primary wide" onClick={()=>setView('Prompt builder')}>Open in Prompt Builder →</button></section></div>}
  </div>;
}
