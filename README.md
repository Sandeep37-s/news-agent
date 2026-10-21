# Drishti — Hindi News Discovery Studio

A working Phase 1 editorial application built in `C:\Users\it\Documents\2d`: Next.js/React/TypeScript dashboard, Python FastAPI backend, SQLAlchemy storage, Alembic migrations, RSS/Atom and configurable JSON API adapters, conservative research, Telegram outbox, and a Claude production-prompt builder. No video generation, rendering, voice generation, or publishing is implemented.

**Installing on another laptop?** Follow [LAPTOP-SETUP.md](LAPTOP-SETUP.md) after cloning this repository. Each machine creates its own private environment and database.

## Open the installed local application

1. Run `Start-Studio.ps1` from PowerShell in this folder.
2. Open **http://localhost:3000**.
3. The administrator password is the `ADMIN_PASSWORD` value in your private `.env` file. Keep that file private. The installer generates random local credentials; there is no default shared password.
4. Use **Run discovery**, review a story, **Select for video**, then open **Prompt builder**. Edit research, generate the complete prompt, and copy it or download Markdown. Attach your images separately in Claude.

The application has already been installed and built in this folder. Its first live discovery run saved 38 feed articles. Active sources now include BBC India/World, NDTV India/Hindi/Movies, and Hindustan Times India/Entertainment/Telugu Cinema. The newly connected publisher feeds use **headlines-only discovery**: title, publisher, URL and timestamps; article excerpts, footage and images are not retained. Their feed terms remain applicable, including personal/non-commercial restrictions; enabling a connection does not purchase commercial content rights. All seed provenance groups are `unknown`: popularity alone will not trigger alerts.

## Parameters and persistence

| Location | Purpose |
|---|---|
| `.env` | Local secrets and server settings; never committed |
| `config/settings.json` | Versioned initial monitoring and scoring parameters |
| `config/sources.json` | Initial source definitions |
| `config/channel_bible.md` | Initial permanent channel rules |
| `config/video_prompt_template.md` | Reusable production template |
| `data/studio.db` | Local SQLite database, live settings, stories, research, decisions, prompts, runs, notifications, audit history |
| Dashboard → Settings | Edit persisted monitoring settings, sources, Channel Bible, and prompt template |
| `infra/parameters.example.json` | Azure deployment parameter template, no secrets |

Bootstrap loads defaults **once**. Changing a seed file later does not overwrite saved settings. Use the dashboard after initialization. Channel/template versions and previous settings are recorded in the audit table; current configuration is also available through authenticated `/api/settings`. `GET /api/audit` exposes recent audit entries to the administrator.

## Fresh local setup (Windows)

