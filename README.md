# Madison Chinese Dance – Project Documentation

Welcome to the **Madison Chinese Dance** website repository. This project hosts the static site for the Madison Chinese Dance community, providing information about programs, events, performances, and ways to get involved.

## Table of Contents
- [About the Project](#about-the-project)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Scripts & Utilities](#scripts--utilities)
- [Managing Pages](#managing-pages)
- [Content Authoring](#content-authoring)
- [Updating Performance Images](#updating-performance-images)
- [Customizing Styles](#customizing-styles)
- [Notes & Tips](#notes--tips)
- [Contact](#contact)

## About the Project
The site is a lightweight, JSON-driven static website built with plain HTML, CSS, and a small amount of JavaScript (`app.js`). Content for each page lives in `docs/content/` as JSON files. Routes and navigation are managed by `docs/content/site.json` and `docs/content/header.json`, and can be regenerated from the filesystem with `scan-pages.py`.

## Getting Started
1. **Clone the repository**
   ```bash
   git clone https://github.com/madisonchinesedance/madisonchinesedance.github.io.git
   cd madisonchinesedance.github.io
   ```

2. **Run a local server** (serve from the `docs/` folder — it is the site root):
   ```bash
   cd docs && python -m http.server 8000
   ```
   Then open http://localhost:8000 in your browser.

3. **Development**
   - Edit JSON files under `docs/content/` to update page content.
   - Modify HTML templates in `docs/pages/` if you need structural changes.
   - Adjust styling in `docs/style.css`.

## Project Structure
```
├─ docs/                     # Publishable site (GitHub Pages root)
│   ├─ index.html            # Home page entry point
│   ├─ app.js                # Navigation & content loading
│   ├─ style.css             # Global stylesheet
│   ├─ CNAME                 # Custom domain
│   ├─ content/              # JSON data for pages and site config
│   │   ├─ site.json         # Route registry
│   │   ├─ header.json       # Navigation structure
│   │   └─ *.json            # Individual page content
│   └─ pages/                # HTML templates for each route
├─ scripts/                  # Python CMS utilities
│   ├─ site-manager.py       # Unified page & nav management
│   ├─ scan-pages.py         # Rebuild routes & nav from filesystem
│   └─ site_lib.py           # Shared helpers
└─ README.md
```

## Deployment
GitHub Pages serves the site from the `/docs` folder on the default branch.

1. Go to **Settings → Pages** in the GitHub repository.
2. Set **Source** to **Deploy from a branch**.
3. Choose your default branch and select the **`/docs`** folder.
4. The `docs/CNAME` file configures the custom domain (`madisonchinesedance.org`).

After changing the Pages source, allow a few minutes for the site to rebuild.

## Scripts & Utilities
The `scripts/` folder contains Python utilities that act as a lightweight CMS. Run all scripts from the repository root.

### Site manager (primary tool)
```bash
python scripts/site-manager.py
```

Interactive menu:
1. List routes
2. Create page
3. Delete page (removes HTML, JSON, and all nav/footer references)
4. Rename page (updates cross-references site-wide)
5. Rename folder
6. Edit navigation manually
7. Scan pages (rebuild `site.json` + nav)

### Scan pages
```bash
python scripts/scan-pages.py           # confirm before writing
python scripts/scan-pages.py --write   # non-interactive
python scripts/scan-pages.py --dry-run # preview only
```

Scans `docs/` and regenerates:
- **`site.json`** — one route per HTML file (`index.html` → home, `pages/**/*.html` → other routes)
- **`header.json` nav** — folder structure becomes dropdown groups; `actions` (Tickets, Donate) are preserved and excluded from nav

Nav labels are taken from each page's `pageTitle` in its content JSON (with fallback to title-case slug). Custom nav labels that differ from `pageTitle` will be overwritten on each scan.

### Other scripts
```bash
python scripts/generate-ai-context.py   # Build ai-context.md from content JSON
python scripts/scan-images.py           # Sync gallery images from Cloudflare R2
```

## Managing Pages
Recommended workflow after structural changes:

```
python scripts/site-manager.py   # create, delete, or rename
python scripts/scan-pages.py --write   # refresh routes and navigation
```

### Create a new page
Use site-manager option **2**, or create the HTML/JSON files manually under `docs/pages/` and `docs/content/`, then run `scan-pages.py --write`.

### Delete a page
Use site-manager option **3**. This removes the route from `site.json`, `header.json`, `footer.json`, and `announcements.json`, then deletes the HTML and JSON files.

## Content Authoring
Content pages use `sections`. A section is the only layout primitive: it can be one column for a page intro or several columns for smaller repeated items.

```json
{
  "pageTitle": "Example Page",
  "metaDescription": "Short search description.",
  "sections": [
    {
      "columns": 1,
      "items": [
        {
          "blocks": [
            {
              "type": "heading",
              "level": 1,
              "id": "example-heading",
              "text": "Welcome",
              "fontSize": "heading-1",
              "align": "center"
            },
            {
              "type": "body",
              "text": "A short introduction for the page.",
              "fontSize": "body",
              "align": "left"
            }
          ]
        }
      ]
    },
    {
      "columns": 3,
      "items": [
        {
          "blocks": [
            {
              "type": "heading",
              "level": 2,
              "text": "Classes"
            },
            {
              "type": "body",
              "text": "Beginner through advanced instruction.",
              "actions": [
                {
                  "route": "beginner-dancers",
                  "label": "Start with classes"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Sections
- `columns`: number of columns from `1` to `4`.
- `items`: card objects rendered inside the section grid.
- `className`: optional extra CSS class (rarely needed).

Use `columns: 1` for full-width content. Use `columns: 2`, `3`, or `4` when you want smaller section items side by side.

On the homepage, layout is inferred automatically from your blocks (for example a gallery with `variant: "runner-tall"` inside a 2-column section creates the highlights sidebar layout). You do not need a section-level `variant`.

### Items
Each item contains a `blocks` array. Add blocks in the order they should appear on the page.

Supported block types: `heading`, `body`, `gallery`, `zeffyEmbed`

Optional item fields:
- `className`: optional extra CSS class.
- `align`: `left`, `center`, or `right` — applies to the whole item.

#### Heading blocks
```json
{
  "type": "heading",
  "level": 2,
  "id": "programs-heading",
  "text": "Programs",
  "fontSize": "heading-3",
  "align": "center"
}
```
`level` can be `1` through `6`.

#### Body blocks
```json
{
  "type": "body",
  "text": "Paragraph one.\n\nParagraph two with **bold** text.",
  "fontSize": "lg",
  "align": "left",
  "actions": [
    {
      "href": "https://example.com",
      "label": "Open link",
      "newTab": true
    }
  ]
}
```
Use `route` instead of `href` for internal site routes. Add multiple body blocks in the same item when you need separate paragraphs or action groups.

#### Gallery blocks
```json
{
  "type": "gallery",
  "variant": "runner"
}
```

Gallery `variant` controls carousel type and aspect ratio:
- `runner` — standard carousel with dots (16:9)
- `runner-tall` — tall sidebar carousel (4:5); uses `homepageRunnerTallImages`
- `runner-wide` — wide carousel (21:9); uses `homepageRunnerWideImages`
- `featured` — featured carousel with thumbnail strip
- `archive` — carousel with year-tabbed thumbnail grid; uses `galleryGroups`

Omit `variant` for a simple carousel plus thumbnail grid.

#### Zeffy embed blocks
```json
{
  "type": "zeffyEmbed",
  "formUrl": "/embed/donation-form/donate-to-madison-chinese-dance-academy",
  "iframeTitle": "Donation form powered by Zeffy"
}
```

### Typography controls
`fontSize` and `align` work on both `heading` and `body` blocks.

| Token | Use for |
|-------|---------|
| `heading-1` | Very large display text (homepage hero) |
| `heading-2` | Large featured headings |
| `heading-3` | Page titles |
| `heading-4` | Subsection headings |
| `heading-5` | Smaller headings |
| `heading-6` | Smallest heading preset |
| `body` | Normal body text |
| `lg` | Slightly larger body text |

`align`: `left` (default), `center`, or `right`

## Updating Performance Images
Performance images are stored in `docs/content/` (e.g., `docs/content/gallery.json`). Use `python scripts/scan-images.py` to sync from Cloudflare R2, or replace image URLs manually in the JSON files.

## Customizing Styles
All styling lives in `docs/style.css`. Adjust colors, fonts, or layout as needed.

## Notes & Tips
- **Run scripts from the repository root** so paths resolve correctly.
- **Serve locally from `docs/`** — that folder is the site root, matching GitHub Pages.
- After adding or moving HTML files, run `python scripts/scan-pages.py --write` to refresh routes and navigation.
- Nav labels come from each page's `pageTitle`; edit content JSON or run scan after renames.

## Contact
For questions or contributions, please open an issue on the GitHub repository or contact the project maintainers.
