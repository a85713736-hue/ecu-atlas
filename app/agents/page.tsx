import Link from 'next/link';
import AgentControls from '../../components/AgentControls';

export const metadata = { title: 'Панель агентов — ECU Atlas' };

const stages = [
  {name:'Поиск источников',detail:'Бесплатный RSS-поиск, каталоги загрузчиков, технические форумы'},
  {name:'Извлечение данных',detail:'HW/SW, MCU, Flash/EEPROM, режимы OBD/Bench/Boot'},
  {name:'Верификация',detail:'Сопоставление сведений и сохранение ссылок на первоисточники'},
  {name:'Публикация',detail:'Кандидаты сохраняются в отчёте задания. Подтверждённые данные публикуются только после проверки'},
];

export default function AgentsPage() {
  return <main>
    <p><Link href="/">← Каталог ЭБУ</Link></p>
    <h1>Панель исследовательских агентов</h1>
    <p>Создание заданий доступно через защищённую очередь. Задания из очереди обрабатываются GitHub Actions по расписанию после настройки токена исполнителя.</p>
    <AgentControls/>
    <div className="card">
      <h2>Запуск поиска через GitHub Actions</h2>
      <p><label htmlFor="ecu">Модель ЭБУ или номер HW</label></p>
      <input id="ecu" name="ecu" value="Bosch MG1US008" readOnly aria-describedby="launch-help"/>
      <p id="launch-help"><small>Для отдельного исследования откройте GitHub Actions, выберите «Run workflow» и введите обозначение ЭБУ. Для обработки очереди оставьте поле пустым.</small></p>
      <p><a href="https://github.com/a85713736-hue/ecu-atlas/actions/workflows/research-agent.yml" target="_blank" rel="noopener noreferrer">Открыть запуск агента в GitHub ↗</a></p>
    </div>
    <h2>Этапы обработки</h2>
    {stages.map((stage,index)=><div className="card" key={stage.name}>
      <h3>{index+1}. {stage.name}</h3><p>{stage.detail}</p>
      <small>Статус: {index===3?'Заблокировано до проверки':'Автоматическая обработка очереди каждые 3 часа'}</small>
    </div>)}
    <div className="card">
      <h2>Результаты исследований</h2>
      <p>После запуска GitHub Actions файлы <code>latest.json</code>, <code>extracted.json</code> и <code>review.json</code> будут доступны в разделе Artifacts соответствующего запуска.</p>
      <p>Результаты обработки веб-очереди отображаются выше в карточках заданий. Данные требуют ручной проверки.</p>
    </div>
  </main>;
}
