# Madison Chinese Dance Academy — Website

Lightweight, responsive single-page site for the Madison Chinese Dance Academy.

How to preview locally:

```powershell
# From the project root
python -m http.server 8000
# then open http://localhost:8000 in your browser
```

Deploy to GitHub Pages:

- Push the `main` branch to GitHub (this repository uses `main`).
- In the repository Settings → Pages, set the source to the `main` branch (root) and save.

Files of interest:

- `index.html` — main markup (semantic HTML5)
- `style.css` — styles, gradient background, responsive navigation
- `app.js` — small vanilla JS for mobile nav and language toggle

If you'd like, I can open a PR with these changes, or add a small deploy workflow next.