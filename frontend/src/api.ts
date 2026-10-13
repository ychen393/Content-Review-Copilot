import type {Decision,Session} from './types'
const json=async(res:Response)=>{if(!res.ok){const body=await res.json().catch(()=>({}));throw new Error(body.detail||'处理未完成。当前稿件和审核进度已保留。')}return res.json()}
export const api={
 parseDocument:(file:File):Promise<{filename:string;text:string}>=>{const body=new FormData();body.append('file',file);return fetch('/api/documents/parse',{method:'POST',body}).then(json)},
 create:(body:Record<string,unknown>):Promise<Session>=>fetch('/api/reviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(json),
 action:(id:string,name:string,query=''):Promise<Session>=>fetch(`/api/reviews/${id}/${name}${query}`,{method:'POST'}).then(json),
 decisions:(id:string,stage:'first'|'second',decisions:Record<string,Decision>):Promise<Session>=>fetch(`/api/reviews/${id}/decisions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage,decisions})}).then(json),
 list:():Promise<Session[]>=>fetch('/api/reviews').then(json), get:(id:string):Promise<Session>=>fetch(`/api/reviews/${id}`).then(json),
 exportUrl:(id:string)=>`/api/reviews/${id}/export/docx`
}
