# Madison Chinese Dance Academy — Website

This repository contains the static website for the Madison Chinese Dance Academy. It's authored with plain HTML, CSS, and a tiny JavaScript helper for navigation.

## Editing site text

Most visible site text is controlled by JSON files in `content/`. To update copy, open the matching file and edit the text value:

- `content/site.json` — routes (page URLs, content files), header navigation, and footer. **Update this when moving or renaming pages** so links stay in sync across the site.
- `content/index.json` — homepage hero text.
- `content/about/about.json` — About page title, description, heading, and body.
- `content/programs/dance-classes.json` — Dance Classes page copy.
- `content/community/events.json` and `content/community/services.json` — Community pages.
- `content/splendid-china/splendid-china-YYYY.json` — Splendid China archive page text for each year.
- `content/tickets.json` — Tickets page text and Zeffy ticket link.
- `content/donate.json` — Donate page text and Zeffy donation link.
- `content/about/contact.json` — Contact page text.
- `content/gallery.json` — Gallery page text and image list (also updated by the gallery scanner).

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
- `images/` — image assets for the site. Splendid China photos live in `images/splendid-china/splendid-china-YYYY/` folders, one folder per year.
- `scripts/scan-images.py` — scans `images/splendid-china/splendid-china-YYYY/` folders and updates `content/gallery.json` with grouped year entries.
- `scripts/rename.py` — renames images in a folder to use the folder's name as a prefix (e.g. `images/splendid-china/splendid-china-2021/IMG_1234.jpg` → `splendid-china-2021-01.jpg`).
- `style.css` — global styles and CSS custom properties (theme variables).
- `app.js` — loads `site.json` and page content, renders shared header/footer, and handles the mobile nav toggle.

## Moving or adding a page

1. Add or update the HTML file under `pages/` (or root for the homepage).
2. Add the page's content JSON under `content/`.
3. Add a route entry in `content/site.json` (`href`, `page`, `content`).
4. Wire the page into `header.nav` or `header.actions` in `site.json` if it should appear in the menu.
5. Set `data-route="<route-id>"` on the page's `<body>` tag.

You do not need to update paths in every JSON file if links use `@route-id` references.

## Updating performance images

Photos are organized by Splendid China year. Add images directly to the matching year folder under `images/splendid-china/splendid-china-YYYY/`, for example:

`images/splendid-china/splendid-china-2026/showcase-01.jpg`

Then run:

```sh
python scripts/scan-images.py
```

The scanner walks every year folder under `images/splendid-china/`, builds year groups in reverse-chronological order, and writes the result to `content/gallery.json`. Year folders without images are skipped, and within each year the images are sorted by filename.

To target a different root or output file, pass `--images-dir` or `--content`:

```sh
python scripts/scan-images.py --images-dir path/to/images --content content/gallery.json
```

### Standardizing image filenames

To make a year folder's images easy to scan and serve, you can rename them so the filename reflects the folder. The included `scripts/rename.py` prefixes every image in a folder with the folder's own name:

```sh
# Interactive: prompts for the path
python scripts/rename.py

# Or pass the path directly
python scripts/rename.py images/splendid-china/splendid-china-2021
```

For a folder named `splendid-china-2021` containing `IMG_1234.jpg` and `IMG_5678.jpg`, the script will produce `splendid-china-2021-01.jpg` and `splendid-china-2021-02.jpg` in filename order.

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

## Contact

- Website Developer and Maintainer: joshuacheng.dev@gmail.com
- Organizational Contact: ahuan98-dance@yahoo.com
