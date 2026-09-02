# Raamat — Johann Taht

*Metsavenna ballaad kolmes vaatuses, ühe hobuse ja kolmeharulise porgandiga.*

Screenplay treatment, written in Markdown, served at
**<https://raamat.k3s.lan>** on the home cluster.

## Editing

Edit the `.md` files. They are plain Obsidian-flavoured Markdown — `[[wikilinks]]`
between the files resolve to in-page anchors, `> [!note]` becomes a callout box,
and a paragraph shaped like

    **SISE. RESTORAN — ÕHTU** · *beat: maailm*

is rendered as a screenplay slug line.

New file? Add its stem to `ORDER` in `build.py` (and optionally a short sidebar
label in `NAV`) — the build warns about any `.md` it finds that is not listed.

## Publishing

    ./build.py && git commit -am 'update' && git push
    kubectl -n book rollout restart deploy/book

`build.py` regenerates the single self-contained `index.html` (~28 KiB, no
external assets). The cluster pod clones this repo at start and serves that
file with busybox httpd, so the restart is what picks up a new commit.

Manifests live in `home-cluster/infrastructure/book/install/`.
