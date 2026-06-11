# JSON Formatting

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

## Sections

- `columns`: number of columns from `1` to `4`.
- `items`: card objects rendered inside the section grid.
- `className`: optional extra CSS class (rarely needed).

Use `columns: 1` for full-width content. Use `columns: 2`, `3`, or `4` when you want smaller section items side by side.

On the homepage, layout is inferred automatically from your blocks (for example a gallery with `variant: "runner-tall"` inside a 2-column section creates the highlights sidebar layout). You do not need a section-level `variant`.

## Items

Each item contains a `blocks` array. Add blocks in the order they should appear on the page.

Supported block types:

- `heading`
- `body`
- `gallery`
- `zeffyEmbed`

Optional item fields:

- `className`: optional extra CSS class.
- `align`: `left`, `center`, or `right` — applies to the whole item.

### Heading blocks

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

### Body blocks

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

Use `route` instead of `href` for internal site routes.

Add multiple body blocks in the same item when you need separate paragraphs or action groups.

### Gallery blocks

```json
{
  "type": "gallery",
  "variant": "runner"
}
```

Gallery `variant` controls carousel type and aspect ratio — not section layout:

- `runner` — standard homepage carousel (16:9)
- `runner-tall` — tall sidebar carousel (4:5)
- `runner-wide` — wide carousel (21:9)

Omit `variant` on gallery pages that use the thumbnail grid.

### Zeffy embed blocks

```json
{
  "type": "zeffyEmbed",
  "formUrl": "/embed/donation-form/donate-to-madison-chinese-dance-academy",
  "iframeTitle": "Donation form powered by Zeffy"
}
```

## Typography controls

`fontSize` and `align` work on both `heading` and `body` blocks.

### `fontSize` presets

| Token | Use for |
|-------|---------|
| `heading-1` | Very large display text (homepage hero) |
| `heading-2` | Large featured headings (homepage stats) |
| `heading-3` | Page titles |
| `heading-4` | Subsection headings |
| `heading-5` | Smaller headings |
| `heading-6` | Smallest heading preset |
| `body` | Normal body text |
| `lg` | Slightly larger body text |

Each `heading-N` token maps to `var(--heading-N-font-size)` in CSS.

Raw CSS values such as `clamp(...)`, `1.25rem`, and `var(--...)` are also accepted.

### `align`

- `left` (default)
- `center`
- `right`

Omit `align` when left alignment is fine.
