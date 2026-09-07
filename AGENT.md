# AGENT.md

Estonian screenplay treatment. Prose in Estonian, everything else in English.

## What this is

Screenplay for a parody action comedy with an Estonian undertone. A forest
brother ballad: deadpan seriousness in frame, the laugh happens in the audience,
never on screen.

Inspiration: A. Kivirähk "Ivan Orav" · Tujurikkuja · 1944 · Top Secret! · SISU ·
John Wick 1 · Malev · Pimp My Ride · Nähtamatu võitlus.

`Toon ja viited.md` is the canonical tone document — read it before touching any
chapter. Its John Wick key (koer → Kerese võidupartii, kutsikas → the
three-pronged carrot, mündid → porgandid, Continental → the stolen-vegetable
restaurant) is the load-bearing structure, not decoration.

## Layout

- `*.md` — the chapters. Obsidian-flavoured Markdown: `[[wikilinks]]`,
  `> [!note]` callouts, and slug lines shaped
  `**SISE. RESTORAN — ÕHTU** · *beat: maailm*`.
- `build.py` — hand-rolled Markdown subset → one self-contained `index.html`.
- `index.html` — generated, committed. Never edit by hand.

## Rules

- Edit `.md`, then run `./build.py`. Commit the regenerated `index.html` in the
  same commit as the source change.
- New chapter → add its stem to `ORDER` in `build.py`, optionally a short
  sidebar label in `NAV`. The build warns about any unlisted `.md`.
- Text is Estonian. Do not "fix" it into English, do not rewrite voice or
  register. Language corrections only when asked.
- `build.py` escapes before applying inline markup — keep that order, it is what
  stops source text injecting HTML.

## Publish

    ./build.py && git commit -am 'update' && git push
    kubectl -n book rollout restart deploy/book

Pod clones the repo at start, so the restart is what picks up the commit.
Manifests: `home-cluster/infrastructure/book/install/`.
