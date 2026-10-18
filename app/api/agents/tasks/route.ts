import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../../lib/prisma';
import { timingSafeEqual } from 'node:crypto';

export const dynamic = 'force-dynamic';
const headers = { 'Cache-Control': 'no-store' };

function authorized(request: NextRequest) {
  const secret = process.env.AGENT_ADMIN_TOKEN;
  const supplied = request.headers.get('authorization')?.replace(/^Bearer /i, '') || '';
  if (!secret) { console.warn('[agent-auth] AGENT_ADMIN_TOKEN missing in runtime environment'); return false; }
  if (!supplied) { console.warn('[agent-auth] Authorization bearer token missing'); return false; }
  const a = Buffer.from(secret);
  const b = Buffer.from(supplied.trim());
  const matches = a.length === b.length && timingSafeEqual(a, b);
  if (!matches) console.warn('[agent-auth] Token mismatch (secret and submitted values differ)');
  return matches;
}

export async function GET(request: NextRequest) {
  if (!authorized(request)) return NextResponse.json({error:'Unauthorized'}, {status:401,headers});
  try {
    const tasks = await prisma.task.findMany({
      where:{role:'research'},
      orderBy:{createdAt:'desc'},
      take:30
    });
    return NextResponse.json({tasks}, {headers});
  } catch {
    return NextResponse.json({error:'Database unavailable'}, {status:503,headers});
  }
}

export async function POST(request: NextRequest) {
  if (!authorized(request)) return NextResponse.json({error:'Unauthorized'}, {status:401,headers});
  let body: unknown;
  try { body = await request.json(); } catch {
    return NextResponse.json({error:'Invalid JSON'}, {status:400,headers});
  }
  const ecu = typeof body === 'object' && body !== null && 'ecu' in body && typeof body.ecu === 'string'
    ? body.ecu.trim() : '';
  if (!ecu || ecu.length > 120 || !/^[\p{L}\p{N}\s._+()\/-]+$/u.test(ecu)) {
    return NextResponse.json({error:'Введите обозначение ЭБУ (1–120 символов)'}, {status:400,headers});
  }
  try {
    const task = await prisma.task.create({data:{ecuId:ecu,role:'research',status:'queued'}});
    return NextResponse.json({task,notice:'Задача поставлена в очередь; исполнитель пока не подключён'}, {status:201,headers});
  } catch {
    return NextResponse.json({error:'Database unavailable'}, {status:503,headers});
  }
}