Requires Python 3.14 and Node.js 24. Run from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe scripts/setup.py
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m backend.bootstrap
Set-Location frontend
npm.cmd ci
npm.cmd run build
Set-Location ..
.\Start-Studio.ps1
```

For development, run the backend with `.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --no-access-log` and run `npm.cmd run dev` in `frontend`. On Linux substitute `.venv/bin/python`. Run backend commands from the project root so the relative SQLite path is consistent.

`Start-Studio.ps1` stores process IDs and logs under `data/`. Do not launch a second copy on the same ports. Close the owned processes when finished; the launcher prints their IDs. Local SQLite supports one machine only. Production uses PostgreSQL and its database-wide advisory lock.

## Sources and hourly discovery

Settings → Sources supports RSS/Atom (`kind: rss`) and licensed news/search JSON APIs (`kind: json`). Add a public HTTPS feed URL, category, region, and enabled flag. Feeds are fetched with bounded network retries, a 20-second timeout, a 2 MB response ceiling, and up to 100 items per source/run. Only title, a short excerpt (up to 500 characters), timestamps and URLs are retained; full articles are not scraped.

For JSON APIs, use `options` such as:

```json
{"items_key":"articles","api_key_env":"LICENSED_NEWS_KEY","fields":{"title":"title","summary":"description","url":"url","published_at":"publishedAt","event_at":"eventAt"}}
```

Keep the corresponding API key in the server environment. This adapter supports Bearer authentication and flat field mappings; adapt the interface in `backend/sources.py` for other licensed schemas. Do not put tokens in source URLs or options. Redirect destinations are checked, and authorization is dropped on cross-host redirects. Production must also restrict outbound network destinations to prevent DNS rebinding; application DNS checks are not a replacement for network controls.

Sources must permit your use. The seed entertainment feeds come from the [Hindustan Times feed directory](https://www.hindustantimes.com/rss). [BBC feed documentation](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm) links its feed terms. Source availability does not grant rights to reuse associated images, audio or footage. Enable additional Hindi, government, regional and licensed sources appropriate to your use.

Local one-time run:

```powershell
.\.venv\Scripts\python.exe -m backend.monitor
```

Local hourly schedule (explicit installation; not needed if using Azure):

```powershell
.\scripts\Install-HourlyTask.ps1
```

The Windows task runs once per hour while this computer can run tasks. It is not a substitute for cloud scheduling. To remove it: `Unregister-ScheduledTask -TaskName DrishtiHourlyDiscovery`.

The hourly Windows task has been installed on this machine as `DrishtiHourlyDiscovery`, and successful scheduled runs have been observed. You do not need to install it again here. Use `Stop-Studio.ps1` to stop the local dashboard/API; that does not disable the separate monitoring task.

Azure uses a native Container Apps Job with cron `0 * * * *`, one replica, a 30-minute timeout, and no permanent polling loop. PostgreSQL advisory locking also prevents overlap with manual runs. A process exit releases the lock; the next owner records abandoned runs as interrupted. Change both the dashboard's interval and the actual external scheduler together. The next-run display is explicitly an estimate, not proof that a scheduler is installed.

## Editorial and entertainment behavior

- India is primary; global notifications require a higher threshold and a major-development signal. Global stories remain awaiting direction, and a prompt requires explicit **Select for video**.
- Ranking displays freshness, coverage, growth, reviewed origin groups, importance, India relevance, evidence and explainability contributions. Weights and thresholds are editable.
- Source independence defaults to unknown. Set an `origin_group` only after reviewing original reporting provenance. Syndicated sources must share the same group. `primary` means an appropriate original source for the claims being monitored, not simply a reputable publication. A primary report or the configured minimum number of reviewed independent origins is required for an automatic alert.
- Headline overlap and numeric checks cluster related English/Hindi reports conservatively. This is a transparent first-version heuristic, not cross-language semantic equivalence. It can miss paraphrases or misclassify stories; human review remains necessary. Geographic and importance signals are likewise heuristic.
- Facts are not automatically marked confirmed. Research separates attributed claims, confirmed facts, conflicts, unknowns and analysis. An empty conflict list means none recorded, not proof of agreement. The editor can save a research review without losing original source records.
- Entertainment supports upcoming releases, box-office updates, record claims, celebrity/industry developments, and regional cinema. Gossip-pattern stories are ineligible for alerts.
- Box-office extraction records separate candidate figures, currency where explicit, territory, measure, reporting period, source, report timestamp and uncertainty. Missing values remain unknown. Conflicting figures are preserved separately; no definitive total is invented. Record headlines remain unverified until comparison category, period and evidence are established. Review extracted amounts before use—automatic extraction can include a budget or another number.

## Optional AI research and Hindi summaries

The zero-cost default is source-attributed extractive research. Configure `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` for an OpenAI-compatible `/chat/completions` provider, then enable `ai_enabled` in monitoring settings. The provider must support JSON response mode. The interface sends short source evidence only and gives the model no tools. It returns a visibly labeled draft; it cannot change evidence, settings or source verification.

`notification_language` accepts `en` or `hi`. Source evidence retains its original language. Hindi AI draft summaries require a configured provider; without one, the app labels the source-language fallback rather than fabricating a translation. The documentary rules and suggested angles remain Hindi-oriented.

Daily call limits and a conservative reserved-cost budget are enforced before requests. Fill in provider token prices and choose a per-call reserve above the maximum expected request cost. Estimated usage is audited when returned by the provider. This is an application-side estimate, not a guaranteed billing cap; also configure hard limits with your provider. Unchanged stories are not summarized again. Updated stories retain the previous manual editorial review.

## Telegram

See `docs/TELEGRAM.md` for BotFather, authorized chat discovery, connection tests and troubleshooting. Set `TELEGRAM_BOT_TOKEN` and comma-separated `TELEGRAM_CHAT_IDS` only in the server environment or Key Vault. No credentials reach the browser. Alerts are queued only for eligible stories and authorized recipients.

Each story/chat pair gets at most one automatic alert. HTTP 429 and server failures retry on later runs with persistent backoff, maximum five attempts. Network response loss is **uncertain** because Telegram offers no sendMessage idempotency key: inspect the chat before explicitly queuing a retry. Interrupted sending is also marked uncertain. Failed messages never remove dashboard stories. Test notification sends require a deliberate Settings action.

## Tests and verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Set-Location frontend
npm.cmd run build
```

Fixtures do not need live websites. Tests cover feed parsing, normalization, clustering, ranking, classification, source failures, no-data failure, restart recovery, lock contention, migrations, auth/CSRF, persisted configuration, Telegram delivery and deduplication, box-office metadata, untrusted source instructions, and complete prompt export. See `docs/VALIDATION.md` for the actual verified scope and remaining external checks.

## Docker and Azure

Docker Compose includes PostgreSQL, migrations, API, dashboard, and an on-demand monitoring service. Set a strong URL-safe `POSTGRES_PASSWORD` in `.env`, then:

```text
docker compose up --build -d
docker compose --profile jobs run --rm monitor
```

PostgreSQL and API have no public host ports. Only the web service binds localhost:3000. Compose does not install a schedule. Docker is not installed on the development machine used for this delivery, so the container build/run must be checked on the deployment machine.

See `docs/AZURE.md` for deployment, secrets, migration job, hourly scheduling, health checks, recurring costs and subscription prerequisites. No Azure resources have been created or billed by this project setup.

See `docs/OPERATIONS.md` for backup, recovery and failure diagnosis.
#   n e w s - a g e n t  
 
