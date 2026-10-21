# PROJECT: AI-POWERED HINDI YOUTUBE NEWS DISCOVERY STUDIO

## 1. Your Role

Act as a senior full-stack engineer, AI systems architect, Python developer, and Azure cloud engineer.

Build a production-minded web application that discovers trending Indian news, researches stories, sends notifications through Telegram, and provides a dashboard where I can select a story and generate a complete prompt for my separate Claude video-production agent.

You must implement the actual application, not merely describe an architecture or generate a collection of disconnected example files.

Inspect the existing repository and available development environment first. Reuse suitable existing code and preserve working functionality. Then implement the system incrementally, run tests, fix errors, and document how to run and deploy it.

If the repository is empty, initialize a suitable project structure.

## 2. Project Scope

This is Phase 1 of a larger YouTube automation project.

### Features to build now

1. Scheduled news monitoring every hour.
2. Indian news discovery and trend detection.
3. Identification of major global developments.
4. Research summaries with source links and timestamps.
5. Telegram notifications.
6. A web dashboard for reviewing news candidates.
7. A story-to-video prompt builder.
8. Persistent configuration, database storage, logs, and error handling.
9. Azure deployment configuration and documentation.

### Features explicitly outside Phase 1

Do not implement video rendering, image generation, voice generation, automated YouTube uploading, or a full video-production agent in this phase.

The prompt builder must prepare instructions for my separate Claude video-production workflow. I will copy the generated prompt and provide the relevant story images to that agent myself.

Do not build unnecessary microservices or introduce complex infrastructure without a clear need.

## 3. News Monitoring Requirements

The monitoring service must execute automatically every 60 minutes.

Use an Azure-compatible scheduled background job or scheduler with reliable execution and persistent state. Prevent overlapping runs and handle restarts safely.

Each monitoring run should:

1. Retrieve recent news from configured and permitted sources.
2. Collect available headlines, summaries, article URLs, publication times, publishers, and retrieval times.
3. Normalize and deduplicate the collected items.
4. Group articles discussing the same underlying event.
5. Identify potential trending stories.
6. Assess their importance and relevance.
7. Generate concise research summaries with supporting source links.
8. Save results to the database.
9. Notify me about new, relevant stories through Telegram.
10. Record the run status, errors, and execution time.

The scheduler must run in Azure independently of my personal computer. It must not depend on my browser being open.

A one-hour schedule is intentional. Do not silently change it to a five-minute or fifteen-minute schedule.

## 4. Geographic and Editorial Priorities

### Primary coverage: India

Prioritize Indian news, including:

- National developments.
- State and regional news.
- Government announcements and public policy.
- Science and technology.
- Business and economy.
- Education and employment.
- Environment and weather-related developments.
- Important court judgments.
- Major public-interest events.
- Other significant developments affecting Indian audiences.

Support both Hindi and English reporting about Indian events.

The user should be able to configure categories and source preferences through application settings.

### Secondary coverage: major global developments

Monitor global developments only to identify events significant enough to merit an informational alert.

Examples include major international conflicts, significant geopolitical developments, major disasters, important scientific breakthroughs, and global events with substantial potential implications for India.

A global story must generate a concise information alert, not automatically enter the video-production workflow.

After receiving a global alert, I will decide what to do next.

Do not automatically generate a global-news video prompt unless I explicitly choose that story and request it.

## 5. Source Collection and Research

Design a modular source-adapter system.

Support suitable sources such as:

- RSS and Atom feeds.
- Official government and public-information feeds.
- Licensed news APIs.
- Search APIs, if configured.
- Other accessible public sources where automated access is permitted.

Do not assume that every news website, YouTube channel, or social platform provides unrestricted access to its content.

Respect access controls, API terms, rate limits, robots directives where applicable, and copyright restrictions. Do not bypass logins, paywalls, or technical access restrictions.

Store source URLs and available metadata. Avoid copying complete copyrighted articles into the database when a short summary and source link are sufficient.

Every research summary must distinguish between:

- Confirmed facts.
- Claims attributed to named sources.
- Conflicting reports.
- Unverified information.
- Analysis and uncertainty.

Prefer primary sources and independent corroboration for important claims.

Never invent source URLs, publication dates, quotations, statistics, or evidence.

If the available sources do not establish a claim, say so.

## 6. Trend Detection and Story Ranking

Implement a configurable story-ranking system.

Consider the following factors:

- Freshness of the event.
- Publication frequency and growth in coverage.
- Independent source corroboration.
- Public importance.
- Relevance to Indian audiences.
- Availability of reliable evidence.
- Potential to explain the story clearly in a short video.

