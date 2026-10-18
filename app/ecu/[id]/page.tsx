import Link from 'next/link';
import {notFound} from 'next/navigation';
import {prisma} from '../../../lib/prisma';
import Viewer from '../../../components/EcuViewer';

export const dynamic = 'force-dynamic';

export default async function EcuPage({params}:{params:Promise<{id:string}>}) {
  const {id}=await params;
  const ecu=await prisma.ecu.findUnique({
    where:{id},
    include:{
      sources:true,
      hardware:true,
      software:true,
      pins:true,
      memories:true,
      loaders:true,
      evidence:true
    }
  });
  if(!ecu)notFound();
  return <main>
    <Link href="/">← Каталог</Link>
    <h1>{ecu.manufacturer} {ecu.model} {ecu.family}</h1>
    <p>Общий статус: <strong>{ecu.status}</strong>. Непроверенные сведения нельзя использовать как инструкцию по подключению.</p>
    <Viewer/>
    <section className="card">
      <h2>Идентификация</h2>
      <p>HW: {ecu.hw||'неизвестно'} · SW: {ecu.sw||'неизвестно'} · MCU: {ecu.mcu||'не подтвержден'}</p>
    </section>
    <section className="card">
      <h2>Аппаратные ревизии ({ecu.hardware.length})</h2>
      {ecu.hardware.length?ecu.hardware.map(h=><div key={h.id}>
        <p><strong>{h.partNumber}</strong> · PCB {h.pcbRevision||'не установлена'} · {h.verification}</p>
        <p>{h.notes||'Описание ревизии пока отсутствует.'}</p>
        <p><Link href={'/ecu/'+ecu.id+'/hardware/'+h.id}>Открыть отдельную карту HW →</Link></p>
      </div>):<p>Подтверждённых данных пока нет.</p>}
    </section>
    <section className="card">
      <h2>Программное обеспечение ({ecu.software.length})</h2>
      {ecu.software.length?ecu.software.map(s=><p key={s.id}>{s.softwareId} · {s.calibration||'калибровка не указана'} · {s.verification}</p>):<p>Данные отсутствуют.</p>}
    </section>
    <section className="card">
      <h2>Распиновка ({ecu.pins.length})</h2>
      {ecu.pins.length?<div style={{overflowX:'auto'}}><table><thead><tr><th>Разъём</th><th>Контакт</th><th>Назначение</th><th>Статус</th></tr></thead><tbody>{ecu.pins.map(p=><tr key={p.id}><td>{p.connector}</td><td>{p.pin}</td><td>{p.signal}</td><td>{p.verification}</td></tr>)}</tbody></table></div>:<p>Распиновка не подтверждена.</p>}
    </section>
    <section className="card">
      <h2>Память и процессор ({ecu.memories.length})</h2>
      {ecu.memories.length?ecu.memories.map(m=><p key={m.id}>{m.component} · {m.type} · {m.capacity||'объём не установлен'} · {m.verification}</p>):<p>Нет подтверждённой карты памяти.</p>}
    </section>
    <section className="card">
      <h2>Чтение и запись ({ecu.loaders.length})</h2>
      {ecu.loaders.length?ecu.loaders.map(l=><p key={l.id}>{l.tool} {l.module||''} · {l.mode} · {l.operation||'операция не уточнена'} · {l.verification}</p>):<p>Совместимость загрузчиков пока не проверена.</p>}
    </section>
    <section className="card">
      <h2>Источники и проверка ({ecu.evidence.length+ecu.sources.length})</h2>
      {ecu.evidence.map(e=><p key={e.id}>{e.subject}: {e.claim} · {e.verification} · <a href={e.sourceUrl} target="_blank" rel="noopener noreferrer">Источник</a></p>)}
      {ecu.sources.map(s=><p key={s.id}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.title||s.url}</a> · {s.verified?'проверен':'не проверен'}</p>)}
      {!ecu.evidence.length&&!ecu.sources.length&&<p>Источники ещё не добавлены.</p>}
    </section>
  </main>;
}
