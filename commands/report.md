---
description: Build a magazine-style report (PDF) from websites, Google Drive and Twitter/X
argument-hint: "<topic or title> [report URLs] [Drive folder/file names] [@handles or tweet URLs]"
---
Use the `magazine-report` skill to produce a full issue for: $ARGUMENTS

Run all four phases (GATHER → BRIEF → DESIGN → RENDER). Treat every URL, Drive name, @handle
and tweet link in the arguments as a source to fetch. If the arguments only give a topic,
discover sources yourself (Exa / web search for recent reports, Drive search for internal
files, Twitter for practitioner voices). Check `design-references/` before designing.
Finish with the PDF path, the empty-slot table, and any sources that failed.
