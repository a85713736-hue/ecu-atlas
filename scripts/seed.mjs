import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const forum = 'https://ecuforum.ru/topic/10146-proshivki-dlya-avtomobiley-haval-tank-geely-changan-chery-exeed-jac-s-dvigatelyami-15-20-gdit-bosch-mg1ua008-mg1us008/';
const catalog = 'https://tcepro.app/catalogs/bosch-mg1us008';
const records = [
  {id:'bosch-mg1us008-haval-dargo',manufacturer:'Haval',model:'Dargo',family:'Bosch MG1US008',hw:'F01RB0DG2L',sw:'F01R0AD5DS',engine:'2.0 GDIT'},
  {id:'bosch-mg1us008-chery-tiggo8-pro-max',manufacturer:'Chery',model:'Tiggo 8 Pro Max',family:'Bosch MG1US008',hw:'F01R00DX1B',sw:'Z21G07A259',engine:'2.0 GDIT'},
  {id:'bosch-mg1us008-changan-uni-k',manufacturer:'Changan',model:'UNI-K',family:'Bosch MG1US008',hw:'F01R00DP9X',sw:'Z51307AI53',engine:'2.0 GDIT'}
];
try {
  for (const r of records) {
    await prisma.ecu.upsert({
      where:{id:r.id},
      create:{id:r.id,manufacturer:r.manufacturer,model:r.model,family:r.family,hw:r.hw,sw:r.sw,status:'source-listed'},
      update:{}
    });
    await prisma.ecuHardware.upsert({
      where:{id:r.id+'-hw'},
      create:{id:r.id+'-hw',ecuId:r.id,partNumber:r.hw,verification:'source-listed',notes:'Идентификатор HW опубликован в каталоге калибровщика; аппаратно не проверен.'},
      update:{}
    });
    await prisma.ecuSoftware.upsert({
      where:{id:r.id+'-sw'},
      create:{id:r.id+'-sw',ecuId:r.id,softwareId:r.sw,engine:r.engine,vehicle:r.model,verification:'source-listed'},
      update:{}
    });
    const loaderSpecs = [
      {suffix:'bitbox454',tool:'BitBox',module:'FID 454',mode:'Bench',operation:'Flash/EEPROM RD/WR; checksum',url:'https://bitsoftware.com/bitbox/catalog/58',notes:'Поддержка на уровне семейства; нужен Scanmatik 2 Pro и адаптер с управлением питанием. Проверить защиту и HW.'},
      {suffix:'pcm92',tool:'PCMflash',module:'92',mode:'Bench/service',operation:'Flash RD/WR/CK; EEPROM RD/WR',url:'https://ecutools.eu/chip-tuning/pcmflash/module-92/',notes:'Для MG1US008 SPC574K/TC277TP. Новая защита может препятствовать работе. Требуется сверка HW.'},
      ...(r.manufacturer==='Haval'?[{suffix:'pcm89',tool:'PCMflash',module:'89',mode:'OBD / зависит от автомобиля',operation:'RD/WR/CK для Great Wall/Haval MG1US008',url:'https://scanmatik.pro/pages/pcm',notes:'Поддержка семейства Great Wall/Haval подтверждена перечнем PCMflash; совместимость конкретной HW/SW не гарантирована.'}]:[])
    ];
    for (const l of loaderSpecs) {
      await prisma.ecuLoader.upsert({
        where:{id:r.id+'-'+l.suffix},
        create:{id:r.id+'-'+l.suffix,ecuId:r.id,tool:l.tool,module:l.module,mode:l.mode,operation:l.operation,evidenceUrl:l.url,verification:'family-documented',notes:l.notes},
        update:{mode:l.mode,operation:l.operation,evidenceUrl:l.url,notes:l.notes,verification:'family-documented'}
      });
    }
    await prisma.ecuEvidence.upsert({
      where:{id:r.id+'-pcm92-pinout'},
      create:{id:r.id+'-pcm92-pinout',ecuId:r.id,subject:'Bench распиновка из руководства PCMflash 92',claim:'T2: +12V 103/63/46; GND 97; CAN-L 64; CAN-H 65. Применимость к конкретному HW НЕ подтверждена.',sourceUrl:'https://pcmflash.ru/downloads/pcmflash_92.pdf',sourceType:'документация загрузчика',verification:'family-documented',notes:'Не переносить в таблицу контактов автомобиля до проверки аппаратной ревизии и ориентации разъёма.'},
      update:{}
    });
    await prisma.ecuEvidence.upsert({
      where:{id:r.id+'-evidence'},
      create:{id:r.id+'-evidence',ecuId:r.id,subject:'Идентификаторы HW/SW',claim:r.manufacturer+' '+r.model+': '+r.hw+' / '+r.sw,sourceUrl:forum,sourceType:'профессиональный форум, коммерческий перечень',verification:'source-listed',notes:'Не подтверждает распиновку, MCU, EEPROM или способ подключения.'},
      update:{}
    });
    await prisma.source.upsert({
      where:{id:r.id+'-source'},
      create:{id:r.id+'-source',ecuId:r.id,url:catalog,title:'TCEPro: каталог Bosch MG1US008',verified:false},
      update:{}
    });
  }
  console.log('ECU Atlas: three source-listed Bosch MG1US008 examples seeded');
} finally {
  await prisma.$disconnect();
}
