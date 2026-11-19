#!/usr/bin/env python3
"""mdmap: turn the Markdown files of a project into one browsable HTML page.

Usage (in a project folder):
    mdmap            write ./md-map.html and open it in the browser
    mdmap <folder>   same, for another folder
    mdmap --no-open  write only

Left: files grouped by folder. Middle: the selected file, rendered.
Right: links from and to this file. "Map": which file links to which.
A link is a relative Markdown link ([x](docs/a.md)), a [[wiki]] link or a link to a folder (-> its README).
Dashed "mentions": a path in backticks or in plain text (`docs/a.md`, docs/x/, `docs/x/config.json` -> the
Markdown files of that folder; a folder without README -> its own .md files) and a distinctive folder or
file name written as a plain word (contains a digit, _ or -, >= 5 chars: "ornament5", "report_2026-11-19").
The output is added to .git/info/exclude so it never ends up in the repository.
No dependencies beyond Python 3; the page loads marked and d3 from cdnjs.
"""
import json, os, re, subprocess, sys, webbrowser
from pathlib import Path

SKIP = {"node_modules", "vendor", ".git", ".next", ".next-dev", "dist", "build", "generated",
        "pub", "var", ".venv", "venv", "__pycache__", ".cache", "storage", "wk"}
MD_LINK = re.compile(r"\]\(([^)\s#]+\.md)(#[^)]*)?\)")
WIKI = re.compile(r"\[\[([^\]|#]+)")
DIR_LINK = re.compile(r"\]\(([^)\s#:]+/)\)")            # [x](docs/)
CODE_PATH = re.compile(r"`([^`\s]+?(?:\.md|/))`")          # `../data.md`, `docs/<name>/`
CODE_FILE = re.compile(r"`([^`\s]+/[^`\s/]+\.[A-Za-z0-9]{1,5})`")  # `docs/x/config.json` -> the md files of docs/x
BARE_PATH = re.compile(r"(?<![\w/:.`\[(])((?:\.\.?/)?[\w.-]+(?:/[\w.<>-]+)+/?)(?![\w`])")  # data/research/ in prose
GENERIC = {"readme", "index", "listing", "claude", "agents", "skill", "notes", "todo", "changelog", "license"}


def collect(root: Path):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".") or d == ".claude"]
        for f in filenames:
            if f.lower().endswith(".md"):
                p = Path(dirpath) / f
                rel = p.relative_to(root).as_posix()
                try:
                    files[rel] = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass
    return files


def resolve(files, root_dirs, base, path):
    """Resolve a path to Markdown file(s): file -> itself; folder -> its README.md or the READMEs
    of its subfolders; <placeholder> -> every subfolder."""
    found = set()
    for start in (base, Path(".")):
        cand = os.path.normpath((start / path).as_posix()).replace(os.sep, "/")
        if "<" in cand:
            pre = cand.split("<")[0].rstrip("/")
            post = cand.split(">", 1)[1].strip("/") if ">" in cand else ""
            for d in sorted(root_dirs):
                if d.startswith(pre + "/") and d.count("/") == pre.count("/") + 1:
                    tgt = (d + "/" + post).rstrip("/")
                    found |= resolve(files, root_dirs, Path("."), tgt + ("" if tgt.endswith(".md") else "/"))
            if found:
                return found
            continue
        if cand.endswith(".md") and cand in files:
            return {cand}
        if cand in root_dirs or cand == ".":
            readme = next((f for f in files if f.lower() == (cand + "/readme.md").lower()), None)
            if readme:
                return {readme}
            subs = {f for f in files if re.fullmatch(re.escape(cand) + r"/[^/]+/readme\.md", f, re.I)}
            if subs:
                return subs
            own = {f for f in files if f.rsplit("/", 1)[0] == cand} if cand != "." else set()
            if 0 < len(own) <= 12:  # a small folder without README: its own Markdown files
                return own
    return found


