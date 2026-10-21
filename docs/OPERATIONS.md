# Operations and troubleshooting

## Where to look

- Dashboard **Overview**: latest run status, counts, estimated next run, Telegram configuration.
- **Activity**: individual source outcomes and delivery status. Empty feeds are not called success.
- `data/api-error.log`, `data/web-error.log`: local process errors. The launcher avoids API access logs.
- Worker stdout: JSON with run ID, status, new story count and article count.
- `audit` table: source/provider error classes, settings history, editorial decisions, prompt generation and AI usage. URLs/tokens from exception strings are not logged.

Run status `success` means configured sources returned usable feed items; it does not mean a story is fact-checked or a Telegram message was delivered. `partial` means at least one source returned items and another failed/was empty. `failed` includes no sources, all-source failure, no source data, or pipeline failure. `interrupted` means a previous worker exited before completion.

## Common problems

- **Login fails:** check the `.env` password and restart the API after changing it. Password must have 16+ characters and session secret 32+. Five-minute global login throttling may temporarily block repeated attempts. Production uses secure cookies over HTTPS; local HTTP requires `COOKIE_SECURE=false`.
- **Backend unavailable:** start API and frontend, inspect logs, check database migration, and verify ports 8000/3000. A manual monitoring request can exceed the front proxy's time limit with many slow sources; inspect Activity before retrying because the worker can still be active.
- **No alerts:** check token/chat configuration, source enabling, category filters, freshness, threshold, original-report provenance and primary-source flags. Do not lower reliability checks simply to get more notifications.
- **Old stories:** publication times are used when supplied. Unknown dates stay unknown and receive conservative freshness. The monitor skips future-dated and older-than-configured items.
- **No entertainment:** check the enabled HT Entertainment/Telugu Cinema and NDTV Movies feeds in Settings and inspect Activity for errors. They use headline discovery, so follow important leads with independent research. An unavailable feed is reported as an error, not replaced with fabricated content.
- **Global prompt blocked:** select the story for video explicitly. Selecting for research alone is not video approval.
- **Copy fails:** browser clipboard permission or secure-context restrictions may apply. Use Markdown download; both contain the same complete generated prompt. Editing the form invalidates its previous prompt preview; generate again before copying.
- **Lock contention:** another worker owns the lock. Do not delete lock files to force a run. PostgreSQL releases advisory locks when the connection exits; local file locks release on process exit. The persistent lock file may remain without being locked.
- **Source failures:** confirm feed access/terms and availability. Private destinations, non-HTTP schemes, unusual ports and oversized responses are rejected. Some sources change their format or deny automated retrieval; disable or replace them.
- **AI failure:** extractive research remains available. Check model compatibility and cost budget. The app never treats model output as independently confirmed evidence.

## Backup and recovery

For SQLite, stop application/worker writes and copy `data/studio.db` to a protected backup location. Also back up the private environment separately with restricted access. For production use managed PostgreSQL backups, point-in-time recovery and regular restore drills. Do not share a live SQLite file between separate Azure replicas.

Use Alembic for schema changes. Test upgrades on a restored copy before production. `001` has a downgrade for test use; downgrading drops data and should not be used as a production rollback plan. Restore from backup instead.

Prompt records retain the generated text and Channel Bible version, so later configuration changes do not alter historical prompts. Audits retain prior versions. Rejected/archived stories remain stored; no automatic retention deletion is enabled. Plan appropriate backup/log retention and capacity monitoring as volume grows.

## Security boundaries

Single-administrator signed, expiring, HttpOnly, SameSite session cookies; mutating API calls require a same-origin custom header. No permissive CORS is installed. Cookies are secure in Azure. The local application binds loopback only. Keep `.env` and data outside source control, rotate session secrets to invalidate sessions, and restrict local file permissions to intended operators.

The app's request throttles are process-local and reset on restart. The production template limits API replicas to one; use an ingress/WAF policy for perimeter throttling and organization login/MFA where required. Source HTML is stripped and React escapes displayed text. AI receives JSON source data with explicit untrusted-data instructions and no tool access. This reduces risk but is not a proof against every model-level prompt injection; all generated drafts require review. No automatic action consumes a model's instructions.
