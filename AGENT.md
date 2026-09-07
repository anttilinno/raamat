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
- `README.md` — the index. Plain links to every chapter, because GitHub does
  not resolve `[[wikilinks]]`. Keep it in sync when chapters come and go.
- `.github/workflows/pages.yml` — renders the chapters with pandoc on push and
  publishes the result. No build artifact is committed.

## Rules

- Edit `.md` and push. There is no local build step.
- New chapter → link it in `README.md`, and add its filename to the chapter
  list in `.github/workflows/pages.yml`; files missing from that list are not
  published.
- Text is Estonian. Do not "fix" it into English, do not rewrite voice or
  register. Language corrections only when asked.

## Publish

    git commit -am 'update' && git push

A push to `main` renders and publishes the book via
`.github/workflows/pages.yml`.
