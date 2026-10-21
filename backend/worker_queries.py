"""Bound worker memory and round trips while retaining freshness checks for all stories."""
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import load_only
from .db import Story,Article

BATCH_SIZE=200


def research_batches(db,story_ids):
    ordered=sorted(story_ids)
    for offset in range(0,len(ordered),BATCH_SIZE):
        ids=ordered[offset:offset+BATCH_SIZE]
        stories=list(db.scalars(select(Story).where(Story.id.in_(ids))))
        grouped=defaultdict(list)
        for article in db.scalars(select(Article).where(Article.story_id.in_(ids)).order_by(Article.retrieved_at.desc(),Article.id)):
            grouped[article.story_id].append(article)
        yield stories,grouped


def ranking_batches(db):
    last_id=None
    while True:
        query=select(Story).options(load_only(Story.id,Story.title,Story.region,Story.category,Story.subcategory,Story.status,Story.score,Story.scoring)).order_by(Story.id).limit(BATCH_SIZE)
        if last_id is not None:
            query=query.where(Story.id>last_id)
        stories=list(db.scalars(query))
        if not stories:
            break
        last_id=stories[-1].id
        grouped=defaultdict(list)
        articles=db.scalars(select(Article).options(load_only(Article.story_id,Article.source_id,Article.publisher,Article.origin_group,Article.published_at,Article.retrieved_at)).where(Article.story_id.in_([story.id for story in stories])).order_by(Article.id))
        for article in articles:
            grouped[article.story_id].append(article)
        yield stories,grouped
