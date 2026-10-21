# Run the studio on your laptop

Install **Git**, **Python 3.14**, and **Node.js 24 LTS**, then open PowerShell:

```powershell
git clone https://github.com/Sandeep37-s/news-agent.git
Set-Location news-agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe scripts/setup.py
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m backend.bootstrap
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.\Start-Studio.ps1
```

Open **http://localhost:3000**. Your newly generated administrator password is the `ADMIN_PASSWORD` entry in this laptop's private `.env` file. Keep it private. If PowerShell blocks the local launcher, you can use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Studio.ps1` for that process only, or follow the manual start commands in README.md.

The repository contains code, default parameters, news-feed definitions, channel rules, the production prompt template, tests and deployment files. It intentionally excludes passwords/tokens, the old computer's database, installed dependencies, logs and scratch files. The laptop starts with a fresh database. Run discovery to collect current headlines. News settings and editorial changes saved only in the old database do not transfer automatically.

Generating and copying a Claude prompt needs no API token. Telegram and optional AI research use credentials that you configure separately in this laptop's `.env`. Restart the studio after editing them. Do not upload `.env` or send its contents through chat.

To install hourly monitoring on this laptop:

```powershell
.\scripts\Install-HourlyTask.ps1
```

This local task requires the laptop to be running. Avoid running two monitors with the same Telegram recipient on separate databases unless you intentionally want duplicate alerts. The Azure deployment is prepared but has not been performed; see `docs/AZURE.md` for computer-independent operation.

For later code updates, stop the local dashboard/API first, run `git pull`, install changed dependencies, run migrations and rebuild the frontend before restarting. Back up the local database before migrations. Keep private `.env` settings on each machine; Git does not transfer them.
