#!/usr/bin/env python3
"""Render the Johann Taht screenplay into one self-contained index.html.

Sources are the *.md files next to this script. Run it after editing them:

    ./build.py && git commit -am 'update' && git push

The cluster serves the committed index.html (see the deploy section of
README.md); nothing is rendered server-side.

ponytail: hand-rolled Markdown subset instead of pandoc/mdBook. The input is
a handful of files using a known set of constructs (headings, blockquotes
with Obsidian [!note] callouts, tables, task lists, [[wikilinks]]) and the
output needs screenplay-specific styling - slug lines, beats, attributed
dialogue - that a generic converter flattens into <p><strong>. If the source
ever grows real Markdown (nested lists, footnotes, images), swap in `pandoc`
and keep the CSS.
"""

import argparse
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE
OUT = HERE / "index.html"

# Reading order. Names are file stems in SRC (without .md).
ORDER = [
    "Johann Taht",
    "Vaatus I - Taht süttib",
    "Vaatus II - Blingimine ja varustamine",
    "Vaatus III - Peipsi arveteklaarimine",
    "Tegelased",
    "Toon ja viited",
    "Johann_Taht_Notes",
]

# Short labels for the sidebar; falls back to the document's own H1.
NAV = {
    "Johann Taht": "Avaleht",
    "Vaatus I - Taht süttib": "I — Taht süttib",
    "Vaatus II - Blingimine ja varustamine": "II — Blingimine",
    "Vaatus III - Peipsi arveteklaarimine": "III — Peipsi",
    "Johann_Taht_Notes": "Toormärkmed",
}


def slugify(text):
    text = text.lower()
    for a, b in (("ä", "a"), ("ö", "o"), ("õ", "o"), ("ü", "u"), ("š", "s"), ("ž", "z")):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# --- inline ------------------------------------------------------------------

def inline(text, doc_ids):
    """Escape, then apply the inline Markdown subset. Order matters: escaping
    first means no user text can inject markup."""
    out = html.escape(text, quote=False)

    def wikilink(m):
        target, label = m.group(1), m.group(2) or m.group(1)
        anchor = doc_ids.get(target)
        if anchor:
            return f'<a href="#{anchor}">{label}</a>'
        return f'<span class="deadlink">{label}</span>'

    out = re.sub(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", wikilink, out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", out)
    out = re.sub(r"(?<!\")(https?://[^\s<]+)", r'<a href="\1">\1</a>', out)
    return out


# --- block parsing -----------------------------------------------------------

SLUG_RE = re.compile(r"^\*\*(.+?)\*\*(?:\s*·\s*\*beat:\s*(.+?)\*)?\s*$")
SCENE_RE = re.compile(r"^(\d+)\.\s+(.*)$")
CALLOUT_RE = re.compile(r"^\[!(\w+)\]\s*(.*)$")


def strip_frontmatter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:]
    return lines


