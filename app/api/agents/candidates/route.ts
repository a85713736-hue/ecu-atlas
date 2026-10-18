import {NextRequest,NextResponse} from 'next/server';
import {prisma} from '../../../../lib/prisma';
import {timingSafeEqual} from 'node:crypto';

export async function POST(request:NextRequest){
 const secret=process.env.AGENT_ADMIN_TOKEN||'';
 const token=request.headers.get('authorization')?.replace(/^Bearer /i,'').trim()||'';
 const a=Buffer.from(secret),b=Buffer.from(token);
 if(!secret||a.length!==b.length||!timingSafeEqual(a,b))
  return NextResponse.json({error:'Unauthorized'},{status:401});
 const body=await request.json();
 const task=await prisma.task.findFirst({where:{id:body.taskId,role:'research',status:'completed'}});
 const hardware=await prisma.ecuHardware.findFirst({where:{id:body.hardwareId,ecuId:body.ecuId}});
 if(!task?.resultJson||!hardware)return NextResponse.json({error:'Task or hardware not found'},{status:404});
 const candidates=JSON.parse(task.resultJson).candidates;
 const item=Array.isArray(candidates)?candidates[body.index]:null;
 if(!item||typeof item.claim!=='string'||typeof item.subject!=='string'||typeof item.source_url!=='string')
  return NextResponse.json({error:'Invalid candidate'},{status:400});
 const evidence=await prisma.ecuEvidence.create({data:{
  ecuId:hardware.ecuId,subject:item.subject.slice(0,100),claim:item.claim.slice(0,500),
  sourceUrl:item.source_url.slice(0,2000),sourceType:'agent_candidate',
  verification:'unverified',notes:'Hardware: '+hardware.partNumber+'; HW ID: '+hardware.id+'; task: '+task.id
 }});
 return NextResponse.json({evidence},{status:201});
}
