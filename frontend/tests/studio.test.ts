import {test} from 'node:test';
import assert from 'node:assert/strict';
import {blank,saveDraft,recoverDraft,discardDraft,draftKey,readApiResponse,StudioApiError} from '../lib/studio.ts';

function memoryStorage(){
  const items=new Map<string,string>();
  return {getItem:(key:string)=>items.get(key)??null,setItem:(key:string,value:string)=>{items.set(key,value);},removeItem:(key:string)=>{items.delete(key);}};
}

test('Hindi draft and production choices survive switching stories and reload',()=>{
  const storage=memoryStorage(),form={...blank,summary:'भारत की खबर — अपुष्ट समय',target_duration_seconds:90};
  assert.equal(saveDraft(storage,'story-one',form),true);
  assert.deepEqual(recoverDraft(storage,'story-one'),form);
  assert.equal(recoverDraft(storage,'story-two'),null);
  discardDraft(storage,'story-one');assert.equal(recoverDraft(storage,'story-one'),null);
});

test('broken or mismatched drafts do not replace saved server edits',()=>{
  const storage=memoryStorage();
  for(const raw of ['{broken','null',JSON.stringify({version:1,storyId:'another',form:blank}),JSON.stringify({version:1,storyId:'one',form:{...blank,summary:42}}),JSON.stringify({version:1,storyId:'one',form:{...blank,target_duration_seconds:900}})]){
    storage.setItem(draftKey('one'),raw);assert.equal(recoverDraft(storage,'one'),null);
  }
});

test('draft storage failure is reported instead of claiming a saved draft',()=>{
  const blocked={getItem:()=>{throw new Error('denied');},setItem:()=>{throw new Error('full');},removeItem:()=>{throw new Error('denied');}};
  assert.equal(saveDraft(blocked,'one',blank),false);assert.equal(recoverDraft(blocked,'one'),null);assert.equal(discardDraft(blocked,'one'),false);
});

test('unrecognised draft fields including credential-like text are not restored',()=>{
  const storage=memoryStorage();
  storage.setItem(draftKey('one'),JSON.stringify({version:1,storyId:'one',form:{...blank,password:'do-not-restore',unexpected:'extra'}}));
  assert.deepEqual(recoverDraft(storage,'one'),blank);
});

test('expired sessions retain a distinct status for the sign-in recovery flow',async()=>{
  await assert.rejects(readApiResponse(new Response('{"detail":"Sign in required"}',{status:401})),(e:unknown)=>e instanceof StudioApiError&&e.status===401);
  await assert.rejects(readApiResponse(new Response('<html>unauthorized</html>',{status:401})),(e:unknown)=>e instanceof StudioApiError&&e.status===401);
});

test('proxy HTML and malformed error bodies produce useful plain-language errors',async()=>{
  await assert.rejects(readApiResponse(new Response('<html>gateway error</html>',{status:502})),/backend response/);
  await assert.rejects(readApiResponse(new Response('null',{status:500})),/request failed/);
  await assert.rejects(readApiResponse(new Response('{"detail":[{"msg":"invalid"}]}',{status:422})),/fields are invalid/);
  assert.deepEqual(await readApiResponse(new Response('{"saved":true}')),{saved:true});
});
