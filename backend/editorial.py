import hashlib
import re
from datetime import datetime, timezone

STOP=set('the a an and of to in on for with as is at by from after new says said'.split())

def tokens(title):
    return set(re.findall(r'[\w\u0900-\u097f]+',title.lower()))-STOP

def fingerprint(title, region):
    return hashlib.sha256((region+'|'+' '.join(sorted(tokens(title)))).encode()).hexdigest()

def similar(a,b):
    x,y=tokens(a),tokens(b)
    # Different collection figures/dates should not merge merely because the film matches.
    nums=lambda s:set(re.findall(r'\d+(?:\.\d+)?',s))
    if nums(a) and nums(b) and nums(a)!=nums(b):
        return False
    return len(x&y)>=3 and len(x&y)/max(1,len(x|y))>=0.65

def classify(title,source):
    t=title.lower()
    region=source.region
    category=source.category
    if region=='global' and re.search(r'\b(india|indian|delhi|mumbai|modi)\b|भारत|भारतीय',t):
        region='india'
    if region=='india' and category in ('national','world'):
        if re.search(r'bollywood|cinema|box.office|film|movie|actor|actress|बॉलीवुड|फिल्म',t): category='entertainment'
        elif re.search(r'\bipo\b|economy|stock|business|bank|inflation',t): category='business'
        elif re.search(r'science|space|isro|research|वैज्ञानिक',t): category='science'
        elif re.search(r'court|judgment|अदालत',t): category='courts'
    sub=''
    if category=='entertainment':
        if re.search(r'rumou?r|dating|relationship|affair|secret wedding|break.?up|अफवाह',t):
            sub='excluded_gossip'
        elif re.search(r'record|fastest|highest|रिकॉर्ड',t): sub='record_breaking'
        elif re.search(r'box.office|collection|gross|crore|करोड़|कमाई',t): sub='box_office'
        elif re.search(r'tamil|telugu|malayalam|kannada|regional',t): sub='regional_cinema'
        elif re.search(r'release|trailer|teaser|ott|casting|poster|रिलीज',t): sub='upcoming_releases'
        else: sub='celebrity_industry'
    return region,category,sub

def rank(story,articles,sources,settings):
    current=datetime.now(timezone.utc)
    dates=[datetime.fromisoformat(a.published_at) for a in articles if a.published_at]
    age=max(0,(current-max(dates)).total_seconds()/3600) if dates else settings['max_age_hours']
    origins={a.origin_group for a in articles if a.origin_group!='unknown'}
    primary=any(sources[a.source_id].primary for a in articles)
    reliable=primary or len(origins)>=settings['min_independent_sources']
    title=story.title.lower()
    important=bool(re.search(r'\b(?:earthquake|war|conflict|disaster|supreme court|policy|election|breakthrough|climate|record|box.office|release|missile|pandemic)\b|भूकंप|युद्ध|सरकार|अदालत',title))
    recent=sum(1 for a in articles if (current-datetime.fromisoformat(a.retrieved_at)).total_seconds()<3600)
    prior=max(1,len(articles)-recent)
    values={'freshness':max(0,1-age/settings['max_age_hours']),'coverage':min(1,len(articles)/5),'growth':min(1,recent/prior/3),'independence':min(1,len(origins)/3),'importance':1 if important else 0.25,'india':1 if story.region=='india' else 0,'evidence':1 if reliable else 0.2,'explainability':0.7}
    contributions={k:round(v*settings['weights'][k],2) for k,v in values.items()}
    score=round(sum(contributions.values())/max(1,sum(settings['weights'].values()))*100,1)
    eligible=reliable and age<=settings['max_age_hours'] and story.subcategory!='excluded_gossip' and (story.region!='global' or important)
    return score,{'contributions':contributions,'independent_origins':len(origins),'publisher_count':len({a.publisher for a in articles}),'primary_source':primary,'eligible':eligible,'importance_signal':important,'age_hours':round(age,1),'explanation':'Heuristic ranking, not a factual confidence score. Independence requires administrator-reviewed provenance; unknown origins do not count.'}

def research(story,articles):
    claims=[{'text':a.summary or a.title,'source':a.publisher,'url':a.url,'published_at':a.published_at,'status':'attributed' if a.summary else 'headline_only'} for a in articles[:12]]
    result={'summary':articles[0].summary or story.title,'confirmed_facts':[], 'attributed_claims':claims,'conflicting_reports':[], 'unverified_information':['Feed statements have not been independently fact-checked.'], 'analysis':'Ranking uses source metadata and headline signals; it does not establish truth.', 'uncertainties':['Event time unknown unless supplied by the source.','Conflicts may exist; automatic collection does not establish absence of disagreement.'], 'angle':'इस खबर की पृष्ठभूमि, उपलब्ध प्रमाण और भारत पर संभावित असर समझाएं।' if story.category!='entertainment' else 'फिल्म की कहानी नहीं, उसकी रिलीज़, उद्योग पर असर और आंकड़ों की सीमाएं समझाएं।', 'box_office':[], 'record_claims':[], 'evidence_status':'Attributed source reports — editorial verification required', 'why_it_matters':'Potential public-interest development; review the source evidence and impact before selection.', 'entity':'Not yet extracted', 'release_date':None, 'provider':'extractive', 'language':'source language'}
    if all(not article.summary for article in articles):
        result['evidence_status']='Headline discovery only — further research required'
        result['analysis']='Only headlines, dates and source links were collected. These are research leads, not a verified account of the event. Verify important facts before writing an original script.'
        result['unverified_information']=['No article text was collected for this story. A headline or its repetition is not independent confirmation.']
    return result
