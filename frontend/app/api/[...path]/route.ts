import {NextRequest} from 'next/server';
export const dynamic='force-dynamic';
async function proxy(request:NextRequest,{params}:{params:Promise<{path:string[]}>}){
  const {path}=await params;
  if(path.some(p=>p==='..'||p.includes('/')||p.includes('\\')))return new Response('Invalid path',{status:400});
  const headers=new Headers();
  for(const key of ['content-type','cookie','x-studio-action']){const value=request.headers.get(key);if(value)headers.set(key,value);}
  const body=['GET','HEAD'].includes(request.method)?undefined:await request.text();
  if(body&&body.length>200000)return Response.json({detail:'Request too large'},{status:413});
  try{
    const upstream=await fetch((process.env.API_INTERNAL_URL||'http://127.0.0.1:8000')+'/api/'+path.map(encodeURIComponent).join('/')+request.nextUrl.search,{method:request.method,headers,body,cache:'no-store',redirect:'manual',signal:AbortSignal.timeout(230000)});
    const output=new Headers();
    for(const key of ['content-type','set-cookie','content-disposition']){const value=upstream.headers.get(key);if(value)output.set(key,value);}
    output.set('Cache-Control','no-store');
    return new Response(upstream.body,{status:upstream.status,headers:output});
  }catch{return Response.json({detail:'Backend unavailable or timed out. Check Activity before retrying a run.'},{status:502});}
}
export {proxy as GET,proxy as POST,proxy as PUT,proxy as PATCH};
