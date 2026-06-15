# Madison Chinese Dance Academy Website

Static site for [madisonchinesedance.org](https://madisonchinesedance.org), built with [Eleventy](https://www.11ty.dev/) and editable through [Pages CMS](https://pagescms.org).

## Quick start (developers)

```bash
npm install
npm run build      # outputs to _site/
npm run serve      # local preview with live reload
```

## Editing content (volunteers)

1. Go to [pagescms.org](https://pagescms.org) and sign in with GitHub
2. Open this repository
3. Edit pages, announcements, navigation, or gallery images
4. Save — GitHub Actions rebuilds and deploys the site automatically

No command line or JSON editing required.

## Project structure

```
src/
  _data/              # Site settings (nav, footer, homepage, gallery, announcements)
  _includes/          # HTML layouts and partials
  assets/             # CSS, JavaScript, uploads
  content/pages/      # Markdown pages
  splendid-china/     # Annual performance archive (collection)
  index.md            # Homepage entry
scripts/
  migrate-content.py  # One-time JSON → Markdown migration (legacy)
  generate-ai-context.py
  scan-images.py      # Sync performance images from Cloudflare R2
.github/workflows/
  deploy.yml          # Build + deploy to GitHub Pages
.pages.yml            # Pages CMS configuration
```

## Deployment

The site deploys via **GitHub Actions** on push to `main` (and the feature branch during development).

**One-time setup after merge:**
1. GitHub → Settings → Pages → Source: **GitHub Actions**
2. Install the [Pages CMS GitHub App](https://github.com/marketplace/pages-cms) on the org repo
3. Invite editor accounts at pagescms.org

## Images (Cloudflare R2)

Performance photos live on R2 (`cdn.madisonchinesedance.org`). To sync from R2:

```bash
python scripts/scan-images.py sync
```

Homepage runner workflow is unchanged — see `scripts/scan-images.py --help`.

## Chatbot

The MCDA Assistant uses a Cloudflare Worker (`mcda-ai-bot`). After content changes, CI runs `generate-ai-context.py` to refresh `ai-context.md` for the worker.

## Legacy

The previous JSON + `docs/app.js` system is retired. Old content remains in git history under `docs/content/` until removed from this branch.
