import {NextRequest,NextResponse} from 'next/server';
import {prisma} from '../../../../lib/prisma';
import {timingSafeEqual} from 'node:crypto';

export async function POST(request:NextRequest){
 const secret=process.env.AGENT_ADMIN_TOKEN||'';
 const token=request.headers.get('authorization')?.replace(/^Bearer /i,'').trim()||'';
 const a=Buffer.from(secret),b=Buffer.from(token);
 if(!secret||a.length!==b.length||!timingSafeEqual(a,b))
  return NextResponse.json({error:'Unauthorized'},{status:401});
 let body:Record<string,unknown>;
 try {body=await request.json();} catch {return NextResponse.json({error:'Invalid JSON'},{status:400});}
 if(typeof body.taskId!=='string'||typeof body.ecuId!=='string'||typeof body.hardwareId!=='string'||!Number.isInteger(body.index)||Number(body.index)<0)
  return NextResponse.json({error:'Invalid identifiers'},{status:400});
 const task=await prisma.task.findFirst({where:{id:body.taskId,role:'research',status:'completed'}});
 const hardware=await prisma.ecuHardware.findFirst({where:{id:body.hardwareId,ecuId:body.ecuId}});
 if(!task?.resultJson||!hardware)return NextResponse.json({error:'Task or hardware not found'},{status:404});
 let candidates:unknown;
 try {candidates=JSON.parse(task.resultJson).candidates;} catch {return NextResponse.json({error:'Invalid report'},{status:422});}
 const item=Array.isArray(candidates)?candidates[body.index]:null;
 if(!item||typeof item.claim!=='string'||typeof item.subject!=='string'||typeof item.source_url!=='string')
  return NextResponse.json({error:'Invalid candidate'},{status:400});
 if(item.claim.length>500||item.subject.length>100||item.source_url.length>2000)
  return NextResponse.json({error:'Candidate too long'},{status:422});
 try {if(new URL(item.source_url).protocol!=='https:')throw new Error('Invalid protocol');}
 catch{return NextResponse.json({error:'Invalid source URL'},{status:422});}
 const existing=await prisma.ecuEvidence.findFirst({where:{ecuId:hardware.ecuId,subject:item.subject,claim:item.claim,sourceUrl:item.source_url,notes:{contains:'HW ID: '+hardware.id+';'}}});
 if(existing)return NextResponse.json({evidence:existing,created:false});
 const evidence=await prisma.ecuEvidence.create({data:{
  ecuId:hardware.ecuId,subject:item.subject.slice(0,100),claim:item.claim.slice(0,500),
  sourceUrl:item.source_url.slice(0,2000),sourceType:'agent_candidate',
  verification:'unverified',notes:'Hardware: '+hardware.partNumber+'; HW ID: '+hardware.id+'; task: '+task.id
 }});
 return NextResponse.json({evidence},{status:201});
}