def links(files):
    by_stem = {}
    for rel in files:
        by_stem.setdefault(Path(rel).stem.lower(), rel)
    out = {}
    for rel, text in files.items():
        base = Path(rel).parent
        targets = set()
        for m in MD_LINK.finditer(text):
            t = m.group(1)
            if t.startswith(("http://", "https://")):
                continue
            norm = os.path.normpath((base / t).as_posix()).replace(os.sep, "/")
            if norm in files and norm != rel:
                targets.add(norm)
        for m in WIKI.finditer(text):
            t = by_stem.get(m.group(1).strip().lower())
            if t and t != rel:
                targets.add(t)
        out[rel] = sorted(targets)
    return out


def mentions(files, strong):
    dirs = set()
    for f in files:
        parts = f.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    # distinctive names -> Markdown files: folder names (-> the md files inside) and file stems
    # (only names with a digit, _ or - and >= 5 chars, so ordinary words never match)
    names = {}
    for d in dirs:
        nm = d.rsplit("/", 1)[-1].lower()
        if len(nm) >= 5 and re.search(r"[\d_-]", nm) and nm not in GENERIC:
            names.setdefault(nm, set()).update(resolve(files, dirs, Path("."), d + "/"))
    for f in files:
        st = Path(f).stem.lower()
        if len(st) >= 5 and re.search(r"[\d_-]", st) and st not in GENERIC:
            names.setdefault(st, set()).add(f)
    names = {k: v for k, v in names.items() if v}
    out = {}
    for rel, text in files.items():
        base = Path(rel).parent
        got = set()
        for rx in (DIR_LINK, CODE_PATH):
            for m in rx.finditer(text):
                got |= resolve(files, dirs, base, m.group(1))
        for rx in (CODE_FILE, BARE_PATH):  # a file or folder path anywhere -> the Markdown in that folder
            for m in rx.finditer(text):
                t = m.group(1)
                if "://" in t or t.startswith("www.") or not re.search(r"[A-Za-z]", t.rstrip("/").rsplit("/", 1)[-1]):
                    continue
                if t.endswith(".md"):
                    got |= resolve(files, dirs, base, t)
                elif t.endswith("/"):
                    got |= resolve(files, dirs, base, t)
                else:
                    parent = t.rsplit("/", 1)[0] + "/"
                    got |= resolve(files, dirs, base, t + "/") or resolve(files, dirs, base, parent)
        low = text.lower()
        for name, tgts in names.items():  # a folder or file name written as a plain word
            if re.search(r"(?<![\w/.-])" + re.escape(name) + r"(?![\w-])", low):
                got |= tgts
        parent = rel.rsplit("/", 1)[0].rsplit("/", 1)[0] if rel.count("/") >= 2 else None
        own_parent = [f for f in files if parent and f.rsplit("/", 1)[0] == parent]
        siblings = sum(1 for f in files if f.rsplit("/", 1)[0] == rel.rsplit("/", 1)[0])
        if 0 < len(own_parent) <= 3 and siblings <= 12:  # reviews/x.md belongs to the Markdown of the folder above (its listing.md)
            got |= set(own_parent)
        stem = Path(rel).stem.lower()  # "ornament1_final_codex.md" belongs to the "ornament1" folder
        for name, tgts in names.items():
            if stem.startswith(name) and stem[len(name):len(name) + 1] in ("_", "-"):
                got |= tgts
        out[rel] = sorted(t for t in got if t != rel and t not in strong[rel])
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else ".").resolve()
    files = collect(root)
    graph = links(files)
    ment = mentions(files, graph)
    data = {"project": root.name, "files": files, "links": graph, "mentions": ment}
    html = (Path(__file__).resolve().parent / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    out = root / "md-map.html"
    out.write_text(html, encoding="utf-8")
    exclude = root / ".git" / "info" / "exclude"
    if exclude.parent.is_dir():
        cur = exclude.read_text() if exclude.exists() else ""
        if "md-map.html" not in cur:
            exclude.write_text(cur + ("" if cur.endswith("\n") or not cur else "\n") + "md-map.html\n")
    n_links = sum(len(v) for v in graph.values())
    n_m = sum(len(v) for v in ment.values())
    print(f"{out}  ·  {len(files)} Markdown files, {n_links} links + {n_m} mentions")
    if "--no-open" not in sys.argv:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
