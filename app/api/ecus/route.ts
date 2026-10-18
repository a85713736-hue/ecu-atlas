import {NextResponse} from 'next/server';
import {prisma} from '../../../lib/prisma';
export async function GET(){try{return NextResponse.json(await prisma.ecu.findMany({take:100,orderBy:{createdAt:'desc'}}))}catch{return NextResponse.json({error:'database unavailable'},{status:503})}}
