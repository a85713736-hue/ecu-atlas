# Local ECU research worker (Windows)

The queue lives on Render. The private research worker runs on your Windows machine next to Docker SearXNG. The SearXNG service stays localhost-only; no paid API or public search endpoint is required.

1. In Render web service Environment add **AGENT_WORKER_TOKEN**, a new random secret different from **AGENT_ADMIN_TOKEN**. Save/deploy.
2. Docker Desktop: start a local SearXNG instance with JSON enabled on `127.0.0.1:8080`; ensure its settings enable JSON output. The worker will not work without a search instance.
3. On Windows, clone `a85713736-hue/ecu-atlas`, open PowerShell at repository root and set environment variables for that terminal only:

```powershell
$env:AGENT_WORKER_TOKEN = 'YOUR_WORKER_TOKEN'
$env:SEARXNG_URL = 'http://127.0.0.1:8080'
$env:ECU_ATLAS_URL = 'https://ecu-atlas-web.onrender.com'
python agents/worker.py --once
# or repeat polling while PC is running
python agents/worker.py --interval 60
```

Do not commit tokens or paste them in chats. Worker claims tasks atomically, writes a compact **unverified** report to PostgreSQL and a full copy under `research/out/<task-id>.json`. Automatic publication of pinouts, EEPROM or wiring remains disabled. Running tasks require manual recovery if the worker crashes; no automatic lease/retry yet.
