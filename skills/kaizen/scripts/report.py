"""Build a kaizen record's report.html from its item files and STATUS.md.

Usage: python report.py <record folder>
Writes <record folder>/report.html and prints its path and the count per verdict.
"""

import html
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

VERDICT_ORDER = ["do", "batch", "wait", "open", "drop"]
VERDICT_LABEL = {"do": "Do", "batch": "Batch", "wait": "Waiting", "open": "Not judged yet", "drop": "Dropped"}
SECTION_ORDER = ["Finding", "Probe", "Debate", "Record"]
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs"


def parse_item(path):
    text = path.read_text(encoding="utf-8")
    title, header, sections, current = path.stem, {}, {}, None
    for line in text.splitlines():
        if current is None and line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is None:
            m = re.match(r"^([A-Z][A-Za-z ]+):\s*(.*)$", line)
            if m:
                header[m.group(1).strip()] = m.group(2).strip()
        else:
            sections[current].append(line)
    sections = {k: "\n".join(v).strip() for k, v in sections.items()}
    verdict_text = header.get("Verdict", "") or field(sections.get("Debate", ""), "Verdict")
    verdict = (verdict_text.split() or ["open"])[0].lower().strip(":")
    if verdict not in VERDICT_LABEL:
        verdict = "open"
    debate = sections.get("Debate", "")
    return {
        "slug": path.stem,
        "title": title,
        "header": header,
        "sections": sections,
        "verdict": verdict,
        "verdict_text": verdict_text or "open",
        "close_call": field(debate, "Close call").lower().startswith("yes"),
        "improves": field(debate, "Improves") or field(debate, "Why"),
        "direction": "direction" in header.get("Lens", "").lower(),
    }


def field(text, name):
    m = re.search(r"^\s*(?:- )?(?:\*\*)?" + re.escape(name) + r"(?:\*\*)?:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def inline(text):
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)

    def link(m):
        href = html.unescape(m.group(2))
        if not re.match(r"^(https?:|t3-thread:|\.{0,2}/|[\w.-]+(/|\.md))", href):
            return m.group(0)
        return '<a href="%s">%s</a>' % (html.escape(href, quote=True), m.group(1))

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)


