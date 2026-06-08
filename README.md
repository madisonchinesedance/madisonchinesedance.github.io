# Madison Chinese Dance – Project Documentation

Welcome to the **Madison Chinese Dance** website repository. This project hosts the static site for the Madison Chinese Dance community, providing information about programs, events, performances, and ways to get involved.

## Table of Contents
- [About the Project](#about-the-project)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Scripts & Utilities](#scripts--utilities)
- [Adding or Moving a Page](#adding-or-moving-a-page)
- [Updating Performance Images](#updating-performance-images)
- [Customizing Styles](#customizing-styles)
- [Notes & Tips](#notes--tips)
- [Contact](#contact)

## About the Project
The site is a lightweight, JSON‑driven static website built with plain HTML, CSS, and a small amount of JavaScript (`app.js`). Content for each page lives in the `content/` directory as JSON files, and navigation is generated from `content/site.json`.

## Getting Started
1. **Clone the repository**  
   ```bash
   git clone https://github.com/madisonchinesedance/madisonchinesedance.github.io.git
   cd madisonchinesedance.github.io
   ```

2. **Open the site**  
   Simply open `index.html` in a browser or serve the directory with any static file server (e.g., `python -m http.server`).

3. **Development**  
   - Edit JSON files under `content/` to update page content.  
   - Modify HTML templates in the `pages/` folder if you need structural changes.  
   - Adjust styling in `style.css`.

## Project Structure
```
├─ app.js                # Core JavaScript for navigation & content loading
├─ index.html            # Home page entry point
├─ style.css             # Global stylesheet
├─ content/              # JSON data for pages and site navigation
│   ├─ site.json         # Master list of routes
│   ├─ header.json
│   └─ *.json            # Individual page content
├─ pages/                # HTML templates for each route
│   ├─ about/
│   ├─ community/
│   ├─ programs/
│   └─ ...                # Other sections
└─ scripts/              # Helper scripts for managing pages & navigation
```

## Scripts & Utilities
The `scripts/` folder contains Python utilities that act as a lightweight CMS:

- **Create a new page**  
  ```bash
  python scripts/create-page.py
  ```
  Prompts for title, slug, navigation placement, etc.

- **Manage navigation**  
  ```bash
  python scripts/manage-nav.py
  ```
  Options: list, rename, move, reorder, or delete navigation items.

- **Manage page files**  
  ```bash
  python scripts/manage-pages.py
  ```
  Options: list routes, rename a route (updates HTML, JSON, and `site.json`), move a page to a different folder.

These tools keep `site.json`, `header.json`, the HTML files, and the JSON content files in sync, allowing you to work with the site without manually editing multiple files.

## Adding or Moving a Page
### Create a new page
```sh
python scripts/create-page.py
```
The script will prompt you for:
- Page title
- Route slug (e.g., `about`, `programs/advanced-dancers`)
- Whether to add it to the main navigation
- Which dropdown to place it under (optional)

### Manage navigation
```sh
python scripts/manage-nav.py
```
A menu lets you:
- List current navigation
- Rename a nav item
- Move an item between top‑level and dropdowns
- Reorder items within a dropdown
- Remove an item

### Manage page files
```sh
python scripts/manage-pages.py
```
Options:
- List all routes
- Rename a route (updates HTML, JSON, and `site.json`)
- Move a page to a different folder

## Updating Performance Images
Performance images are stored in the `content/` directory (e.g., `content/gallery.json`). Replace the image URLs in the corresponding JSON file and commit the changes. The site will automatically display the new images.

## Customizing Styles
All styling lives in `style.css`. Adjust colors, fonts, or layout as needed. The stylesheet follows standard CSS conventions and is loaded globally.

## Notes & Tips
- **Run scripts from the repository root** to ensure paths resolve correctly.
- **Commit changes** to `site.json` and related JSON files together to keep navigation in sync.
- Use a static file server (e.g., `python -m http.server`) for local testing of navigation and content loading.

## Contact
For questions or contributions, please open an issue on the GitHub repository or contact the project maintainers.

---

*Last updated: $(date +"%Y-%m-%d")*