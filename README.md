# Raamat — Johann Taht

*Metsavenna ballaad kolmes vaatuses, ühe hobuse ja kolmeharulise porgandiga.*

Screenplay treatment, written in Markdown, served at
**<https://anttilinno.github.io/raamat/>**.

## Editing

Edit the `.md` files. They are plain Obsidian-flavoured Markdown — `[[wikilinks]]`
between the files resolve to in-page anchors, `> [!note]` becomes a callout box,
and a paragraph shaped like

    **SISE. RESTORAN — ÕHTU** · *beat: maailm*

is rendered as a screenplay slug line.

New file? Add its filename to the chapter list in
`.github/workflows/pages.yml` — files that are not listed are not published.

## Publishing

    git commit -am 'update' && git push

A push to `main` renders the chapters with pandoc into one self-contained
`index.html` and deploys it to GitHub Pages — see
`.github/workflows/pages.yml`. Nothing is built or committed locally.
