'use client';
import { useState } from 'react';
type Task = {id:string;ecuId:string|null;status:string;createdAt:string};
export default function AgentControls(){
 const [token,setToken]=useState('');
 const [ecu,setEcu]=useState('Bosch MG1US008');
 const [tasks,setTasks]=useState<Task[]>([]);
 const [message,setMessage]=useState('');
 const [busy,setBusy]=useState(false);
 async function call(method:'GET'|'POST'){
  setBusy(true);setMessage('');
  try {
   const response=await fetch('/api/agents/tasks',{
    method,headers:{Authorization:'Bearer '+token,...(method==='POST'?{'Content-Type':'application/json'}:{})},
    ...(method==='POST'?{body:JSON.stringify({ecu})}:{})
   });
   const data=await response.json();
   if(!response.ok)throw new Error(data.error||'Ошибка запроса');
   if(method==='GET')setTasks(data.tasks);
   else setTasks(old=>[data.task,...old].slice(0,30));
   setMessage(method==='POST'?data.notice:'Очередь обновлена');
  }catch(error){setMessage(error instanceof Error?error.message:'Ошибка сети');}
  finally{setBusy(false);}
 }
 return <section className="card">
  <h2>Очередь исследований</h2>
  <p><small>Токен используется только для запросов с этой страницы и не сохраняется в браузере. Не вводите его на чужих устройствах.</small></p>
  <p><label htmlFor="agent-token">Административный токен</label></p>
  <input id="agent-token" type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} placeholder="AGENT_ADMIN_TOKEN"/>
  <p><label htmlFor="agent-ecu">Модель ЭБУ / HW</label></p>
  <input id="agent-ecu" value={ecu} maxLength={120} onChange={e=>setEcu(e.target.value)} placeholder="Bosch MG1US008"/>
  <p><button disabled={!token||!ecu.trim()||busy} onClick={()=>call('POST')}>Добавить в очередь</button>{' '}<button disabled={!token||busy} onClick={()=>call('GET')}>Обновить список</button></p>
  {message&&<p role="status">{message}</p>}
  <h3>Последние задания</h3>
  {tasks.length===0?<p><small>Задания не загружены. Введите токен и нажмите «Обновить список».</small></p>:<ul>{tasks.map(t=><li key={t.id}>{t.ecuId} — {t.status} · {new Date(t.createdAt).toLocaleString('ru-RU')}</li>)}</ul>}
  <p><small>Статус queued означает только запись в PostgreSQL. Автоматический исполнитель пока не подключён.</small></p>
 </section>;
}
