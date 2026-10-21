# Open your Hindi News Studio

Project and saved parameters: **C:\Users\it\Documents\2d**

1. Open **http://localhost:3000** while the local application is running.
2. If needed, run `Start-Studio.ps1` in this folder.
3. Read your administrator password from the private `.env` file's `ADMIN_PASSWORD` entry. Do not share the file.
4. Review Indian news or Entertainment, open a story, and inspect its evidence.
5. Open **Prompt builder**, choose the story, and edit the story and reference-picture direction. Click **Select story & generate both prompts**. If already selected, click **Generate both prompts**.
6. Switch between **News-story prompt** and **Reference-picture prompt** to copy or download each. **Copy both prompts** and **Download both** provide the combined handoff to Claude. Attach actual story images and permanent references separately in Claude.

The Windows hourly monitoring task is installed as `DrishtiHourlyDiscovery` and has run successfully. This still requires this computer to be available. Use Azure deployment for monitoring independent of your computer.

Settings and editorial decisions are saved in `data/studio.db`. Initial parameter files are in `config/`. Server secrets stay in `.env`. Full setup, Telegram instructions, Azure deployment, and troubleshooting are in `README.md` and `docs/`.

Verified: 29 automated tests pass, the production dashboard builds, live RSS retrieval works, and browser checks confirm both prompt tabs and clipboard success.

Connected sources: BBC India/World; NDTV India/Hindi/Movies; Hindustan Times India/Entertainment/Telugu Cinema. NDTV and HT connections collect headlines and links for private discovery, with publisher terms retained in Settings. No API key or paid connection was activated for these RSS feeds. They do not provide a commercial content licence. Important leads still need research before your own original script and approved publishing.

## Which token do I need?

**No API token is needed to generate or copy either prompt.** The application combines your selected story's evidence, your edits, the Channel Bible, and two saved templates. It supplies text only. Your separate Claude video agent handles the video; attach actual images there.

Optional service credentials go in the private `C:\Users\it\Documents\2d\.env` file:

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_IDS`: only for Telegram notifications. The bot token comes from BotFather.
- `AI_API_KEY` and `AI_MODEL`: only for optional AI-written research summaries. Also configure the provider address and enable `ai_enabled` in monitoring settings.

Restart the studio after editing `.env`. Settings → Tokens & service connections shows whether each service is configured without displaying the secret values. Never paste tokens into story fields or a production prompt.

Remaining setup: your Telegram token/chat IDs; optional AI provider key/model; and Azure subscription/resources. Docker, managed PostgreSQL, Azure template compilation and actual deployment still need environment-specific verification. No video production or publishing runs automatically.

Stop the dashboard and API using `Stop-Studio.ps1`. The separate hourly task continues until disabled in Windows Task Scheduler.
