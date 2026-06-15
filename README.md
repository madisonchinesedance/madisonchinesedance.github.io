# Madison Chinese Dance Academy Website

Static site for [madisonchinesedance.org](https://madisonchinesedance.org), served from the `docs/` folder on GitHub Pages and editable through [Pages CMS](https://pagescms.org).

## Editing content (volunteers)

1. Go to [pagescms.org](https://pagescms.org) and sign in with GitHub
2. Open the `madisonchinesedance/madisonchinesedance.github.io` repository
3. Edit pages, announcements, navigation, footer, or gallery settings
4. Save — changes go live on the next GitHub Pages deploy (usually within a minute)

No command line, npm, or JSON file editing required.

## How the site works

- **HTML shells** in `docs/pages/` and `docs/index.html`
- **Content** in `docs/content/*.json`
- **`docs/app.js`** loads JSON and renders the page in the browser
- **No build step** — push to `main` and GitHub Pages serves `docs/` directly

## Project structure

```
docs/
  app.js, style.css, index.html
  pages/              # HTML shells (one per route)
  content/            # JSON content (edited via Pages CMS)
    header.json       # Navigation
    footer.json
    announcements.json
    index.json        # Homepage
    gallery.json
    classes/, events/, get-involved/, splendid-china/
scripts/
  generate-ai-context.py   # Chatbot knowledge base
  scan-images.py           # Sync performance photos from Cloudflare R2
.pages.yml                 # Pages CMS field definitions
```

## Deployment

GitHub → **Settings** → **Pages** → Source: **Deploy from branch** → `main` → **`/docs`**

No GitHub Actions or npm required.

## Images (Cloudflare R2)

Performance photos live on R2 (`cdn.madisonchinesedance.org`). To sync from R2:

```bash
python scripts/scan-images.py sync
```

See `python scripts/scan-images.py --help` for homepage runner categorization.

## Chatbot

The MCDA Assistant uses a Cloudflare Worker. After content changes, regenerate context:

```bash
python scripts/generate-ai-context.py
```

Then deploy the worker with the updated `ai-context.md` if needed.

## Route registry

`docs/content/site.json` maps route IDs to pages. **Do not edit via Pages CMS** — it is maintained in the repo only. Adding a new page requires a new HTML shell, JSON file, and route entry.

## Legacy Eleventy migration

An experimental Eleventy + GitHub Actions setup was tried and reverted. It remains on branch `feature/pages-cms-11ty` in git history if you ever want to revisit pre-rendered HTML.