def render_table(rows, doc_ids):
    def cells(row):
        return [c.strip() for c in row.strip().strip("|").split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]  # rows[1] is the |---|---| separator
    out = ["<table><thead><tr>"]
    out += [f"<th>{inline(c, doc_ids)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline(c, doc_ids)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_quote(lines, doc_ids):
    """A blockquote. Three shapes: an Obsidian [!note] callout, dialogue with a
    trailing *— attribution* line, or a plain pull quote."""
    body = [l[2:] if l.startswith("> ") else l[1:] for l in lines]
    body = [l.rstrip() for l in body]

    callout = CALLOUT_RE.match(body[0]) if body else None
    if callout:
        title = callout.group(2) or callout.group(1).title()
        rest = [l for l in body[1:] if l.strip()]
        inner = "".join(f"<p>{inline(l, doc_ids)}</p>" for l in rest)
        return (
            f'<aside class="callout"><p class="callout-title">{html.escape(title)}</p>{inner}</aside>'
        )

    attrib = None
    while body and not body[-1].strip():
        body.pop()
    if body and body[-1].startswith("*—") and body[-1].endswith("*"):
        attrib = body.pop()[1:-1]
        while body and not body[-1].strip():
            body.pop()

    lines_html = "".join(
        f'<span class="line">{inline(l, doc_ids)}</span>' if l.strip() else ""
        for l in body
    )
    out = f'<blockquote class="dialogue">{lines_html}'
    if attrib:
        out += f'<footer>{inline(attrib, doc_ids)}</footer>'
    return out + "</blockquote>"


def render_doc(stem, text, doc_ids):
    lines = strip_frontmatter(text.splitlines())
    doc_id = doc_ids[stem]
    out = [f'<section class="doc" id="{doc_id}">']
    toc = []  # (anchor, label, is_scene)

    i, n = 0, len(lines)
    para = []

    def flush_para():
        if not para:
            return
        text = " ".join(para)
        m = SLUG_RE.match(text)
        if m and (m.group(2) or "." in m.group(1)):
            beat = f'<span class="beat">{inline(m.group(2), doc_ids)}</span>' if m.group(2) else ""
            out.append(f'<p class="slug">{inline(m.group(1), doc_ids)}{beat}</p>')
        elif text.startswith("→ "):
            out.append(f'<p class="next">{inline(text[2:], doc_ids)}</p>')
        else:
            out.append(f"<p>{inline(text, doc_ids)}</p>")
        para.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped.startswith("#"):
            flush_para()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            if level == 1:
                out.append(f'<h1>{inline(title, doc_ids)}</h1>')
            else:
                scene = SCENE_RE.match(title)
                anchor = f"{doc_id}-{slugify(title)}"
                if scene:
                    out.append(
                        f'<h2 id="{anchor}" class="scene">'
                        f'<span class="num">{scene.group(1)}</span>'
                        f'{inline(scene.group(2), doc_ids)}</h2>'
                    )
                else:
                    out.append(f'<h{level} id="{anchor}">{inline(title, doc_ids)}</h{level}>')
                toc.append((anchor, title, bool(scene)))
            i += 1
            continue

        if stripped == "---":
            flush_para()
            out.append('<hr>')
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(lines[i].strip())
                i += 1
            out.append(render_quote(block, doc_ids))
            continue

        if stripped.startswith("|"):
            flush_para()
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            out.append(render_table(block, doc_ids))
            continue

        if stripped.startswith(("- ", "* ")):
            flush_para()
            items = []
            while i < n and lines[i].strip().startswith(("- ", "* ")):
                item = lines[i].strip()[2:]
                i += 1
                # Indented continuation lines belong to the item above, not to a
                # new paragraph. The raw notes file leans on this heavily.
                while i < n and lines[i][:1].isspace() and lines[i].strip() \
                        and not lines[i].strip().startswith(("- ", "* ")):
                    item += " " + lines[i].strip()
                    i += 1
                task = item.startswith("[ ] ") or item.startswith("[x] ")
                if task:
                    done = item.startswith("[x]")
                    mark = "✓" if done else "○"
                    cls = "task done" if done else "task"
                    items.append(
                        f'<li class="{cls}"><span class="box">{mark}</span>'
                        f'{inline(item[4:], doc_ids)}</li>'
                    )
                else:
                    items.append(f"<li>{inline(item, doc_ids)}</li>")
            cls = ' class="tasks"' if 'class="task' in items[0] else ""
            out.append(f"<ul{cls}>" + "".join(items) + "</ul>")
            continue

        para.append(stripped)
        i += 1

    flush_para()
    out.append("</section>")
    return "".join(out), toc


CSS = """
:root{
  --paper:#f4f1ea; --ink:#1c1a17; --muted:#6b6459; --rule:#d8d2c6;
  --accent:#b4521e; --quote:#efe9dd; --shadow:rgba(28,26,23,.08);
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#16151a; --ink:#e6e1d8; --muted:#918a7d; --rule:#312e35;
    --accent:#e07a3c; --quote:#1e1c23; --shadow:rgba(0,0,0,.4);
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.65 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  -webkit-font-smoothing:antialiased}
.wrap{display:grid;grid-template-columns:250px minmax(0,1fr);gap:0;
  max-width:1180px;margin:0 auto}

/* nav */
nav{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;
  padding:2.4rem 1.4rem 3rem;border-right:1px solid var(--rule);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:13px}
nav .brand{font-family:inherit;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;font-size:11px;color:var(--accent);margin:0 0 1.6rem}
nav ol{list-style:none;margin:0 0 1.4rem;padding:0}
nav .top{display:block;padding:.3rem 0;color:var(--ink);text-decoration:none;
  font-weight:600;letter-spacing:.01em}
nav .top:hover{color:var(--accent)}
nav .sub{list-style:none;margin:.15rem 0 .9rem;padding:0 0 0 .1rem;
  border-left:1px solid var(--rule)}
nav .sub a{display:block;padding:.18rem 0 .18rem .7rem;color:var(--muted);
  text-decoration:none;font-size:12.5px}
nav .sub a:hover{color:var(--accent)}
nav .sub .n{display:inline-block;min-width:1.15em;color:var(--accent);
  font-variant-numeric:tabular-nums}

/* page */
main{padding:2.4rem 3rem 8rem;max-width:44rem}
.doc{padding-bottom:3rem}
.doc + .doc{border-top:1px solid var(--rule);padding-top:3rem}
h1{font-size:2.1rem;line-height:1.15;margin:0 0 1.6rem;letter-spacing:-.015em}
h2{font-size:1.28rem;margin:2.6rem 0 .9rem;line-height:1.25;letter-spacing:-.01em}
h3{font-size:1.05rem;margin:2rem 0 .6rem}
h2.scene{display:flex;gap:.7rem;align-items:baseline;
  padding-top:.9rem;border-top:1px solid var(--rule)}
h2.scene .num{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.72rem;
  font-weight:700;letter-spacing:.1em;color:var(--accent);
  border:1px solid var(--accent);border-radius:2px;padding:.12rem .42rem;
  line-height:1.4;flex:none;transform:translateY(-.15em)}
p{margin:0 0 1.05rem}
a{color:var(--accent);text-underline-offset:2px}
.deadlink{color:var(--muted)}
hr{border:0;height:1px;background:var(--rule);margin:2.4rem 0}
code{font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
  background:var(--quote);padding:.1em .35em;border-radius:3px}

/* slug line */
p.slug{font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;
  font-size:.76rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:var(--muted);margin:0 0 1.1rem;display:flex;flex-wrap:wrap;
  gap:.5rem .9rem;align-items:baseline}
p.slug .beat{font-weight:600;letter-spacing:.08em;color:var(--accent);
  text-transform:none;font-style:italic}
p.slug .beat::before{content:"beat: "}

/* quotes */
blockquote.dialogue{margin:1.6rem 0;padding:1rem 0 1rem 1.3rem;
  border-left:2px solid var(--accent);background:var(--quote);
  padding-right:1.1rem;border-radius:0 3px 3px 0}
blockquote.dialogue .line{display:block;margin:0 0 .35rem}
blockquote.dialogue footer{margin-top:.7rem;font-size:.82rem;color:var(--muted);
  font-style:italic}
aside.callout{margin:1.6rem 0;padding:.95rem 1.15rem;border-radius:4px;
  background:var(--quote);border:1px solid var(--rule);
  box-shadow:0 1px 2px var(--shadow)}
aside.callout .callout-title{font-family:ui-sans-serif,system-ui,sans-serif;
  font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:var(--accent);margin:0 0 .45rem}
aside.callout p:last-child{margin-bottom:0}
aside.callout p{font-size:.94rem}

/* lists + tables */
ul{margin:0 0 1.1rem;padding-left:1.2rem}
li{margin:0 0 .4rem}
ul.tasks{list-style:none;padding-left:0}
ul.tasks li{display:flex;gap:.6rem;align-items:baseline}
ul.tasks .box{color:var(--accent);flex:none;font-size:.85em}
ul.tasks .done{color:var(--muted);text-decoration:line-through}
.tablewrap{overflow-x:auto;margin:0 0 1.4rem}
table{border-collapse:collapse;width:100%;font-size:.92rem;margin:0 0 1.4rem}
th,td{text-align:left;padding:.5rem .8rem .5rem 0;border-bottom:1px solid var(--rule);
  vertical-align:top}
th{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.68rem;font-weight:700;
  letter-spacing:.11em;text-transform:uppercase;color:var(--muted)}

p.next{margin-top:2.4rem;font-family:ui-sans-serif,system-ui,sans-serif;
  font-size:.85rem;font-weight:600}
p.next::before{content:"→ ";color:var(--accent)}

@media (max-width:820px){
  .wrap{grid-template-columns:1fr}
  nav{position:static;height:auto;border-right:0;border-bottom:1px solid var(--rule);
    padding:1.6rem 1.4rem}
  main{padding:2rem 1.4rem 5rem}
}
"""


def build():
    docs = {}
    for stem in ORDER:
        path = SRC / f"{stem}.md"
        if not path.exists():
            sys.exit(f"missing source file: {path}")
        docs[stem] = path.read_text(encoding="utf-8")

    # README is repo documentation, not a chapter.
    extra = sorted(
        p.stem for p in SRC.glob("*.md") if p.stem not in ORDER and p.stem != "README"
    )
    if extra:
        print(f"warning: not in ORDER, skipped: {', '.join(extra)}", file=sys.stderr)

    doc_ids = {stem: slugify(stem) for stem in ORDER}

    body, nav = [], []
    for stem in ORDER:
        rendered, toc = render_doc(stem, docs[stem], doc_ids)
        body.append(rendered)
        label = NAV.get(stem, stem)
        subs = "".join(
            f'<li><a href="#{a}">'
            + (
                f'<span class="n">{SCENE_RE.match(t).group(1)}</span>{html.escape(SCENE_RE.match(t).group(2))}'
                if scene else html.escape(t)
            )
            + "</a></li>"
            for a, t, scene in toc
        )
        nav.append(
            f'<li><a class="top" href="#{doc_ids[stem]}">{html.escape(label)}</a>'
            + (f'<ul class="sub">{subs}</ul>' if subs else "")
            + "</li>"
        )

    return (
        "<!doctype html>\n"
        '<html lang="et"><head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>Johann Taht — metsavenna ballaad kolmes vaatuses</title>\n"
        '<meta name="color-scheme" content="light dark">\n'
        f"<style>{CSS}</style>\n"
        "</head><body>\n"
        '<div class="wrap">\n'
        '<nav><p class="brand">Johann Taht</p><ol>' + "".join(nav) + "</ol></nav>\n"
        "<main>" + "".join(body) + "</main>\n"
        "</div></body></html>\n"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--out", type=Path, default=OUT, help="output file")
    args = ap.parse_args()

    page = build()
    args.out.write_text(page, encoding="utf-8")
    print(f"{args.out} ({len(page.encode()) // 1024} KiB)")


if __name__ == "__main__":
    main()
