import Link from 'next/link';
import {notFound} from 'next/navigation';
import {prisma} from '../../../../../lib/prisma';

export const dynamic = 'force-dynamic';
export default async function HardwareCard({params}:{params:Promise<{id:string;hwId:string}>}){
  const {id,hwId}=await params;
  const hw=await prisma.ecuHardware.findFirst({where:{id:hwId,ecuId:id},include:{ecu:true}});
  if(!hw)notFound();
  const [pins,memories,loaders,software,evidence]=await Promise.all([
    prisma.ecuPin.findMany({where:{ecuId:id,hardwareId:hwId},orderBy:[{connector:'asc'},{pin:'asc'}]}),
    prisma.ecuMemory.findMany({where:{ecuId:id,hardwareId:hwId}}),
    prisma.ecuLoader.findMany({where:{ecuId:id,hardwareId:hwId}}),
    prisma.ecuSoftware.findMany({where:{ecuId:id}}),
    prisma.ecuEvidence.findMany({where:{ecuId:id}})
  ]);
  return <main>
    <Link href={'/ecu/'+id}>← Карточка ЭБУ</Link>
    <h1>{hw.ecu.manufacturer} {hw.ecu.model} · HW {hw.partNumber}</h1>
    <p><strong>Достоверность:</strong> {hw.verification}. PCB: {hw.pcbRevision||'не установлена'}. {hw.notes||''}</p>
    <section className="card"><h2>Идентификация</h2><p>Семейство: {hw.ecu.family||'не установлено'}; ревизия: {hw.revision||'не установлена'}; разъёмы: {hw.connectorInfo||'не подтверждены'}.</p>
    <p>SW, указанные для семейства (не обязательно совместимы с этой HW): {software.length?software.map(s=>s.softwareId).join(', '):'нет данных'}.</p></section>
    <section className="card"><h2>Распиновка именно этой HW ({pins.length})</h2>
      {pins.length?<div style={{overflowX:'auto'}}><table><thead><tr><th>Разъём</th><th>Пин</th><th>Цепь</th><th>Напряжение</th><th>Проверка</th><th>Источник</th></tr></thead><tbody>{pins.map(p=><tr key={p.id}><td>{p.connector}</td><td>{p.pin}</td><td>{p.signal}</td><td>{p.voltage||'—'}</td><td>{p.verification}</td><td>{p.evidenceUrl ? <a href={p.evidenceUrl}>Открыть</a> : 'Не указан'}</td></tr>)}</tbody></table></div>:<p>Нет распиновки, подтверждённой для данной аппаратной ревизии.</p>}</section>
    <section className="card"><h2>Процессор, Flash и EEPROM ({memories.length})</h2>
      {memories.length?memories.map(m=><p key={m.id}>{m.component} · {m.type} · {m.capacity||'размер не установлен'} · {m.addressRange||'адреса не установлены'} · {m.verification} · Чтение: {m.readMethod||'неизвестно'} · Запись: {m.writeMethod||'неизвестно'} · {m.evidenceUrl ? <a href={m.evidenceUrl}>Источник</a> : 'Источник не указан'}</p>):<p>MCU, память, адреса и объёмы не подтверждены для этой HW.</p>}</section>
    <section className="card"><h2>Проверенные способы чтения/записи ({loaders.length})</h2>
      {loaders.length?loaders.map(l=><p key={l.id}>{l.tool} {l.module||''} · {l.mode} · {l.operation||''} · {l.verification} · Состав копии: {l.backupScope||'не установлен'} · {l.evidenceUrl ? <a href={l.evidenceUrl}>Источник</a> : 'Источник не указан'}</p>):<p>Нет подтверждённых способов именно для этой HW. Общая поддержка семейства не означает совместимости.</p>}</section>
    <section className="card"><h2>Источники ({evidence.length})</h2><p>Источники семейства не подтверждают автоматически сведения для конкретной HW-ревизии.</p>
      {evidence.map(e=><p key={e.id}>{e.subject} · {e.verification} · <a href={e.sourceUrl} target="_blank" rel="noopener noreferrer">Источник</a></p>)}
      {!evidence.length&&<p>Источники отсутствуют.</p>}
    </section>
  </main>;
}
