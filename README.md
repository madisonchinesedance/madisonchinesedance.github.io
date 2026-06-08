## Adding or moving a page

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

These tools keep `site.json`, `header.json`, the HTML files, and the JSON content files in sync, so you can work with the site like a lightweight CMS without memorizing JSON paths.

## Updating performance images

(unchanged)…

## Customizing styles

(unchanged)…

## Notes & tips

(unchanged)…

## Contact

(unchanged)…