def markdown(text):
    """A small Markdown subset: fences, headings, bullets, tables and paragraphs."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            lang, body = line.strip()[3:].strip(), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(body))
            out.append('<pre class="mermaid">%s</pre>' % code if lang == "mermaid" else "<pre><code>%s</code></pre>" % code)
        elif line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")) + 2, 6)
            out.append("<h%d>%s</h%d>" % (level, inline(line.lstrip("#").strip()), level))
            i += 1
        elif line.lstrip().startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].lstrip().startswith(("- ", "* ")):
                items.append("<li>%s</li>" % inline(lines[i].lstrip()[2:]))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items))
        elif line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                head = "".join("<th>%s</th>" % inline(c) for c in rows[0])
                body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in rows[1:])
                out.append('<div class="table"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body))
        elif not line.strip():
            i += 1
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(("#", "- ", "* ", "|", "```")):
                para.append(lines[i].strip())
                i += 1
            out.append("<p>%s</p>" % "<br>".join(inline(p) for p in para))
    return "\n".join(out)


def split_mermaid(text):
    blocks = re.findall(r"```mermaid\n(.*?)```", text, re.S)
    return blocks, re.sub(r"```mermaid\n.*?```", "", text, flags=re.S)


def card(item):
    h = item["header"]
    badges = ['<span class="badge v-%s">%s</span>' % (item["verdict"], html.escape(item["verdict_text"]))]
    if item["close_call"]:
        badges.append('<span class="badge warn">close call</span>')
    for key in ("Status", "Lens"):
        if h.get(key):
            badges.append('<span class="badge">%s</span>' % html.escape(h[key]))
    diagrams, details = [], []
    for name in SECTION_ORDER + [s for s in item["sections"] if s not in SECTION_ORDER]:
        body = item["sections"].get(name, "")
        if not body:
            continue
        found, body = split_mermaid(body)
        diagrams += found
        details.append("<h4>%s</h4>%s" % (html.escape(name), markdown(body)))
    thread = h.get("Thread", "")
    parts = [
        '<article id="%s">' % html.escape(item["slug"], quote=True),
        "<h3>%s</h3>" % inline(item["title"]),
        '<div class="badges">%s<code class="slug">%s</code></div>' % ("".join(badges), html.escape(item["slug"])),
    ]
    if item["improves"]:
        parts.append('<p class="improves">%s</p>' % inline(item["improves"]))
    finding = item["sections"].get("Finding", "")
    facts = [(name, field(finding, name)) for name in ("Gain", "Cost and risk")]
    facts = [(n, v) for n, v in facts if v]
    if facts:
        parts.append('<p class="meta">%s</p>' % "<br>".join("%s: %s" % (n, inline(v)) for n, v in facts))
    if thread:
        parts.append('<p class="meta">Run: %s</p>' % inline(thread))
    if diagrams:
        parts.append('<div class="diagrams">%s</div>' % "".join('<pre class="mermaid">%s</pre>' % html.escape(d) for d in diagrams))
    if details:
        parts.append("<details><summary>Finding, probe, debate and record</summary>%s</details>" % "".join(details))
    parts.append("</article>")
    return "\n".join(parts)


def not_covered(folder):
    runs = [r for r in (folder / "runs").glob("*/reports") if r.is_dir()] if (folder / "runs").is_dir() else []
    if not runs:
        return []
    lines = []
    for report in sorted(max(runs, key=lambda r: r.stat().st_mtime).glob("*.md")):
        text = report.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^## Not covered\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        if m:
            for line in m.group(1).splitlines():
                if line.strip().startswith("- ") and line.strip()[2:].strip().lower() not in ("none", "nothing"):
                    lines.append("- %s (%s)" % (line.strip()[2:], report.stem))
    return lines


def status_sections(folder):
    path = folder / "STATUS.md"
    if not path.exists():
        return ""
    return markdown(re.sub(r"^# .*\n", "", path.read_text(encoding="utf-8"), count=1))


CSS = """
:root{--bg:#f7f6f3;--panel:#fff;--text:#1d1d1f;--muted:#6b6b70;--line:#e3e1dc;--accent:#3d5afe;
--do:#1b7f4b;--batch:#2463a8;--wait:#9a6700;--open:#6b6b70;--drop:#9b2c2c;--warn:#b54708;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141416;--panel:#1d1d21;--text:#ececef;
--muted:#9a9aa3;--line:#2e2e34;--accent:#8c9eff;--do:#4cc38a;--batch:#6aa8f0;--wait:#e0b44c;--open:#9a9aa3;
--drop:#f08a8a;--warn:#f0a35e;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141416;--panel:#1d1d21;--text:#ececef;--muted:#9a9aa3;--line:#2e2e34;--accent:#8c9eff;
--do:#4cc38a;--batch:#6aa8f0;--wait:#e0b44c;--open:#9a9aa3;--drop:#f08a8a;--warn:#f0a35e;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:960px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:40px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:16px;margin:0 0 8px}h4{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:16px 0 6px}
.sub,.meta{color:var(--muted)}.counts{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.count{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 14px}
.count b{font-size:20px;display:block}article{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:16px;margin:12px 0;overflow-wrap:anywhere}.badges{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
.badge{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:1px 9px;color:var(--muted)}
.v-do{color:var(--do);border-color:var(--do)}.v-batch{color:var(--batch);border-color:var(--batch)}
.v-wait{color:var(--wait);border-color:var(--wait)}.v-open{color:var(--open)}.v-drop{color:var(--drop);border-color:var(--drop)}
.warn{color:var(--warn);border-color:var(--warn)}.slug{font-size:12px;color:var(--muted)}.improves{margin:4px 0 8px}
.diagrams{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:12px 0}
.diagrams pre{margin:0;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;overflow-x:auto}
details summary{cursor:pointer;color:var(--accent);margin-top:8px}pre{overflow-x:auto;background:var(--bg);padding:8px;border-radius:6px}
code{font-size:13px}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}a{color:var(--accent)}
.theme{margin:20px 0 4px;font-size:14px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
"""


def build(folder):
    items = [parse_item(p) for p in sorted((folder / "items").glob("*.md"))] if (folder / "items").is_dir() else []
    counts = Counter(i["verdict"] for i in items)
    repo = folder.resolve().parent.parent.name if folder.resolve().parent.name == ".agents" else folder.resolve().name
    out = [
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        '<meta name=viewport content="width=device-width,initial-scale=1">',
        "<title>Kaizen: %s</title><style>%s</style></head><body><main>" % (html.escape(repo), CSS),
        "<h1>Kaizen: %s</h1>" % html.escape(repo),
        '<p class="sub">%d items. Built %s.</p>' % (len(items), datetime.now().strftime("%Y-%m-%d %H:%M")),
        '<div class="counts">%s</div>' % "".join(
            '<div class="count"><b>%d</b>%s</div>' % (counts[v], VERDICT_LABEL[v]) for v in VERDICT_ORDER if counts[v]),
    ]
    close = [i for i in items if i["close_call"]]
    if close:
        out.append("<h2>Close calls</h2><ul>%s</ul>" % "".join(
            '<li><a href="#%s">%s</a>: %s</li>' % (html.escape(i["slug"], quote=True), inline(i["title"]), html.escape(i["verdict_text"]))
            for i in close))
    def status(i):
        return (i["header"].get("Status", "").split() or [""])[0].lower()

    done = {"shipped", "dropped"}
    groups = [
        ("Shipped", lambda i: status(i) == "shipped"),
        ("In progress", lambda i: status(i) in ("launched", "blocked") and status(i) not in done),
        ("To do", lambda i: i["verdict"] in ("do", "batch") and not i["direction"] and status(i) not in done | {"launched", "blocked"}),
        ("Waiting", lambda i: i["verdict"] == "wait" and not i["direction"] and status(i) not in done | {"launched", "blocked"}),
        ("Not judged yet", lambda i: i["verdict"] == "open" and not i["direction"] and status(i) not in done),
        ("Direction", lambda i: i["direction"] and i["verdict"] != "drop" and status(i) not in done | {"launched", "blocked"}),
        ("Dropped", lambda i: status(i) != "shipped" and (i["verdict"] == "drop" or status(i) == "dropped")),
    ]
    for name, wanted in groups:
        chosen = [i for i in items if wanted(i)]
        if not chosen:
            continue
        out.append("<h2>%s</h2>" % name)
        by_theme = defaultdict(list)
        for i in chosen:
            by_theme[i["header"].get("Theme", "")].append(i)
        for theme in sorted(by_theme):
            if theme:
                out.append('<p class="theme">%s</p>' % html.escape(theme))
            out.extend(card(i) for i in by_theme[theme])
    gaps = not_covered(folder)
    if gaps:
        out.append("<h2>Not covered in the last pass</h2>%s" % markdown("\n".join(gaps)))
    status = status_sections(folder)
    if status:
        out.append("<h2>Board and passes</h2>%s" % status)
    out.append("</main><script type=module>import mermaid from '%s';" % MERMAID)
    out.append("const dark=matchMedia('(prefers-color-scheme: dark)').matches&&document.documentElement.dataset.theme!=='light'"
               "||document.documentElement.dataset.theme==='dark';"
               "mermaid.initialize({startOnLoad:false,theme:dark?'dark':'neutral',securityLevel:'strict'});"
               "mermaid.run({querySelector:'.diagrams .mermaid'});"
               "document.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)"
               "mermaid.run({nodes:d.querySelectorAll('pre.mermaid:not([data-processed])')})}));</script></body></html>")
    target = folder / "report.html"
    target.write_text("\n".join(out), encoding="utf-8")
    index = ["# Index", "", "| Item | Verdict | Status | Theme | Goal |", "|---|---|---|---|---|"]
    for i in items:
        cells = [i["slug"], i["verdict_text"], i["header"].get("Status", ""), i["header"].get("Theme", ""), i["title"]]
        index.append("| %s |" % " | ".join(c.replace("|", "/") for c in cells))
    (folder / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return target, counts


def main():
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        sys.exit("usage: python report.py <record folder>")
    target, counts = build(Path(sys.argv[1]))
    print(target.resolve())
    print(", ".join("%s %d" % (VERDICT_LABEL[v], counts[v]) for v in VERDICT_ORDER if counts[v]) or "no items")


if __name__ == "__main__":
    main()
