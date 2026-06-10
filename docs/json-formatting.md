# JSON Formatting

Content pages use `sections`. A section is the only layout primitive: it can be one column for a page intro or several columns for smaller repeated items.

```json
{
  "pageTitle": "Example Page",
  "metaDescription": "Short search description.",
  "sections": [
    {
      "name": "intro",
      "columns": 1,
      "items": [
        {
          "heading1": {
            "id": "example-heading",
            "text": "Welcome",
            "fontSize": "var(--heading-1-font-size)"
          },
          "body": {
            "text": "A short introduction for the page."
          }
        }
      ]
    },
    {
      "name": "options",
      "columns": 3,
      "items": [
        {
          "heading2": {
            "text": "Classes"
          },
          "body": {
            "text": "Beginner through advanced instruction.",
            "actions": [
              {
                "route": "beginner-dancers",
                "label": "Start with classes"
              }
            ]
          }
        },
        {
          "heading2": {
            "text": "Performances"
          },
          "body": {
            "text": "Annual concerts and community programs."
          }
        },
        {
          "heading2": {
            "text": "Contact"
          },
          "body": {
            "text": "Ask about classes, bookings, or support."
          }
        }
      ]
    }
  ]
}
```

## Sections

- `name`: optional stable name used for a generated CSS class like `section-intro`.
- `columns`: number of columns from `1` to `4`.
- `className`: optional extra CSS class.
- `items`: content objects rendered inside the section grid.

Use `columns: 1` for full-width content. Use `columns: 2`, `3`, or `4` when you want smaller section items side by side.

## Items

Items are plain objects keyed by the content they contain:

- `heading1` through `heading6`
- `body`
- `gallery`
- `zeffyEmbed`

Headings support:

```json
{
  "heading2": {
    "id": "programs-heading",
    "text": "Programs",
    "fontSize": "var(--heading-1-font-size)"
  }
}
```

Body content supports rich text and actions:

```json
{
  "body": {
    "text": "Paragraph one.\n\nParagraph two with **bold** text.",
    "actions": [
      {
        "href": "https://example.com",
        "label": "Open link",
        "newTab": true
      }
    ]
  }
}
```

Use `route` instead of `href` for internal site routes.
