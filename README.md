# Madison Chinese Dance Academy — Website

This repository contains the static website for the Madison Chinese Dance Academy. It's authored with plain HTML, CSS, and a tiny JavaScript helper for navigation.

## Editing site text

Most visible site text is controlled by JSON files in `content/`. To update copy, open the matching file and edit the text value:

- `content/site.json` — routes (page URLs, content files). **Update this when moving or renaming pages** so links stay in sync across the site.
- `content/header.json` — main navigation, logo, action buttons, and announcements.
- `content/footer.json` — footer brand text and columns.
- `content/index.json` — homepage hero text.
- `content/faq.json` — FAQ page questions and answers.
- `content/tickets.json` — Tickets page text and Zeffy ticket link.
- `content/donate.json` — Donate page text and Zeffy donation link.
- `content/gallery.json` — Gallery page text and image list (also updated by the gallery scanner).
- `content/programs/beginner-dancers.json`, `intermediate-dancers.json`, `advanced-dancers.json` — Dance program pages.
- `content/splendid-china/splendid-china-YYYY.json` — Splendid China archive page text for each year.

### Internal links in JSON

Reference another site page with a route id instead of a file path:

```json
"splendidTicketsHref": "@tickets"
```

Route ids are defined under `routes` in `content/site.json` (for example `home`, `gallery`, `tickets`, `splendid-china-2026`).

### Line breaks and emphasis in JSON

In page body fields (paragraphs, divs, buttons, and similar), you can format copy directly in JSON:

- `\n` — line break within the same paragraph
- `\n\n` — start a new paragraph (on `<div>` blocks, each becomes a `<p>`)
- `<b>`, `<strong>`, `<i>`, `<em>`, `<br>` — bold, italic, or manual line breaks

Example:

```json
"classesBody": "We offer classes for <b>all ages</b>.\n\nSchedule details will be posted here."
```

Titles, headings (`<h1>`–`<h6>`), and meta descriptions stay plain text only. Use `data-json-plain` on an element if you need to force plain text on a specific field.

After changing a JSON file, save it and refresh the page. For local preview, serve the folder over HTTP, because browsers may block JSON loading from a plain `file://` tab.

## Project structure

- `index.html` — site home (hero + header/footer). Keep at repo root for Pages.
- `pages/` — secondary pages. Each page uses root-absolute `/style.css` and `/app.js` so assets work regardless of folder depth.
- `content/` — editable JSON files used as a lightweight CMS.
- `scripts/scan-images.py` — connects to the Cloudflare R2 bucket and updates `content/gallery.json` with grouped year entries.
- `scripts/generate-ai-context.py` — generates `ai-context.md` from content JSON files (used for AI chatbot context).
- `style.css` — global styles and CSS custom properties (theme variables).
- `app.js` — loads `site.json` and page content, renders shared header/footer, and handles the mobile nav toggle.
- `docs/` — project documentation (JSON formatting guide, etc.).

## Adding or moving a page

1. Add or update the HTML file under `pages/` (or root for the homepage).
2. Add the page's content JSON under `content/`.
3. Add a route entry in `content/site.json` (`href`, `page`, `content`).
4. Wire the page into `header.nav` or `header.actions` in `content/header.json` if it should appear in the menu.
5. Set `data-route="<route-id>"` on the page's `<body>` tag.

You do not need to update paths in every JSON file if links use `@route-id` references.

## Updating performance images

Photos are stored in a Cloudflare R2 bucket and served via `cdn.madisonchinesedance.org`. The bucket mirrors the local folder structure:

```
splendid-china/splendid-china-YYYY/filename.webp
```

To update the gallery after adding images to R2:

1. Set the required environment variables (or create `scripts/.env`):
   - `R2_ACCOUNT_ID`
   - `R2_ACCESS_KEY`
   - `R2_SECRET_KEY`
   - `R2_BUCKET`
   - `R2_PUBLIC_URL`

2. Install dependencies:
   ```sh
   pip install boto3 python-dotenv
   ```

3. Run the scanner:
   ```sh
   python scripts/scan-images.py
   ```

The scanner connects to the R2 bucket, finds all year folders, and writes the result to `content/gallery.json` and each per-year JSON file. Year folders without images are skipped, and within each year images are sorted by filename.

To target a different output file:

```sh
python scripts/scan-images.py --content content/gallery.json
```

## Customizing styles

- Edit `style.css` variables at the top (`:root`) to adjust the theme and layout:
	- `--base-font-size` — root font size (px)
	- `--body-font-size` and `--body-font-color` — paragraph text size and color
	- `--nav-link-font-size` — header tab text size
	- `--heading-1-font-size` and `--heading-1-font-weight` — page/hero heading sizing
	- `--content-width` — maximum measure used for centered content blocks

## Notes & tips

- The homepage hero uses the same page-hero styles so typography and alignment stay consistent across pages.
- Pages load assets from the site root (`/style.css`, `/app.js`, `/content/...`), which matches the custom domain deployment at `madisonchinesedance.org`.
- The chatbot widget loads on every page and connects to a Cloudflare Worker endpoint for AI responses.

## Contact

- Website Developer and Maintainer: joshuacheng.dev@gmail.com
- Organizational Contact: ahuan98-dance@yahoo.com