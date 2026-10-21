export type Form={
  summary:string;sources:string;confirmed_facts:string;uncertainties:string;angle:string;
  additional_instructions:string;image_instructions:string;target_duration_seconds:number;
  story_format:'auto'|'explainer'|'timeline'|'news_update';
  animation_style:'hybrid'|'motion_graphics'|'anchor_led';
  anchor_presence:'balanced'|'minimal'|'frequent';
};
export const textFields=['summary','sources','confirmed_facts','uncertainties','angle','additional_instructions','image_instructions'] as const;
export const formLimits={summary:15000,sources:15000,confirmed_facts:15000,uncertainties:15000,angle:5000,additional_instructions:10000,image_instructions:5000};
export const blank:Form={summary:'',sources:'',confirmed_facts:'',uncertainties:'',angle:'',additional_instructions:'',image_instructions:'I will attach story images separately. Ask for missing permanent references.',target_duration_seconds:240,story_format:'auto',animation_style:'hybrid',anchor_presence:'balanced'};

export class StudioApiError extends Error{
  status:number;
  constructor(message:string,status:number){super(message);this.name='StudioApiError';this.status=status;}
}

export async function readApiResponse(response:Response){
  let data;
  try{data=JSON.parse(await response.text());}
  catch{throw new StudioApiError(response.status===401?'Sign in required':'The studio could not read the backend response. Check Activity before retrying a discovery run.',response.status);}
  if(!response.ok){
    const detail=data&&typeof data==='object'?data.detail:null;
    const problems=Array.isArray(detail)?detail.slice(0,3).map(item=>{
      const location=Array.isArray(item?.loc)?item.loc.filter((part:unknown)=>part!=='body').join(' → '):'';
      return location&&typeof item?.msg==='string'?location+': '+item.msg:'';
    }).filter(Boolean).join('; '):'';
    throw new StudioApiError(typeof detail==='string'?detail:response.status===422?'Some fields are invalid. '+(problems||'Check their values and try again.'):'The request failed. Please try again.',response.status);
  }
  return data;
}

export async function api(path:string,method='GET',body?:unknown){
  let response;
  try{response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json','X-Studio-Action':'1'},cache:'no-store',...(body===undefined?{}:{body:JSON.stringify(body)})});}
  catch{throw new StudioApiError('The studio could not reach its backend. Check your connection and that the studio is running.',0);}
  return readApiResponse(response);
}

type DraftStorage=Pick<Storage,'getItem'|'setItem'|'removeItem'>;
export const draftKey=(storyId:string)=>'drishti:story-draft:v1:'+storyId;

export function saveDraft(storage:DraftStorage,storyId:string,form:Form):boolean{
  try{storage.setItem(draftKey(storyId),JSON.stringify({version:1,storyId,form}));return true;}
  catch{return false;}
}

export function recoverDraft(storage:DraftStorage,storyId:string):Form|null{
  try{
    const raw=storage.getItem(draftKey(storyId));
    if(!raw)return null;
    const item=JSON.parse(raw),data=item?.form;
    if(item?.version!==1||item.storyId!==storyId||!data||typeof data!=='object')return null;
    const form={...blank};
    for(const key of textFields){if(typeof data[key]!=='string'||data[key].length>formLimits[key])return null;form[key]=data[key];}
    if(!Number.isInteger(data.target_duration_seconds)||data.target_duration_seconds<60||data.target_duration_seconds>300)return null;
    if(!['auto','explainer','timeline','news_update'].includes(data.story_format)||!['hybrid','motion_graphics','anchor_led'].includes(data.animation_style)||!['balanced','minimal','frequent'].includes(data.anchor_presence))return null;
    form.target_duration_seconds=data.target_duration_seconds;
    form.story_format=data.story_format;form.animation_style=data.animation_style;form.anchor_presence=data.anchor_presence;
    return form;
  }catch{return null;}
}

export function discardDraft(storage:DraftStorage,storyId:string):boolean{
  try{storage.removeItem(draftKey(storyId));return true;}catch{return false;}
}
