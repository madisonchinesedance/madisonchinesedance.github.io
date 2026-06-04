# Madison Chinese Dance Academy — Website

This repository contains a small, responsive static website for the Madison Chinese Dance Academy. It's authored with plain HTML, CSS, and a tiny JavaScript helper for navigation.

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

After changing a JSON file, save it and refresh the page. For local preview, serve the folder over HTTP, because browsers may block JSON loading from a plain `file://` tab.

## Project structure

- `index.html` — site home (hero + header/footer). Keep at repo root for Pages.
- `pages/` — secondary pages. Each page uses root-absolute `/style.css` and `/app.js` so assets work regardless of folder depth.
- `content/` — editable JSON files used as a lightweight CMS.
- `images/` — image assets for the site. Gallery images currently live directly in `images/gallery/`.
- `scripts/scan-gallery.js` — scans `images/gallery/` and updates `content/gallery.json`.
- `style.css` — global styles and CSS custom properties (theme variables).
- `app.js` — loads `site.json` and page content, renders shared header/footer, and handles the mobile nav toggle.

## Moving or adding a page

1. Add or update the HTML file under `pages/` (or root for the homepage).
2. Add the page's content JSON under `content/`.
3. Add a route entry in `content/site.json` (`href`, `page`, `content`).
4. Wire the page into `header.nav` or `header.actions` in `site.json` if it should appear in the menu.
5. Set `data-route="<route-id>"` on the page's `<body>` tag.

You do not need to update paths in every JSON file if links use `@route-id` references.

## Updating gallery images

Add images directly under the gallery folder, for example:

`images/gallery/my-photo.jpg`

Then run:

```sh
node scripts/scan-gallery.js
```

The scanner updates `content/gallery.json`, and the Gallery page renders the images in filename order.

## Customizing styles

- Edit `style.css` variables at the top (`:root`) to adjust the theme and layout:
	- `--base-font-size` — root font size (px)
	- `--body-font-size` and `--body-font-color` — paragraph text size and color
	- `--nav-link-font-size` — header tab text size
	- `--page-heading-size` and `--page-heading-weight` — page/hero heading sizing
	- `--content-max` — maximum measure used for centered content blocks

## Notes & tips

- The homepage hero uses the same page-hero styles so typography and alignment stay consistent across pages.
- Pages load assets from the site root (`/style.css`, `/app.js`, `/content/...`), which matches the custom domain deployment at `madisonchinesedance.org`.

## Contact

- Website Developer and Maintainer: joshuacheng.dev@gmail.com
- Organizational Contact: ahuan98-dance@yahoo.com
