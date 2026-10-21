import json
from sqlalchemy import select
from .config import ROOT
from .db import Session, Source, Setting

def bootstrap():
    with Session() as db:
        if not db.get(Setting, 'monitoring'):
            db.add(Setting(key='monitoring', value=json.loads((ROOT/'config/settings.json').read_text())))
        for key, filename in [('channel','channel_bible.md'),('template','video_prompt_template.md'),('picture_template','reference_picture_prompt_template.md')]:
            if not db.get(Setting,key):
                db.add(Setting(key=key,value={'markdown':(ROOT/'config'/filename).read_text(encoding='utf-8')}))
        if not db.get(Setting, 'sources_initialized'):
            for data in json.loads((ROOT/'config/sources.json').read_text(encoding='utf-8')):
                if not db.scalar(select(Source).where(Source.url==data['url'])):
                    db.add(Source(**data))
            db.add(Setting(key='sources_initialized',value={'done':True}))
        db.commit()

if __name__ == '__main__':
    bootstrap()
