# Azure deployment runbook

No subscription, resource group, region, budget or production credentials were supplied. Deployment is prepared but has not been executed. The local application does not depend on Azure. Do not infer free credits or free service eligibility.

## Prerequisites

Use the [cost-conscious design](AZURE-COSTS.md). The existing environment must provide the built-in **Consumption** workload profile. Default container sizes are 0.25 vCPU / 0.5 GiB, adjustable per component using `apiSize`, `webSize` and `workerSize` (`standard` = 0.5 vCPU / 1 GiB). Validate memory and cold starts in the real environment before production use.

Use an approved Azure subscription and resource group, Azure Container Registry, an existing Container Apps managed environment, a user-assigned managed identity, Key Vault and managed PostgreSQL Flexible Server. Place the environment and database on a compatible private network with working private DNS. Disable public database access. The template deliberately reuses these resources rather than making a database publicly reachable or selecting a paid subscription for you.

Grant the managed identity `AcrPull` on the registry and `Key Vault Secrets User` on the vault. Limit permissions to these resource scopes. Restrict dashboard access using your organization's access gateway/IP controls in addition to the application's password. A production identity provider/MFA can be placed in front of the web application. The API's ingress is internal; do not publish port 8000.

Key Vault secrets required by the template:

| Secret | Value |
|---|---|
| `database-url` | `postgresql+psycopg://USER:URL_ENCODED_PASSWORD@PRIVATE_HOST:5432/studio?sslmode=require` |
| `admin-password` | A unique random password of at least 16 characters |
| `session-secret` | A unique random value of at least 32 characters |
| `telegram-token` | Your official bot token, only with `enableTelegram=true` |
| `telegram-chats` | Authorized comma-separated chat IDs, only with `enableTelegram=true` |

For deployment without Telegram, retain `enableTelegram=false` (the default); Telegram secret references are omitted. The monitor receives database and optional Telegram credentials; the migration job receives only the database credential. Never use mock IDs with a real token. Set optional AI environment and Key Vault references only if you intend to use a paid provider.

Use the Azure Portal or secure secret-input mechanisms; do not paste secrets into `parameters.example.json`, shell history, Git, or chat. Use private endpoints/network controls and the environment's outbound restrictions to allow only configured news/provider destinations, Telegram, Key Vault and database connectivity. DNS validation in the app is a supplementary check, not a full SSRF network boundary.

## Build images

Build and push immutable image tags or digests using your approved build environment:

```text
docker build -f Dockerfile.backend -t REGISTRY.azurecr.io/drishti-api:v1 .
docker build -t REGISTRY.azurecr.io/drishti-web:v1 frontend
docker push REGISTRY.azurecr.io/drishti-api:v1
docker push REGISTRY.azurecr.io/drishti-web:v1
```

`API_INTERNAL_URL` is evaluated at runtime by the Next.js server proxy; no backend secret or URL is baked into browser JavaScript. Containers run as non-root users. The API and scheduled job use the same backend image.

## Deploy and migrate

Copy `infra/parameters.example.json` to an environment-specific parameter file with your existing resource names, image tags, vault URI (trailing slash), and dashboard URL. The template defaults to an hourly UTC cron expression.

```text
az bicep build --file infra/main.bicep
az deployment group what-if --resource-group YOUR_GROUP --template-file infra/main.bicep --parameters @YOUR_PARAMETERS.json
az deployment group create --resource-group YOUR_GROUP --template-file infra/main.bicep --parameters @YOUR_PARAMETERS.json
az containerapp job start --name drishti-migrate --resource-group YOUR_GROUP
az containerapp job execution list --name drishti-migrate --resource-group YOUR_GROUP
```

Wait for migration completion before using the dashboard or initiating discovery. A scheduled job that starts before migration finishes should fail visibly; it must not be reported as successful. The migration job runs Alembic followed by idempotent default configuration initialization. For existing deployments, back up first, apply compatible migrations before activating changed application revisions, and test rollback against the backup.

Use the deployment's `dashboard` output. On first deployment, if the final host was not known, update `dashboardUrl` and redeploy so Telegram links point to the correct address. A custom approved domain avoids this bootstrap step. Verify HTTPS, login, `/health` internally, source retrieval, persistence across restarts, and a real authorized Telegram test.

```text
az containerapp job start --name drishti-monitor --resource-group YOUR_GROUP
az containerapp job execution list --name drishti-monitor --resource-group YOUR_GROUP
```

The [Container Apps Jobs documentation](https://learn.microsoft.com/en-us/azure/container-apps/jobs) describes scheduled execution. `0 * * * *` means the top of every hour in UTC, independent of your computer or browser. Job parallelism is one, the default timeout is 600 seconds (`monitorTimeoutSeconds`, allowed 60–1,800), automatic job retries are zero, and the app's PostgreSQL advisory lock prevents concurrent manual/scheduled workers. External requests and outbox retries are bounded. Do not replace the hourly schedule with frequent polling.

To change cadence, update the Bicep `cronExpression`, deploy, and save matching `interval_minutes` in the dashboard. Calendar schedules are authoritative; the dashboard estimate can be stale after manual runs or missed executions.

## Operational validation and costs

Use Activity and structured run logs to distinguish success, partial source failures, failed/no-data runs and interrupted runs. Configure Azure Monitor alerts for failed executions, missing successful runs, database errors and memory/time limits. Check outbox failures separately from ingestion. API `/health` verifies database connectivity; it does not assert news freshness.

Budget for PostgreSQL compute/storage/backups, registry storage, Container Apps API/web requests and scheduled execution, logs, Key Vault operations, networking, and optional AI/news APIs. There are no image/video API dependencies. Check the current Azure Pricing Calculator in your actual region and subscription before deployment. Set Azure Cost Management budgets and retention limits. Scale-to-zero is configured for web/API; PostgreSQL still has its own recurring charges. AI cost figures are estimates and need provider price configuration.

Production database integration, container execution and an actual cloud schedule must be verified after credentials/network provisioning; a Bicep compile alone does not prove deployment success.
