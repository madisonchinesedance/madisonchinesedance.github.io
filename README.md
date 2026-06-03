# Madison Chinese Dance Academy — Website

This repository contains a small, responsive static website for the Madison Chinese Dance Academy. It's authored with plain HTML, CSS, and a tiny JavaScript helper for navigation.

## Editing site text

Most visible site text is controlled by JSON files in `content/`. To update copy, open the matching file and edit the text value:

- `content/site.json` — shared header navigation, ticket/donate buttons, footer, and site metadata.
- `content/homepage.json` — homepage hero text.
- `content/about.json` — About page title, description, heading, and body.
- `content/classes.json` — Classes page title, description, heading, and body.
- `content/splendid.json` — Splendid China page event text and ticket button.
- `content/tickets.json` — Tickets page text and Zeffy ticket link.
- `content/donate.json` — Donate page text and Zeffy donation link.
- `content/contact.json` — Contact page text.

After changing a JSON file, save it and refresh the page. For local preview, serve the folder over HTTP, because browsers may block JSON loading from a plain `file://` tab.

## Project structure

- `index.html` — site home (hero + header/footer). Keep at repo root for Pages.
- `pages/` — secondary pages (moved from root). Files reference assets with `../` so they work from inside `pages/`.
- `content/` — editable JSON files used as a lightweight CMS.
- `style.css` — global styles and CSS custom properties (theme variables).
- `app.js` — loads JSON content, renders shared header/footer, and handles the mobile nav toggle.

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
