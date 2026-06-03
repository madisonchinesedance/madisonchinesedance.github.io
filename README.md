# Madison Chinese Dance Academy — Website

This repository contains a small, responsive static website for the Madison Chinese Dance Academy. It's authored with plain HTML, CSS, and a tiny JavaScript helper for navigation.

## Editing site text

Most visible site text is controlled by JSON files in `content/`. To update copy, open the matching file and edit the text value:

- `content/site.json` — shared header logo, navigation dropdowns, header buttons, footer, and site metadata. Header settings live under the `header` object.
- `content/index.json` — homepage hero text.
- `content/about.json` — About page title, description, heading, and body.
- `content/dance-classes.json` — Dance Classes page title, description, heading, and body.
- `content/splendid-china-YYYY.json` — Splendid China archive page text for each year.
- `content/tickets.json` — Tickets page text and Zeffy ticket link.
- `content/donate.json` — Donate page text and Zeffy donation link.
- `content/contact.json` — Contact page text.

After changing a JSON file, save it and refresh the page. For local preview, serve the folder over HTTP, because browsers may block JSON loading from a plain `file://` tab.

## Project structure

- `index.html` — site home (hero + header/footer). Keep at repo root for Pages.
- `pages/` — secondary pages (moved from root). Files reference assets with `../` so they work from inside `pages/`.
- `content/` — editable JSON files used as a lightweight CMS.
- `images/` — image assets for the site. Gallery images currently live directly in `images/gallery/`.
- `scripts/scan-gallery.js` — scans `images/gallery/` and updates `content/gallery.json`.
- `style.css` — global styles and CSS custom properties (theme variables).
- `app.js` — loads JSON content, renders shared header/footer, and handles the mobile nav toggle.

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
- When adding or moving pages, keep relative paths correct: pages in the `pages/` folder link to assets using `../style.css` and `../app.js`.

## Contact

- Website Developer and Maintainer: joshuacheng.dev@gmail.com
- Organizational Contact: ahuan98-dance@yahoo.com
