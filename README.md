# mdmap

See every Markdown file in a project on one page: read them rendered, and see which file links to which.

Built for projects where an AI agent (Claude Code, Codex…) keeps its rules and notes in many `.md` files (`CLAUDE.md`, `AGENTS.md`, `docs/…`). After a while nobody knows what is where. `mdmap` writes a single `md-map.html` you open in the browser.

- **Read:** files grouped by folder on the left, the selected file rendered in the middle, links *from* and *to* it on the right. Links between files work inside the page.
- **Map:** one coloured cluster per folder (a subfolder joins its parent's cluster when the parent has Markdown of its own: `product/reviews/` sits with `product/listing.md`, and its files point to it), arrows for links. Hover a file to light up its links, click to read it, scroll to zoom, drag to move.
- **What counts as a link:** relative Markdown links (`[x](docs/a.md)`), `[[wiki]]` links, links to a folder (its `README.md`), and paths written in backticks (`` `docs/a.md` ``, drawn dashed as a "mention").
- **Mentions (dashed):** also a path in plain text (`docs/x/`, `docs/x/config.json` → the Markdown of that folder; a small folder without README → its own `.md` files), a distinctive folder or file name written as a word (has a digit, `_` or `-`, at least 5 characters: `ornament5`, `report_2026-11-19`), and a file whose name starts with a folder name (`ornament1_review.md` → `ornament1/`).
- English or Turkish, following the browser language.

No install step beyond Python 3. The page loads [marked](https://marked.js.org) and [d3](https://d3js.org) from cdnjs. `md-map.html` is added to the repository's `.git/info/exclude`, so it never gets committed.

## Install as a Claude Code skill (`/mdmap`)

```bash
git clone https://github.com/mkilicer/mdmap ~/.claude/skills/mdmap
```

Then, in any project, type `/mdmap` (or ask "show me the md map"). Claude builds the page, opens it and gives you the link.

## Use from the terminal

```bash
git clone https://github.com/mkilicer/mdmap ~/mdmap
ln -s ~/mdmap/mdmap.py ~/.local/bin/mdmap   # any folder on your PATH
cd your-project && mdmap
```

Options: `mdmap <folder>` for another folder, `mdmap --no-open` to only write the file.

Skipped folders: `node_modules`, `vendor`, `.git`, `.next`, `dist`, `build`, `generated`, `pub`, `var`, `storage`, `wk`, virtualenvs and hidden folders (except `.claude`).

## Update

```bash
git -C ~/.claude/skills/mdmap pull
```

## License

MIT
