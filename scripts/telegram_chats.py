import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import httpx
from backend.config import env

if not env.telegram_bot_token:
    raise SystemExit('Set TELEGRAM_BOT_TOKEN in the private environment first.')
try:
    with httpx.Client(timeout=15,trust_env=False) as client:
        response=client.get('https://api.telegram.org/bot'+env.telegram_bot_token+'/getUpdates')
        data=response.json()
    if not data.get('ok'):
        raise SystemExit('Telegram rejected getUpdates. Check token and existing webhook configuration.')
    chats={}
    for update in data.get('result',[]):
        message=update.get('message',update.get('channel_post',{}))
        chat=message.get('chat',{})
        if chat.get('id'):
            chats[str(chat['id'])]=chat.get('type','unknown')
    if not chats: print('No chats found. Send a message to the bot, then try again.')
    for id,kind in chats.items(): print(f'{id}: {kind}')
except httpx.HTTPError:
    raise SystemExit('Telegram network request failed. No token or response content was logged.')
