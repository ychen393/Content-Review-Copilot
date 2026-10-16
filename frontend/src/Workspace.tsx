import React,{useEffect,useState} from 'react'

type Project={id:string;name:string;brand:string;platform:string}
type Task={id:string;project_id:string;mode:'generate'|'review';brief:string;quantity:number}
type Item={id:string;title:string;body:string;status:string;current_version:number;review_session_id?:string}
const request=async<T,>(url:string,body?:unknown):Promise<T>=>{
 const response=await fetch(url,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
 if(!response.ok)throw new Error((await response.json().catch(()=>({}))).detail||'请求失败')
 return response.json()
}
export default function Workspace({onLegacyReview,onReviewItem}:{onLegacyReview:()=>void;onReviewItem:(item:{id:string;title:string;body:string})=>void}){
 const [projects,setProjects]=useState<Project[]>([])
 const [selected,setSelected]=useState('')
 const [tasks,setTasks]=useState<Task[]>([])
 const [task,setTask]=useState('')
 const [items,setItems]=useState<Item[]>([])
 const [name,setName]=useState('')
 const [brand,setBrand]=useState('')
 const [platform,setPlatform]=useState('小红书')
 const [mode,setMode]=useState<'generate'|'review'>('review')
 const [quantity,setQuantity]=useState(1)
 const [brief,setBrief]=useState('')
 const [title,setTitle]=useState('')
 const [body,setBody]=useState('')
 const [error,setError]=useState('')
 const loadProjects=()=>request<Project[]>('/api/projects').then(setProjects).catch(e=>setError(String(e)))
 useEffect(()=>{loadProjects()},[])
 useEffect(()=>{setTasks([]);setTask('');if(selected)request<Task[]>(`/api/projects/${selected}/tasks`).then(setTasks).catch(e=>setError(String(e)))},[selected])
 useEffect(()=>{setItems([]);if(task)request<Item[]>(`/api/tasks/${task}/items`).then(setItems).catch(e=>setError(String(e)))},[task])
 const submit=async(action:()=>Promise<void>)=>{setError('');try{await action()}catch(e){setError(e instanceof Error?e.message:String(e))}}
 return <main className="mx-auto max-w-6xl p-6 space-y-6">
 <header className="flex flex-wrap justify-between items-center gap-3"><div><p className="text-sm text-muted">Content Review Copilot / M2</p><h1 className="text-3xl font-bold">内容项目工作台</h1><p className="text-muted mt-1">创建项目、组织内容任务、保存文案版本。AI 批量生成将在下一阶段接入。</p></div><button className="btn-secondary" onClick={onLegacyReview}>返回单篇审核</button></header>
 {error&&<div role="alert" className="rounded-lg border border-red-300 p-3 text-red-700">{error}</div>}
 <section className="card space-y-3"><h2 className="text-xl font-semibold">新建项目</h2>
 <div className="grid gap-3 md:grid-cols-3"><input aria-label="项目名称" className="border rounded-lg p-2" placeholder="项目名称" value={name} onChange={e=>setName(e.target.value)}/><input aria-label="品牌" className="border rounded-lg p-2" placeholder="品牌" value={brand} onChange={e=>setBrand(e.target.value)}/><input aria-label="发布渠道" className="border rounded-lg p-2" value={platform} onChange={e=>setPlatform(e.target.value)}/></div>
 <button className="btn-primary" disabled={!name.trim()} onClick={()=>submit(async()=>{const p=await request<Project>('/api/projects',{name:name.trim(),brand,platform});setName('');await loadProjects();setSelected(p.id)})}>创建项目</button></section>
 <section className="card space-y-3"><h2 className="text-xl font-semibold">项目与任务</h2>
 <label className="block text-sm">选择项目 <select className="block border rounded-lg p-2 mt-1 w-full" value={selected} onChange={e=>setSelected(e.target.value)}><option value="">选择项目</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name} · {p.brand||'未设置品牌'}</option>)}</select></label>
 {selected&&<><div className="grid md:grid-cols-3 gap-3"><label>任务模式<select className="block border rounded-lg p-2 w-full" value={mode} onChange={e=>setMode(e.target.value as 'generate'|'review')}><option value="review">审核</option><option value="generate">生成（先创建任务）</option></select></label><label>内容数量<input className="block border rounded-lg p-2 w-full" type="number" min={1} max={20} value={quantity} onChange={e=>setQuantity(Number(e.target.value))}/></label><label>任务 Brief<input className="block border rounded-lg p-2 w-full" value={brief} onChange={e=>setBrief(e.target.value)}/></label></div>
 <button className="btn-primary" onClick={()=>submit(async()=>{const t=await request<Task>('/api/tasks',{project_id:selected,mode,brief,quantity});setTasks(await request<Task[]>(`/api/projects/${selected}/tasks`));setTask(t.id)})}>创建任务</button>
 <label className="block">选择任务<select className="block border rounded-lg p-2 w-full" value={task} onChange={e=>setTask(e.target.value)}><option value="">选择任务</option>{tasks.map(t=><option key={t.id} value={t.id}>{t.mode==='review'?'审核':'生成'} · {t.brief||t.id.slice(0,8)}（最多 {t.quantity} 篇）</option>)}</select></label></>}
 </section>
 {task&&<section className="card space-y-3"><h2 className="text-xl font-semibold">内容队列 · {items.length} 篇</h2>
 <p className="text-sm text-muted">可手工添加待审核稿件；新增版本不会覆盖历史版本。</p>
 <input aria-label="内容标题" className="border rounded-lg p-2 w-full" placeholder="标题" value={title} onChange={e=>setTitle(e.target.value)}/>
 <textarea aria-label="内容正文" className="border rounded-lg p-2 w-full" rows={4} placeholder="输入内容正文" value={body} onChange={e=>setBody(e.target.value)}/>
 <button className="btn-primary" onClick={()=>submit(async()=>{await request(`/api/tasks/${task}/items`,{title,body});setItems(await request<Item[]>(`/api/tasks/${task}/items`));setTitle('');setBody('')})}>添加内容</button>
 <div className="space-y-2">{items.map((item,i)=><div key={item.id} className="border rounded-lg p-3 flex items-center justify-between gap-3"><div><p className="font-semibold">{i+1}. {item.title||'未命名稿件'}</p><p className="text-sm text-muted">状态 {item.status} · 版本 v{item.current_version}</p></div><div className="flex gap-2"><button className="btn-secondary" disabled={!item.body.trim()} onClick={()=>onReviewItem(item)}>{item.review_session_id?"继续审核":"开始审核"}</button><button className="btn-secondary" onClick={()=>submit(async()=>{const text=window.prompt('修改内容（将保存新版本）',item.body);if(text===null)return;await request(`/api/items/${item.id}/versions`,{text,title:item.title,created_by:'user',reason:'Manual edit'});setItems(await request<Item[]>(`/api/tasks/${task}/items`))})}>新建版本</button></div></div>)}</div>
 </section>}
 </main>
}
