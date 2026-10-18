import {notFound} from 'next/navigation';
import {prisma} from '../../../lib/prisma';
import Viewer from '../../../components/EcuViewer';
export const dynamic = 'force-dynamic';
export default async function EcuPage({params}:{params:Promise<{id:string}>}) {const {id}=await params;const ecu=await prisma.ecu.findUnique({where:{id},include:{sources:true}});if(!ecu)notFound();return <main><a href="/">← Каталог</a><h1>{ecu.manufacturer} {ecu.model} {ecu.family}</h1><Viewer/><div className="card"><p>HW: {ecu.hw||'неизвестно'}</p><p>SW: {ecu.sw||'неизвестно'}</p><p>MCU: {ecu.mcu||'не проверено'}</p><p>Статус: {ecu.status}</p></div><h2>Источники</h2>{ecu.sources.map(s=><p key={s.id}><a href={s.url} rel="noopener noreferrer" target="_blank">{s.title||s.url}</a> {s.verified?'· проверено':'· ожидает проверки'}</p>)}</main>}
