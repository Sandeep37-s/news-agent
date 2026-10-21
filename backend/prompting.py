"""Build one evidence snapshot for both downstream prompts, without stale editor copies."""
from datetime import datetime, timezone


FORMATS = {
    'auto': 'Choose the structure that best fits the evidence; explain the choice.',
    'explainer': 'Explain what happened, the essential background, why it matters and what remains unknown.',
    'timeline': 'Build a chronological account using verified event times; do not substitute publication dates for event dates.',
    'news_update': 'Lead with the latest supported development, explain what changed and retain essential context.',
}
ANIMATION = {
    'hybrid': 'Layered 2D cut-out illustrations plus motion graphics, with restrained anchor gestures and purposeful camera movement.',
    'motion_graphics': 'Prioritise readable maps, timelines, diagrams, charts and contextual illustrations; use character animation sparingly.',
    'anchor_led': 'Use the approved illustrated anchor to guide the explanation, intercut with evidence and story graphics; avoid a static talking head throughout.',
}
ANCHOR = {
    'balanced': 'Use the anchor for the introduction, difficult explanations and closing; roughly 15–25 percent of screen time when suitable.',
    'minimal': 'Use a brief anchor introduction and closing; let contextual illustrations and graphics carry the story.',
    'frequent': 'Return to the anchor between major story sections, with substantial contextual cutaways; do not keep the anchor visible throughout.',
}


def evidence_packet(story, articles, edit, max_age_hours):
    research = story.research or {}
    warnings = []
    if not edit['confirmed_facts'].strip():
        warnings.append('No facts have been marked confirmed by the editor. Verify the claims before writing a factual script.')
    if not articles:
        warnings.append('No collected source records are attached to this story.')
    elif all(not a.summary for a in articles):
        warnings.append('Headline discovery only: article text was not collected. Open the source links and research the important claims.')
    if articles and not any(a.event_at for a in articles):
        warnings.append('Event time is not established in the source metadata. Publication and retrieval times are not event times.')
    if not edit['sources'].strip():
        warnings.append('The editor source-links field is empty. Collected source records below remain available; verify sources for edited claims.')
    current = datetime.now(timezone.utc)
    dated = []
    for article in articles:
        if article.published_at:
            try:
                stamp = datetime.fromisoformat(article.published_at)
                if stamp.tzinfo:
                    dated.append(stamp)
            except ValueError:
                pass
    if dated and (current - max(dated)).total_seconds() > max_age_hours * 3600:
        warnings.append('Collected coverage is older than the discovery freshness window. Check for updates before calling this breaking or current news.')
    # Source records are stable within the pair; the editor's current text occurs once.
    evidence = [{
        'source_ref': f'S{index}', 'publisher': a.publisher, 'url': a.url,
        'headline': a.title, 'excerpt': a.summary or None,
        'evidence_type': 'attributed_feed_excerpt' if a.summary else 'headline_only',
        'published_at': a.published_at, 'event_at': a.event_at,
        'retrieved_at': a.retrieved_at, 'origin_group': a.origin_group,
    } for index, a in enumerate(articles, 1)]
    duration = edit['target_duration_seconds']
    production = {
        'target_duration_seconds': duration,
        'duration_rule': 'A target, not a reason to add filler or omit essential uncertainty. Final timing must follow the actual voice track.',
        'story_format': edit['story_format'], 'story_direction': FORMATS[edit['story_format']],
        'animation_style': edit['animation_style'], 'animation_direction': ANIMATION[edit['animation_style']],
        'anchor_presence': edit['anchor_presence'], 'anchor_direction': ANCHOR[edit['anchor_presence']],
        'delivery': 'Hindi, 1920x1080, 16:9, 30 fps unless the user explicitly changes the delivery specification.',
        'reference_status': 'Not verified by this studio. Check actual approved anchor/newsroom assets in the downstream session.',
    }
    return {
        'headline': story.title, 'region': story.region, 'category': story.category,
        'prepared_at': current.isoformat(),
        'editorial_review': {key: edit[key] for key in ('summary', 'confirmed_facts', 'uncertainties', 'sources', 'angle')},
        'evidence_status': research.get('evidence_status', 'Unverified'),
        'readiness': {'status': 'research_review_required', 'warnings': warnings,
                      'note': 'Automatic checks identify gaps; they do not verify a story or certify publication readiness.'},
        'source_metadata': evidence,
        'conflicting_reports': research.get('conflicting_reports', []),
        'unverified_information': research.get('unverified_information', []),
        'research_uncertainties': research.get('uncertainties', []),
        'box_office': research.get('box_office', []),
        'record_claims': research.get('record_claims', []),
        'production_preferences': production,
    }
