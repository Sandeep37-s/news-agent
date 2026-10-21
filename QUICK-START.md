# Open your Hindi News Studio

Project and saved parameters: **C:\Users\it\Documents\2d**

1. Open **http://localhost:3000** while the local application is running.
2. If needed, run `Start-Studio.ps1` in this folder.
3. Read your administrator password from the private `.env` file's `ADMIN_PASSWORD` entry. Do not share the file.
4. Review Indian news or Entertainment, open a story, and inspect its evidence.
5. Open **Prompt builder**, choose the story, and edit the brief. Click **Select for video & generate prompt**. If already selected, click **Generate complete prompt**. The generated brief appears automatically.
6. Use **Copy Complete Prompt** or **Download Markdown**. Attach your story images and permanent references separately in Claude.

The Windows hourly monitoring task is installed as `DrishtiHourlyDiscovery` and has run successfully. This still requires this computer to be available. Use Azure deployment for monitoring independent of your computer.

Settings and editorial decisions are saved in `data/studio.db`. Initial parameter files are in `config/`. Server secrets stay in `.env`. Full setup, Telegram instructions, Azure deployment, and troubleshooting are in `README.md` and `docs/`.

Verified: 27 automated tests pass, the production dashboard builds, live RSS retrieval works, and browser sign-in/research/prompt-form checks pass.

Connected sources: BBC India/World; NDTV India/Hindi/Movies; Hindustan Times India/Entertainment/Telugu Cinema. NDTV and HT connections collect headlines and links for private discovery, with publisher terms retained in Settings. No API key or paid connection was activated for these RSS feeds. They do not provide a commercial content licence. Important leads still need research before your own original script and approved publishing.

## Which token do I need?

**No API token is needed to generate or copy the Claude prompt.** The application combines your selected story's evidence, your edits, the Channel Bible, and the saved production template. Paste the result into your separate Claude project and attach images there.

Optional service credentials go in the private `C:\Users\it\Documents\2d\.env` file:

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_IDS`: only for Telegram notifications. The bot token comes from BotFather.
- `AI_API_KEY` and `AI_MODEL`: only for optional AI-written research summaries. Also configure the provider address and enable `ai_enabled` in monitoring settings.

Restart the studio after editing `.env`. Settings → Tokens & service connections shows whether each service is configured without displaying the secret values. Never paste tokens into story fields or a production prompt.

Remaining setup: your Telegram token/chat IDs; optional AI provider key/model; and Azure subscription/resources. Docker, managed PostgreSQL, Azure template compilation and actual deployment still need environment-specific verification. No video production or publishing runs automatically.

Stop the dashboard and API using `Stop-Studio.ps1`. The separate hourly task continues until disabled in Windows Task Scheduler.
