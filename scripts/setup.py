"""Create local-only secrets without putting them in command arguments or source."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parent.parent
path=root/'.env'
if not path.exists():
    value=(root/'.env.example').read_text()
    value=value.replace('ADMIN_PASSWORD=','ADMIN_PASSWORD='+secrets.token_urlsafe(20))
    value=value.replace('SESSION_SECRET=','SESSION_SECRET='+secrets.token_urlsafe(40))
    path.write_text(value,encoding='utf-8')
    print('Created private .env. Your generated administrator password is stored there.')
else:
    print('Existing .env retained.')
