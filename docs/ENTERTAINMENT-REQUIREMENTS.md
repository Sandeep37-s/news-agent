## ADDITIONAL REQUIREMENT: BOLLYWOOD AND INDIAN ENTERTAINMENT NEWS

Extend the News Discovery Agent to cover Bollywood and the wider Indian entertainment industry as a first-class news category.

This category must be included in the hourly news monitoring workflow and Telegram notifications.

### 1. Entertainment Categories

Monitor the following topics:

**A. Upcoming Movies and Releases**
- Newly announced films.
- Official release dates.
- Upcoming theatrical and OTT releases.
- Release-date changes and postponements.
- Teaser, trailer, poster, and music releases.
- Major casting announcements.
- Official production announcements.

**B. Box-Office Performance**
- Opening-day collections.
- Opening-weekend collections.
- First-week and lifetime collections.
- Domestic and worldwide box-office figures.
- Opening records and reported box-office milestones.
- Budget and collection comparisons when reliable figures are available.
- Theatrical performance compared with documented expectations, where credible evidence exists.

**C. Record-Breaking Movies**
Identify credible reports of films setting records in categories such as:
- Highest opening day.
- Highest opening weekend.
- Highest opening for a particular actor or franchise.
- Highest domestic or worldwide gross within a clearly defined category.
- Fastest reported milestone, such as reaching a specified collection.
- Regional-language cinema records.
- Other officially documented industry milestones.

Never label a film as having broken a record without identifying the specific record, comparison category, relevant time period, and supporting evidence.

**D. Bollywood and Celebrity Developments**
- Major film announcements.
- Significant awards and achievements.
- Important interviews and public statements.
- Major professional collaborations.
- Verified controversies and legal developments with substantial public interest.
- Other significant developments involving actors, directors, producers, music composers, and film studios.

Avoid low-value celebrity gossip, unverified relationship rumors, fabricated controversies, and speculative claims about private lives.

**E. Wider Indian Cinema**
Do not restrict coverage to Hindi-language Bollywood films.

Include significant developments in Telugu, Tamil, Malayalam, Kannada, and other Indian film industries when they attract substantial attention, set notable records, or have wider cultural or commercial importance.

### 2. Entertainment Sources

Use available, permitted sources such as:
- Official film-production and studio announcements.
- Official movie and streaming-platform announcements.
- Reliable Indian entertainment publications.
- Interviews and original statements.
- Reputable box-office reporting services.
- Film trade analysts and industry publications.
- Official award and festival announcements.

Store the source URL, publication date, event date where known, publisher, and relevant claims.

For important box-office stories, seek more than one credible report when possible.

### 3. Box-Office Accuracy Rules

Box-office figures can differ between reporting sources.

For every important collection figure, record:
- The amount and currency.
- Whether it is domestic or worldwide.
- Whether it is gross collection, net collection, or another reported measure.
- The period covered.
- The date on which the figure was reported.
- The source and any disagreement with other estimates.

Do not mix domestic net collections with worldwide gross collections.

Do not compare collections from different currencies, territories, or reporting periods without explaining the differences.

Distinguish officially announced figures from trade estimates and media-reported estimates.

If figures conflict, display the difference and attribute the estimates to their sources instead of inventing a single definitive figure.

### 4. Entertainment Trend Detection

Identify entertainment stories that are gaining attention, including:
- A major trailer release.
- A film announcing an important release-date change.
- An unusually strong opening.
- A verified box-office milestone.
- A credible report of a new industry record.
- A significant announcement about a major upcoming film.

Group duplicate coverage of the same movie event into one story candidate.

Rank stories using freshness, public interest, source reliability, reporting growth, and storytelling potential.

Do not treat every film release or celebrity mention as breaking news.

### 5. Entertainment Telegram Notifications

Label these notifications clearly as ENTERTAINMENT NEWS.

Each notification should include:
- Headline.
- Movie or celebrity name.
- What happened.
- Release date or reporting period, if relevant.
- Verified or attributed box-office figures, if relevant.
- Why the story is attracting attention.
- Source links.
- A suggested Hindi documentary angle.
- A link to the full story in the dashboard.

Example notification:

ENTERTAINMENT NEWS: A film reaches a reported box-office milestone.

- Film: [Movie name]
- Milestone: [Specific collection or record]
- Reporting period: [Date or duration]
- Collection type: [Domestic net / domestic gross / worldwide gross]
- Sources: [Clickable source links]
- Important caveat: [Estimate, discrepancy, or confirmation status]
- Suggested video angle: How the film reached this milestone and what the numbers actually mean.

The example is a template, not a real news claim.

### 6. Entertainment Story-to-Video Prompt

When I select an entertainment story, the Prompt Builder must create a story-specific production prompt using the same permanent Channel Bible and fictional 2D anchor.

The prompt should include:
- A concise Hindi documentary narrative.
- The film's background and release information.
- A verified timeline of events.
- Relevant box-office data and its limitations.
- Comparisons with previous records only when supported by sources.
- A scene-by-scene storyboard.
- Prompts for cinematic 2D illustrations.
- Suggestions for posters, maps, charts, timelines, and box-office graphics.
- Source references for factual claims.
- Appropriate on-screen disclaimers for uncertain figures.

The video should generally be under five minutes when the story can be explained accurately within that duration.

Use a more engaging visual approach for entertainment stories while preserving the permanent channel identity.

Do not use copyrighted film clips, posters, photographs, music, or other assets unless their use is appropriately authorized or otherwise permitted. Prefer original illustrations and properly licensed material.

### 7. Dashboard Integration

Add Entertainment as a separate category in the dashboard alongside other Indian news categories.

Provide filters for:
- Upcoming releases.
- Box-office updates.
- Record-breaking films.
- Celebrity and industry news.
- Regional Indian cinema.

Allow me to select a story and send it to the existing Prompt Builder.

Do not build a separate video-production system for entertainment. Reuse the existing story research, approval, prompt-generation, and project-management workflows.

### 8. Acceptance Criteria

The feature is complete when:
1. Entertainment stories are collected during the hourly monitoring cycle.
2. Duplicate reports about the same film event are grouped.
3. Significant entertainment developments can trigger Telegram alerts.
4. Box-office figures preserve their collection type, period, source, and uncertainty.
5. The dashboard supports entertainment filtering.
6. Selected stories can be converted into the existing Claude video prompt.
7. The original Indian-news monitoring workflow continues to function.
8. No entertainment video is generated or published automatically.