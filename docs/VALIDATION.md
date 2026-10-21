# Delivery verification — 21 October 2026

## Verified on this Windows machine

- Python dependencies installed in the project-local virtual environment; Node dependencies installed with a retained package lock.
- Alembic migration and idempotent configuration bootstrap completed on the actual local SQLite database.
- Initial live BBC feed run retrieved and persisted 38 articles. Further hourly runs added new items; an unchanged repeat added zero articles/stories.
- Windows Task Scheduler task `DrishtiHourlyDiscovery` is installed, repeats every hour, and has completed with exit status 0. It runs outside the browser, but still requires this computer to be available.
- FastAPI health endpoint and Next.js dashboard returned HTTP 200.
- Browser checks: administrator login, overview counts, Indian story cards, source trail/timestamps, uncertainty labels, scoring explanation, and prepopulated prompt form.
- Follow-up fix: the builder now offers an explicit **Select for video & generate prompt** action, preserving edited form fields. Browser verification produced a complete 7,291-character prompt for the selected entertainment story and confirmed clipboard success. Selection is still required by the backend; the combined button performs that deliberate selection first. Inline feedback explains readiness, errors and copying.
- Production Next.js build and TypeScript checks passed.
- **36 automated tests passed**, including paired output, current-edit snapshot isolation, source context in picture prompts, production preference validation, authenticated saved-history restoration, headline-only warnings, expired global alert rescoring, undated alert suppression, classification word boundaries and non-receipts exclusion. Existing separate/combined download, migration, AI, Telegram and security checks still pass. Tests use a separate temporary database.
- The live database was backed up and upgraded to migration 002. Browser checks confirmed both generated prompt tabs and successful picture/combined clipboard feedback. Older saved prompts retain their news-story text; regenerate them to add a picture prompt.
- Quality update: the local database was backed up and upgraded to migration 003 to preserve snapshot research-gap notes. Browser checks confirmed preference propagation into both prompts, restoration after refresh, older version selection, preservation of current form choices and combined clipboard success. The earlier story-only records remain readable.

The tests include migration upgrade/downgrade, RSS/Atom parsing, URL normalization, blocked private destinations, deduplication, clustering, Indian/global/entertainment classification, scoring and shared-origin suppression, partial-source and no-data failure, scheduler locking, restart recovery before and after article persistence, notification deduplication/backoff and uncertain delivery, authentication/CSRF, Unicode login rejection, persisted settings and template validation, explicit global selection, complete Markdown prompt export, box-office metadata, provider call budgets, and isolation of untrusted source instructions.

One dependency deprecation warning concerns the current Starlette/httpx test-client integration. It does not fail tests or affect the running application's HTTP client. No live API keys are used in tests.

## External checks still required

- Actual Telegram delivery: requires your bot token and authorized chat IDs. Only mocked delivery was exercised.
- Actual AI-provider calls and billing: requires a chosen model/provider and key. The provider interface and cost controls were tested with fixtures.
- Managed PostgreSQL integration and network access: the local tests use SQLite. Production PostgreSQL advisory locking is implemented but requires verification against the deployment database.
- Docker image build/run: Docker is unavailable on this machine.
- Azure deployment, cloud execution history, HTTPS/identity/network configuration, backups and production cost budgets: no cloud deployment has occurred.
- Bicep compiler validation: automatic compiler download did not finish within the bounded download window. Run `az bicep build --file infra/main.bicep` and the documented Azure `what-if` before deployment; template compilation has not been claimed as passing.
- Headline-feed follow-up: HT India/Entertainment/Telugu and NDTV India/Movies/Hindi returned usable RSS during connection checks and are enabled in headline-only mode. Their publicly stated feed restrictions still apply; no commercial content licence has been purchased. Direct Google/YouTube/X/Instagram connectors remain unimplemented.

Automatic research is conservative: it preserves source-attributed reports rather than claiming independent fact-checking. Headline classification/clustering and numeric extraction can miss or misinterpret context; review the research before creating a production brief.
Box-office extraction intentionally skips figures near budget, fee, salary, investment or audience-count wording. Mixed contexts can therefore require manual research even when a receipt figure is present; an empty result never establishes that no box-office figures exist.
