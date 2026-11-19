---
name: mdmap
description: Build a browsable HTML map of the project's Markdown files (rendered reading view + link graph by folder) and give the user the link. Use when the user types /mdmap or asks to see, map, browse or read the project's md files ("md haritası", "md'leri göster").
---

# mdmap

Generate the page and hand the user the link. Do not read or summarise the Markdown files yourself.

1. Run from the project root (the current working directory unless the user names another folder):

   ```bash
   python3 "<this skill's base directory>/mdmap.py" "<folder>" --no-open
   ```

   It prints one line: `<path>/md-map.html  ·  N Markdown files, X links + Y mentions`.
   If it fails, show the error line and stop.

2. Open it for the user: `open "<path>/md-map.html"` on macOS, `xdg-open` on Linux, `start` on Windows.

3. Reply in the user's language with the clickable path as a Markdown link (`[md-map.html](<absolute path>)`), the counts from step 1, and one line: re-run `/mdmap` after the Markdown files change. The file is added to `.git/info/exclude`, so it never gets committed.
