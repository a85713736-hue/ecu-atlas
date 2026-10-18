'use client';
import { useState } from 'react';

type Source = {category?:string;title?:string;source_url?:string;snippet?:string;verification?:string};
type Candidate = {category?:string;value?:string;excerpt?:string;verification?:string;hardware_revision?:string|null};
type Document = {source_url?:string;candidates?:Candidate[]};
type Claim = {subject?:string;claim?:string;excerpt?:string;source_url?:string;hardware_revision?:string|null;verification?:string};
type Report = {candidates?:Claim[];review?:{source_count?:number;review_status?:string};sources?:Source[];extracted_documents?:Document[];errors?:Array<{error?:string;category?:string}>;publish_allowed?:boolean;error?:string};
type Task = {id:string;ecuId:string|null;status:string;createdAt:string;resultJson?:string|null};
const labels:Record<string,string> = {identification:'Идентификация HW/SW',mcu:'Процессор',memory:'Flash / EEPROM',pinout:'Распиновка',loader:'Загрузчики и режимы',field_reports:'Практический опыт',bosch_part_number:'Номер Bosch',mode:'Режим подключения'};
const statuses:Record<string,string> = {queued:'В очереди',running:'Исследуется',completed:'Собраны материалы',failed:'Ошибка исследования'};
function safeUrl(value?:string){try {const u=new URL(value||'');return u.protocol==='https:'||u.protocol==='http:'?u.href:null;}catch{return null;}}
function reportOf(t:Task):Report|null {if(!t.resultJson)return null;try {const r=JSON.parse(t.resultJson);return r&&typeof r==='object'?r:null;}catch{return null;}}
export default function AgentControls(){
 const [token,setToken]=useState('');
 const [ecu,setEcu]=useState('Bosch MG1US008');
 const [tasks,setTasks]=useState<Task[]>([]);
 const [message,setMessage]=useState('');
 const [busy,setBusy]=useState(false);
 const [expanded,setExpanded]=useState<string|null>(null);
 const [targetEcu,setTargetEcu]=useState('');
 const [targetHw,setTargetHw]=useState('');
 async function importCandidate(taskId:string,index:number){
  setBusy(true);setMessage('');
  try {
   const response=await fetch('/api/agents/candidates',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({taskId,ecuId:targetEcu,hardwareId:targetHw,index})});
   const data=await response.json();
   if(!response.ok)throw new Error(data.error||'Ошибка импорта');
   setMessage('Кандидат сохранён как непроверенное доказательство для выбранной HW.');
  }catch(error){setMessage(error instanceof Error?error.message:'Ошибка сети');}
  finally{setBusy(false);}
 }
 async function call(method:'GET'|'POST'){
  setBusy(true);setMessage('');
  try {
   const response=await fetch('/api/agents/tasks',{
    method,cache:'no-store',headers:{Authorization:'Bearer '+token,...(method==='POST'?{'Content-Type':'application/json'}:{})},
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
  <p><small>Административный токен используется только для запросов и не сохраняется в браузере.</small></p>
  <p><label htmlFor="agent-token">Административный токен</label></p>
  <input id="agent-token" type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} placeholder="AGENT_ADMIN_TOKEN"/>
  <p><label htmlFor="agent-ecu">Модель ЭБУ / HW</label></p>
  <input id="agent-ecu" value={ecu} maxLength={120} onChange={e=>setEcu(e.target.value)} placeholder="Bosch MG1US008"/>
  <p><button disabled={!token||!ecu.trim()||busy} onClick={()=>call('POST')}>Добавить в очередь</button>{' '}<button disabled={!token||busy} onClick={()=>call('GET')}>Обновить список</button></p>
  {message&&<p role="status">{message}</p>}
  <h3>Перенос кандидатов в доказательства</h3>
  <p><small>Укажите внутренние ID существующего ЭБУ и его аппаратной ревизии. Импорт не подтверждает достоверность.</small></p>
  <input value={targetEcu} onChange={e=>setTargetEcu(e.target.value)} placeholder="ECU ID" aria-label="ECU ID"/>{' '}
  <input value={targetHw} onChange={e=>setTargetHw(e.target.value)} placeholder="HW ID" aria-label="HW ID"/>
  <h3>Последние задания</h3>
  {tasks.length===0?<p><small>Задания не загружены. Введите токен и нажмите «Обновить список».</small></p>:<div>{tasks.map(t=>{
   const report=reportOf(t);
   return <article key={t.id} style={{borderTop:'1px solid #7775',padding:'12px 0'}}>
    <p><strong>{t.ecuId||'ЭБУ'}</strong> — {statuses[t.status]||t.status} · {new Date(t.createdAt).toLocaleString('ru-RU')}</p>
    {t.status==='completed'&&report&&<p><small>Источников: {report.review?.source_count??report.sources?.length??0} · Данные требуют проверки</small></p>}
    <button onClick={()=>setExpanded(expanded===t.id?null:t.id)}>{expanded===t.id?'Скрыть материалы':'Посмотреть материалы'}</button>
    {expanded===t.id&&<div style={{padding:'10px 0'}}>
     {!report?<p>Отчёт ещё не получен. Для обработки очереди требуется запущенный исполнитель SearXNG.</p>:<>
      <p><strong>Статус проверки:</strong> {report.review?.review_status==='pending'?'Ожидает ручной проверки':report.error?'Ошибка':'Не проверено'}. Автоматическая публикация запрещена.</p>
      {report.error&&<p role="alert">{report.error}</p>}
      <h4>Найденные источники</h4>
      {!report.sources?.length?<p>Нет источников.</p>:<ul>{report.sources.map((s,i)=><li key={i}><strong>{labels[s.category||'']||s.category||'Источник'}</strong>: {safeUrl(s.source_url)?<a href={safeUrl(s.source_url)!} target="_blank" rel="noopener noreferrer">{s.title||s.source_url}</a>:s.title||'Без ссылки'} <small>— не проверено</small>{s.snippet&&<p><small>{s.snippet}</small></p>}</li>)}</ul>}
      <h4>Структурированные кандидаты с источниками ({report.candidates?.length||0})</h4>
      <p><small>Для привязки к HW необходимы точный аппаратный номер, ревизия платы и проверка первоисточника. До этого сведения не переносятся в подтверждённую базу.</small></p>
      <p><small>Это черновые утверждения. Не подтверждены для конкретной аппаратной ревизии.</small></p>
      {report.candidates?.length ? <ul>{report.candidates.map((c,i)=><li key={i}><button disabled={busy||!token||!targetEcu||!targetHw} onClick={()=>importCandidate(t.id,i)}>Сохранить для HW (не проверено)</button>{' '}<strong>{labels[c.subject||'']||c.subject}:</strong> {c.claim} · HW: {c.hardware_revision||'не установлена'} · {safeUrl(c.source_url)?<a href={safeUrl(c.source_url)!} target="_blank" rel="noopener noreferrer">Источник</a>:'Без источника'}{c.excerpt&&<p><small>{c.excerpt}</small></p>}</li>)}</ul>:<p>Структурированные кандидаты пока не сформированы.</p>}
      <h4>Кандидаты: MCU, память, HW, загрузчики</h4>
      {!report.extracted_documents?.some(d=>d.candidates?.length)?<p>Пока нет извлечённых технических данных.</p>:report.extracted_documents?.map((d,i)=><div key={i}><p><small>{safeUrl(d.source_url)?<a href={safeUrl(d.source_url)!} target="_blank" rel="noopener noreferrer">{d.source_url}</a>:d.source_url}</small></p><ul>{d.candidates?.map((c,j)=><li key={j}><strong>{labels[c.category||'']||c.category}:</strong> {c.value} <small>— не проверено, HW-ревизия не подтверждена</small>{c.excerpt&&<p><small>{c.excerpt}</small></p>}</li>)}</ul></div>)}
      {!!report.errors?.length&&<><h4>Ошибки сбора</h4><ul>{report.errors.map((e,i)=><li key={i}>{e.category?e.category+': ':''}{e.error}</li>)}</ul></>}
      <p><small>Это поисковые материалы, а не подтверждённая распиновка, ёмкость EEPROM или инструкция по подключению.</small></p>
     </>}
    </div>}
   </article>;
  })}</div>}
  <p><small>queued — запись в PostgreSQL; running — обработка; completed — материалы собраны, но не опубликованы.</small></p>
 </section>;
}
