import { NextRequest, NextResponse } from 'next/server';
import { timingSafeEqual } from 'node:crypto';
import { prisma } from '../../../../lib/prisma';

export const dynamic = 'force-dynamic';
const headers = { 'Cache-Control': 'no-store' };

function authorized(request: NextRequest) {
 const secret = process.env.AGENT_WORKER_TOKEN;
 const supplied = request.headers.get('authorization')?.replace(/^Bearer /i, '').trim() || '';
 if (!secret || !supplied) return false;
 const a = Buffer.from(secret); const b = Buffer.from(supplied);
 return a.length === b.length && timingSafeEqual(a,b);
}
export async function POST(request: NextRequest) {
 if (!authorized(request)) return NextResponse.json({error:'Unauthorized'}, {status:401,headers});
 let body: {action?:string;taskId?:string;status?:string;result?:unknown};
 try {body=await request.json();} catch {return NextResponse.json({error:'Invalid JSON'},{status:400,headers});}
 if(body.action==='claim'){
  const candidates=await prisma.task.findMany({where:{role:'research',status:'queued'},orderBy:{createdAt:'asc'},take:5});
  for(const task of candidates){
   const changed=await prisma.task.updateMany({where:{id:task.id,status:'queued'},data:{status:'running'}});
   if(changed.count===1)return NextResponse.json({task:{id:task.id,ecu:task.ecuId}}, {headers});
  }
  return NextResponse.json({task:null},{headers});
 }
 if(body.action==='complete'){
  if(typeof body.taskId!=='string' || !['completed','failed'].includes(body.status||''))return NextResponse.json({error:'Invalid status or taskId'},{status:400,headers});
  const data=JSON.stringify(body.result??null);
  if(data.length>250000)return NextResponse.json({error:'Result too large'},{status:413,headers});
  const changed=await prisma.task.updateMany({where:{id:body.taskId,role:'research',status:'running'},data:{status:body.status,resultJson:data}});
  if(changed.count!==1)return NextResponse.json({error:'Task not running or not found'},{status:409,headers});
  return NextResponse.json({ok:true},{headers});
 }
 return NextResponse.json({error:'Unknown action'},{status:400,headers});
}