Use transparent, configurable scoring rather than presenting an unexplained AI-generated score as objective truth.

Do not count multiple websites repeating the same original report as independent confirmation.

Group duplicate articles under one story candidate and preserve the individual source records.

Detect stories that are already in the database so that the system does not send repetitive notifications on every hourly run.

Support configurable thresholds and alert suppression rules.

A trending score must not override basic reliability checks. A viral rumor must not automatically become a recommended video.

## 7. Telegram Notification System

Integrate with the official Telegram Bot API.

Use environment variables or Azure Key Vault for the bot token and other secrets. Never expose credentials in frontend code, logs, or committed configuration files.

Provide a setup guide covering:

1. Creating a Telegram bot through BotFather.
2. Configuring the bot token securely.
3. Obtaining the authorized chat ID.
4. Testing the connection.
5. Sending a test notification.
6. Troubleshooting delivery failures.

Only send notifications to authorized chat IDs configured by the administrator.

### Indian news notification

Each notification should contain:

- Headline.
- Short Hindi or English summary, depending on configuration.
- Why the story matters.
- Event time and publication time where available.
- Source names and clickable URLs.
- Confidence or evidence status.
- Why the story was selected.
- Suggested angle for a Hindi documentary.
- A link to the story in the web dashboard.

The dashboard must allow me to review the complete research before deciding whether to create a video.

### Major global-news notification

Each notification should contain:

- Headline.
- What happened.
- Why it matters.
- Relevance to India, where applicable.
- Reliable source links.
- Any important uncertainty.

Label this clearly as a global information alert.

Do not automatically start video production or send a ready-to-publish video prompt for global alerts.

### Notification reliability

Implement:

- Duplicate suppression.
- Retry handling for transient Telegram API failures.
- Delivery status tracking.
- Safe handling of rate limits.
- Logging without exposing secrets.

If notification delivery fails, retain the story in the dashboard.

## 8. Web Dashboard

Build a clean, responsive dashboard using Next.js, React, and TypeScript.

Use a Python FastAPI backend.

The dashboard should contain the following sections.

### A. Overview

Display:

- Latest monitoring run.
- Next scheduled run, if known.
- Number of new stories discovered.
- Indian news candidates.
- Major global alerts.
- Source retrieval errors.
- Telegram delivery status.

Do not display a successful status if the corresponding job failed.

### B. Indian News

Show a searchable and filterable list of story candidates.

Each story card should contain:

- Headline.
- Short summary.
- Category.
- Event and publication times where known.
- Number of unique reporting sources.
- Trend score and explanation.
- Verification status.
- Source links.
- Suggested video angle.
- Current editorial status.

Allow me to open a story to see the complete research and sources.

Provide actions to mark a story as:

- Interested.
- Selected for video.
- Rejected.
- Archived.

These actions should persist in the database.

Selecting a story must not automatically publish or generate a video.

### C. Global Alerts

Show major international developments separately from Indian video candidates.

Allow me to review, dismiss, archive, or explicitly select an alert for further research.

Selecting an alert for research must require a deliberate user action.

### D. Prompt Builder

Build a dedicated section for generating the prompt I will paste into Claude.

The form must contain:

1. Selected story.
2. Research summary.
3. Source URLs.
4. Important confirmed facts.
5. Unresolved claims and uncertainties.
6. Suggested storytelling angle.
7. Optional additional instructions.
8. Reference-image instructions.
9. Permanent channel rules.

Prepopulate the form with the selected story's saved research data.

Allow manual editing before generating the prompt.

Provide a prominent Copy Complete Prompt button.

Copy the complete prompt to the clipboard and display success or failure feedback.

Also provide a way to download or save the generated prompt as a Markdown file if practical.

The prompt must be self-contained enough to work when copied into another Claude session, while directing Claude to use the permanent channel files available in its own project environment.

Do not pretend that copying a prompt transfers image files automatically.

## 9. Permanent Channel Configuration

Create a persistent, editable Channel Bible.

Store its configuration in a versioned Markdown or structured configuration file, with appropriate database support if needed.

Initial rules:

- Channel language: Hindi.
- Primary news focus: India.
- Major global developments: information alerts only until I give further instructions.
- Typical video duration: under five minutes when the story can be explained accurately and clearly in that time.
- Storytelling style: cinematic documentary explainer.
- Visual style: consistent 2D anime-inspired illustrations.
- Anchor: original fictional male illustrated anchor.
- Voice: male Hindi narration.
- Permanent visual identity: reuse the approved anchor reference and newsroom design.
- Production: human approval at every major stage.
- Publishing: never publish without explicit authorization.

