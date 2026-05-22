# Madison Chinese Dance Academy — Website

This repository contains a small, responsive static website for the Madison Chinese Dance Academy. It's authored with plain HTML, CSS, and a tiny JavaScript helper for navigation.

## Project structure

- `index.html` — site home (hero + header/footer). Keep at repo root for Pages.
- `pages/` — secondary pages (moved from root). Files reference assets with `../` so they work from inside `pages/`.
- `style.css` — global styles and CSS custom properties (theme variables).
- `app.js` — small JS for mobile nav toggle and any light interactions.

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