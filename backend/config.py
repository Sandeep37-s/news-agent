from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent

class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str = 'sqlite:///./data/studio.db'
    admin_password: str = ''
    session_secret: str = ''
    cookie_secure: bool = False
    telegram_bot_token: str = ''
    telegram_chat_ids: str = ''
    dashboard_url: str = 'http://localhost:3000'
    ai_base_url: str = 'https://api.openai.com/v1'
    ai_api_key: str = ''
    ai_model: str = ''

env = Environment()
(ROOT / 'data').mkdir(exist_ok=True)