The Channel Bible should remain separate from individual story data.

The prompt builder should include the appropriate rules in every generated prompt.

The Channel Bible is configuration for the downstream video agent. Do not implement the video-production pipeline itself in this phase.

## 10. Story-to-Video Prompt Template

Create a reusable template file called `video_prompt_template.md`.

The prompt generated by the application should include:

### Story information
The selected headline, summary, relevant event dates, and context.

### Research evidence
Source links, confirmed facts, attributed allegations, conflicting reports, and unresolved questions.

### Video instructions
Create a cinematic, 2D illustrated Hindi documentary with a target duration under five minutes where practical.

Preserve accuracy and completeness. Do not add filler just to reach a target duration.

### Anchor and style
Use the permanent fictional male anchor, approved anchor reference image, and consistent newsroom environment.

### Visual planning
Generate a scene-by-scene storyboard, image prompts, camera movements, animation instructions, transitions, and narration.

Use story-specific illustrations. Do not present generated images as authentic news photographs or footage.

### Approval workflow
Require the following sequence:

1. Research review and approval.
2. Hindi script approval.
3. Storyboard and visual plan approval.
4. Final rendered video review.
5. Separate explicit authorization before any publishing.

The downstream agent must stop at each required approval gate.

### Deliverables
Final MP4, Hindi script, storyboard, image prompts, project assets, source notes, YouTube title, description, and thumbnail concept.

Do not claim that video assets have been generated or that a video has been rendered unless those operations actually occurred.

## 11. Global Information Alert Workflow

Implement this explicit rule in both backend logic and dashboard behavior:

When the monitoring service identifies a significant global development:

1. Save the story and its source links.
2. Send a concise Telegram information alert.
3. Mark it as awaiting user direction.
4. Do not automatically create a video prompt.
5. Wait for me to decide whether to request further research, select it for a video, or dismiss it.

Indian story candidates may be prepared for video selection, but they must still pass through the prompt builder and the separate approval process.

## 12. Suggested Technical Architecture

Use a modular monolith initially.

Recommended components:

- Frontend: Next.js, React, TypeScript.
- Backend: Python, FastAPI.
- Database: PostgreSQL.
- Data access: SQLAlchemy and Alembic migrations, or another consistent migration-supported approach.
- Scheduled processing: Azure-compatible scheduled jobs or a background worker.
- Notifications: Telegram Bot API.
- AI research and summarization: configurable provider interface.
- News ingestion: pluggable RSS, API, and permitted search adapters.
- Configuration: environment variables and Azure Key Vault.
- Logging: structured logs with run identifiers.
- Testing: unit tests and integration tests.

Choose a practical Azure deployment model, such as Azure Container Apps Jobs for hourly scheduled processing and an appropriate hosted service for the web application.

Avoid keeping a permanent polling loop alive solely to execute hourly jobs if a native scheduled job is more reliable and economical.

Use managed PostgreSQL if the budget supports it. Otherwise, clearly document a suitable development setup and its production limitations.

Provide Docker configuration for reproducible builds.

Keep API keys on the server side.

Use database migrations, typed request/response models, input validation, and secure error handling.

Do not add Redis, Kubernetes, multiple independent microservices, or other infrastructure unless the actual implementation requires them.

## 13. Database Design

Create appropriate tables or equivalent models for:

- News sources.
- Retrieved articles.
- Story clusters.
- Story candidates.
- Research summaries.
- Claims and evidence.
- Telegram notifications.
- Monitoring runs.
- User decisions.
- Channel configuration.
- Prompt templates.
- Generated prompt records.
- Audit and error records.

Use stable identifiers, timestamps, uniqueness constraints, and indexes.

Store UTC timestamps internally and display dates in the user's configured timezone.

Avoid storing full article content unnecessarily.

Prevent duplicate stories and duplicate notifications using persistent identifiers and suitable deduplication logic.

## 14. Scheduling and Reliability

The hourly monitoring schedule must be configurable, with a default interval of 60 minutes.

Requirements:

- No overlapping scheduled runs.
- Persistent monitoring status.
- Bounded retries.
- Timeouts for external requests.
- Graceful handling of API failures.
- Recovery after restarts.
- Deduplication across runs.
- Monitoring and health checks.
- A way to trigger a manual test run from an authorized dashboard action.

A failed source should not cause the entire monitoring run to fail if other sources remain available.

Record which sources succeeded, which failed, and why.

Never fabricate a successful monitoring result when no source data was retrieved.

## 15. Security and Privacy

Implement:

