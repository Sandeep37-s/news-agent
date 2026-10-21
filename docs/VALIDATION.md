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
- **65 backend tests passed**, including paired output, current-edit snapshot isolation, source context in picture prompts, production preference validation, authenticated saved-history restoration, headline-only warnings, expired global alert rescoring, undated alert suppression, classification word boundaries and non-receipts exclusion. Existing separate/combined download, migration, AI, Telegram and security checks still pass. Tests use a separate temporary database.
- The live database was backed up and upgraded to migration 002. Browser checks confirmed both generated prompt tabs and successful picture/combined clipboard feedback. Older saved prompts retain their news-story text; regenerate them to add a picture prompt.
- Quality update: the local database was backed up and upgraded to migration 003 to preserve snapshot research-gap notes. Browser checks confirmed preference propagation into both prompts, restoration after refresh, older version selection, preservation of current form choices and combined clipboard success. The earlier story-only records remain readable.

The tests include migration upgrade/downgrade, RSS/Atom parsing, URL normalization, blocked private destinations, deduplication, clustering, Indian/global/entertainment classification, scoring and shared-origin suppression, partial-source and no-data failure, scheduler locking, restart recovery before and after article persistence, notification deduplication/backoff and uncertain delivery, authentication/CSRF, Unicode login rejection, persisted settings and template validation, explicit global selection, complete Markdown prompt export, box-office metadata, provider call budgets, and isolation of untrusted source instructions.

Six frontend tests pass for draft recovery/validation, storage failures, expired-session status and malformed backend responses. TypeScript and the production build pass. The launcher now waits for API/schema and dashboard readiness; its successful local restart was verified.
Browser checks also confirmed same-tab draft recovery after refresh, returning to an older story outside the top 100 via the recent-story selector, and restoration of the story/draft after sign-out and sign-in. Test-only editorial direction was restored to its original value afterwards. Actual eight-hour expiry is covered through response/status tests rather than waiting eight hours.

One dependency deprecation warning concerns the current Starlette/httpx test-client integration. It does not fail tests or affect the running application's HTTP client. No live API keys are used in tests.

## External checks still required

- Actual Telegram delivery: requires your bot token and authorized chat IDs. Only mocked delivery was exercised.
- Actual AI-provider calls and billing: requires a chosen model/provider and key. The provider interface and cost controls were tested with fixtures.
- Managed PostgreSQL integration and network access: the local tests use SQLite. Production PostgreSQL advisory locking is implemented but requires verification against the deployment database.
- Docker image build/run: Docker is unavailable on this machine.
- Azure deployment, cloud execution history, HTTPS/identity/network configuration, backups and production cost budgets: no cloud deployment has occurred.
- Bicep compilation now passes locally with CLI 0.48.1. A compile-only CI job is included. Azure what-if, deployment and actual Consumption-container memory/runtime validation still require the chosen environment.
- Headline-feed follow-up: HT India/Entertainment/Telugu and NDTV India/Movies/Hindi returned usable RSS during connection checks and are enabled in headline-only mode. Their publicly stated feed restrictions still apply; no commercial content licence has been purchased. Direct Google/YouTube/X/Instagram connectors remain unimplemented.

Automatic research is conservative: it preserves source-attributed reports rather than claiming independent fact-checking. Headline classification/clustering and numeric extraction can miss or misinterpret context; review the research before creating a production brief.
Box-office extraction intentionally skips figures near budget, fee, salary, investment or audience-count wording. Mixed contexts can therefore require manual research even when a receipt figure is present; an empty result never establishes that no box-office figures exist.

Cost-efficiency update: migration 004 adds feed validators and query indexes. Tests verify conditional 304 parsing avoidance, source edit invalidation, recovery from interrupted research with a cached response, bounded source reads, two article SELECTs for 300 ranked stories and at most six commits for a 120-article fixture run. Test lock files now belong to the test database directory so the real hourly worker cannot interfere. SQLite foreign keys are enforced. No Azure cost reduction has been measured or guaranteed.
