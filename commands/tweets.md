---
description: Pull Twitter/X posts (search, @handle timeline, or tweet URLs) via Agent Reach
argument-hint: "<search query | @handle | tweet URLs>"
---
Fetch Twitter/X content for: $ARGUMENTS

1. Run `agent-reach doctor` and check whether TWITTER_AUTH_TOKEN and TWITTER_CT0 are set.
2. With cookies: use `twitter search "<q>" -n 20 --json`, `twitter user-posts @handle -n 30 --json`,
   or `twitter tweet <url> --json` as appropriate (see the agent-reach skill, social reference).
3. Without cookies, or if search fails: for tweet URLs use the no-login syndication endpoint
   documented in the magazine-report skill's `references/sourcing.md`; for search fall back to Exa
   (`site:x.com <query>`), then read the found tweet URLs via syndication.
4. Present: author, @handle, date, verbatim text, likes, link — most relevant first — and say
   which method was used. If a report is in progress, save to its `sources/` folder.
Keep requests few and spaced; never scrape followers.