- Secure environment configuration.
- Secret management.
- Input validation.
- Protected administrative dashboard access.
- Restricted Telegram recipients.
- Safe handling of untrusted article content.
- Protection against prompt injection from retrieved webpages.
- Redaction of credentials from logs.
- Reasonable rate limiting and error handling.

Treat retrieved news articles and social posts as untrusted data. Instructions embedded in an article must never override the system's configuration or cause arbitrary tool execution.

Do not expose the database or administration endpoints publicly without appropriate authentication and network protections.

## 16. Cost Control

Build the initial application to minimize unnecessary spending.

Requirements:

- Use RSS and suitable free sources where practical.
- Make paid APIs optional and configurable.
- Avoid repeated summarization of unchanged stories.
- Cache results where appropriate.
- Track AI calls and estimated costs when supported.
- Allow spending limits and alert thresholds.
- Do not assume Azure credits or free tiers are available without checking the actual subscription.
- Document likely paid services and potential recurring costs.

Do not require a paid image-generation or video-generation API in Phase 1.

## 17. Testing Requirements

Implement tests for:

- Source parsing and normalization.
- Article deduplication.
- Story clustering.
- Trend ranking.
- Global versus Indian story classification.
- Notification deduplication.
- Telegram delivery failures.
- Scheduler locking.
- Database migrations.
- Prompt generation.
- Copyable prompt completeness.
- Configuration persistence.
- Authentication and authorization.
- Handling malicious instructions in retrieved content.

Include sample fixture data so tests do not depend on live news websites.

Provide an integration test for the main workflow using mock news sources and a mocked Telegram client.

Run the tests and fix failures before claiming the implementation is complete.

## 18. Development Workflow

Work in small, verifiable milestones.

### Milestone 1: Repository inspection and design
Inspect the existing codebase, report what exists, identify missing components, and establish the implementation plan.

### Milestone 2: Backend and database
Implement source models, story models, migrations, configuration, and basic API endpoints.

### Milestone 3: News ingestion
Implement source adapters, normalization, deduplication, story grouping, and initial ranking.

### Milestone 4: Research and notifications
Implement research summaries, global-news filtering, Telegram integration, and delivery tracking.

### Milestone 5: Dashboard
Implement the overview, Indian news list, global alerts, story detail pages, and editorial actions.

### Milestone 6: Prompt builder
Implement the permanent Channel Bible, reusable template, editable story form, complete prompt generation, clipboard copying, and Markdown export.

### Milestone 7: Reliability and testing
Add scheduling, retries, tests, security checks, logging, and operational documentation.

### Milestone 8: Azure deployment
Prepare the Docker images, deployment configuration, secret setup, database migrations, scheduled job, health checks, and deployment instructions.

After each milestone, run relevant tests and report what works, what remains, and any external credentials needed.

Do not claim Azure deployment succeeded unless the application has actually been deployed and verified.

## 19. Required Deliverables

Provide a working repository containing:

- Frontend application.
- FastAPI backend.
- Database models and migrations.
- News source adapters.
- Hourly scheduler.
- Trend detection and story grouping.
- Research summarization.
- Telegram notifications.
- Global alert handling.
- Channel Bible configuration.
- Prompt builder.
- Reusable video prompt template.
- Automated tests.
- Docker configuration.
- Azure deployment files.
- `.env.example` without real credentials.
- `.gitignore`.
- README with setup and deployment instructions.
- Operational troubleshooting guide.

The README must explain how to run locally, configure sources, connect Telegram, start the hourly schedule, test the system, deploy to Azure, and monitor costs.

## 20. Definition of Done

The project is complete when:

1. The application can retrieve news from at least one functioning configured source.
2. It groups duplicate articles and produces persistent story candidates.
3. It distinguishes Indian candidates from major global information alerts.
4. It sends Telegram messages to the authorized chat when configured.
5. It avoids repeatedly notifying about unchanged stories.
6. The dashboard displays research and source links.
7. I can select a story and edit its details.
8. The prompt builder produces a complete prompt using the permanent Channel Bible and template.
9. I can copy the prompt and paste it into my separate Claude video-production agent.
10. Hourly monitoring works independently of my computer when deployed.
11. Tests pass for the critical workflows.
12. Deployment and credential configuration are documented.
13. No video generation or publishing is triggered automatically.

## Final Instruction

Start by inspecting the repository and development environment.

Then implement the application rather than stopping after planning. Ask me only for information that is genuinely required to proceed, such as missing credentials or a deployment decision that cannot be safely inferred.

Use mock credentials and test fixtures during development. Never ask me to paste secrets into source files or commit real credentials.

Prioritize a reliable, usable first version over unnecessary complexity.