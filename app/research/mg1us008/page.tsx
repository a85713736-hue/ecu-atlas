import Link from 'next/link';

export const metadata = {title:'Bosch MG1US008 — техническое досье | ECU Atlas'};
const rows=[
  ['BitBox','FID 454','Bench','Flash и EEPROM, чтение/запись; сверить конкретный HW','https://bitsoftware.com/bitbox/catalog/58'],
  ['PCMflash','92','Bench / service','В документации указаны MG1US008 SPC574K / TC277TP; ограничения защиты','https://ecutools.eu/chip-tuning/pcmflash/module-92/'],
  ['PCMflash','89','OBD / семейство','Официальный перечень: Great Wall/Haval MG1US008, RD/WR/CK; сверить автомобиль и HW','https://scanmatik.pro/pages/pcm']
];
export default function Mg1us008Research(){
  return <main>
    <Link href="/">← Каталог</Link>
    <h1>Bosch MG1US008</h1>
    <p>Техническое досье семейства. Данные не являются универсальной распиновкой для всех аппаратных ревизий.</p>
    <section className="card">
      <h2>Процессор и память</h2>
      <p>В документации PCMflash 92 для MG1US008 встречаются варианты SPC574K и TC277TP. Точная модель MCU, размеры Flash и EEPROM, диапазоны адресов и защита определяются по конкретному HW и требуют отдельного подтверждения.</p>
      <p><strong>Статус:</strong> семейство документировано; конкретные аппаратные ревизии не идентифицированы.</p>
    </section>
    <section className="card">
      <h2>Загрузчики</h2>
      <div style={{overflowX:'auto'}}><table><thead><tr><th>Загрузчик</th><th>Модуль</th><th>Режим</th><th>Особенности</th></tr></thead><tbody>
        {rows.map(r=><tr key={r[0]+r[1]}><td><a href={r[4]} target="_blank" rel="noopener noreferrer">{r[0]}</a></td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>)}
      </tbody></table></div>
    </section>
    <section className="card">
      <h2>Bench-подключение: справочные данные</h2>
      <p>Ранее опубликованная таблица T2 из руководства PCMflash 92: +12 В — 103/63/46; GND — 97; CAN-L — 64; CAN-H — 65.</p>
      <p><strong>Не подключать по этой таблице без сверки:</strong> номера контактов, ориентация разъёма и применимость к аппаратной ревизии должны быть подтверждены по актуальному оригиналу документации и реальному блоку.</p>
      <p><a href="https://pcmflash.ru/downloads/pcmflash_92.pdf" target="_blank" rel="noopener noreferrer">Документация PCMflash 92</a></p>
    </section>
    <section className="card">
      <h2>Привязка к автомобилям</h2>
      <p>PCMflash 89: Great Wall/Haval 1.5T и 2.0T (MG1US008) — RD/WR/CK по перечню модулей; также DongFeng 1.5T (UP8/MG1US008). Эти сведения подтверждают поддержку семейства в конкретных группах автомобилей, но не гарантируют работу с любым SW или защитой.</p>
      <p><a href="https://scanmatik.pro/pages/pcm" target="_blank" rel="noopener noreferrer">Перечень PCMflash</a> · <a href="https://ecutools.eu/publications/pcmflash-138-update-23092024/" target="_blank" rel="noopener noreferrer">Обновление PCMflash 1.3.8</a></p>
    </section>
    <section className="card">
      <h2>Что ещё требуется установить</h2>
      <p>Для каждого HW: фотография платы с двух сторон, точная маркировка MCU, Flash/EEPROM и их размеры, полный backup по загрузчикам, разъёмы и автомобильная распиновка, Boot/Test/GPT, защита и процедура восстановления.</p>
      <p>Неподтверждённые адреса, контакты и размеры памяти намеренно не публикуются как факты.</p>
    </section>
  </main>;
}
