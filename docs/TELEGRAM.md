# Telegram setup

1. Open the official **@BotFather** in Telegram and use `/newbot`. Keep the issued token private.
2. Put it in `TELEGRAM_BOT_TOKEN` in the ignored `.env` file, or in the Azure Key Vault `telegram-token` secret. Never put it in a source file, frontend setting, command argument, screenshot or shared log.
3. Send `/start` to your bot from the destination private chat. For a group, add the bot and give it permission to send messages.
4. Run `.\.venv\Scripts\python.exe scripts/telegram_chats.py` from the project root. It uses the token from the environment, calls the official `getUpdates` endpoint, and prints only candidate chat IDs and chat types. It does not select or authorize a recipient. If there are no updates, send the bot another message. An existing webhook can prevent polling; resolve that in your bot configuration rather than deleting it blindly.
5. Put the intended ID in `TELEGRAM_CHAT_IDS`. Separate multiple explicitly authorized destinations with commas. Restart the API and monitor processes after changing environment variables.
6. Open Settings → **Send test notification**. Confirm the message appears in the authorized chat and that the response says `sent`.
7. Run discovery. Stories must meet evidence and score thresholds before alerts are queued. Configuring a bot alone does not override the editorial checks.

## Delivery diagnosis

- `pending`: scheduled for retry, waiting for credentials, or waiting for the next hourly run.
- `sent`: Telegram acknowledged the message.
- `failed`: permanent API rejection or maximum attempts reached. Check revoked token, wrong ID, permissions or a blocked bot.
- `uncertain`: timeout, connection loss, or restart during sending. Inspect Telegram first. Queue a retry only if necessary; Telegram may already have delivered it.
- `suppressed`: recipient no longer authorized or story rejected/archived/dismissed.
- Rate limits: `retry_after` is respected as a minimum; the next hourly run may deliver later.

The [official Telegram Bot API](https://core.telegram.org/bots/api#sendmessage) defines message delivery fields. The application sends plain text with source URLs, without interpreting article markup.
