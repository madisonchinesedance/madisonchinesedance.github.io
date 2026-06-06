# JSON Formatting Guide

This site is mostly edited through JSON files in `content/`. Page files use ordered blocks, so you can reorder, remove, or add visible page elements without editing HTML.

## Page File Shape

Most page JSON files should look like this:

```json
{
  "pageTitle": "About Us | Madison Chinese Dance Academy",
  "metaDescription": "Learn about Madison Chinese Dance Academy.",
  "blocks": [
    {
      "type": "hero",
      "blocks": []
    }
  ]
}
```

`pageTitle` controls the browser tab title.

`metaDescription` controls the page description used by search engines and link previews.

`blocks` is the ordered list of visible page content. Move items up or down in this array to change the page order.

## Text Formatting

Use `\n\n` to make a new paragraph inside a `text` field:

```json
{
  "type": "body",
  "text": "First paragraph.\n\nSecond paragraph."
}
```

The body renderer allows these inline tags: `<b>`, `<strong>`, `<i>`, `<em>`, and `<br>`.

```json
{
  "type": "body",
  "text": "<b>Email:</b> madison.chinese.dances@gmail.com"
}
```

## Hero Block

A `hero` block creates the large main panel at the top of a page.

```json
{
  "type": "hero",
  "blocks": [
    {
      "type": "heading1",
      "id": "about-heading",
      "text": "About Us"
    },
    {
      "type": "body",
      "text": "Page intro text goes here."
    }
  ]
}
```

Use `"variant": "home"` only for the homepage hero.

```json
{
  "type": "hero",
  "variant": "home",
  "blocks": []
}
```

## Section Block

A `section` block groups content below the hero.

```json
{
  "type": "section",
  "blocks": [
    {
      "type": "heading2",
      "id": "programs-heading",
      "text": "Programs"
    },
    {
      "type": "body",
      "text": "Section text goes here."
    }
  ]
}
```

Homepage sections can use the existing visual variants:

```json
{
  "type": "section",
  "variant": "home-intro",
  "blocks": []
}
```

```json
{
  "type": "section",
  "variant": "home-pathways",
  "blocks": []
}
```

## Headings

Use `heading1` for the main page heading. Usually each page should have one.

```json
{
  "type": "heading1",
  "id": "contact-heading",
  "text": "Contact"
}
```

Use `heading2` for section headings.

```json
{
  "type": "heading2",
  "id": "services-heading",
  "text": "Services"
}
```

`id` is optional, but useful for accessibility and section labels. Keep it unique on the page.

## Body Text

Use `body` for paragraphs. A body block can also include buttons through `actions`.

```json
{
  "type": "body",
  "text": "Join us for Splendid China 2026.",
  "actions": [
    {
      "route": "tickets",
      "label": "Purchase Tickets",
      "style": "primary"
    }
  ]
}
```

## Actions And Links

Actions create buttons. They can link to a route from `content/site.json`:

```json
{
  "route": "contact",
  "label": "Contact us",
  "style": "secondary"
}
```

Or to a direct URL:

```json
{
  "href": "https://www.zeffy.com/en-US/ticketing/splendid-china--2026",
  "label": "Open in Zeffy",
  "style": "primary",
  "newTab": true
}
```

Action fields:

- `route`: links to a route defined in `content/site.json`.
- `href`: direct link, email link, phone link, anchor link, or full URL.
- `label`: visible button text.
- `style`: use `primary` or `secondary`.
- `newTab`: set to `true` for external links that should open in a new tab.
- `ariaLabel`: optional accessible label.
- `className`: optional extra CSS class, only use when a page already has a matching style.

## Cards

Use `type: "cards"` for repeated card-like items.

```json
{
  "type": "cards",
  "columns": 2,
  "items": [
    {
      "heading": "Dance Lessons",
      "body": "For Chinese dances, ballet, lyrical, Jazz, and Hip-Hop.",
      "route": "beginner-dancers",
      "label": "Start with beginner dancers"
    },
    {
      "heading": "Performances",
      "body": "For public and private events."
    }
  ]
}
```

`columns` controls how many items appear in one row on desktop. Use `1`, `2`, `3`, or `4`. On smaller screens, the grid collapses to one column automatically.

Optional card layout fields:

- `variant`: optional visual variant, only when the stylesheet already defines one for that card group.
- `headingTag`: optional heading tag for card headings, such as `h2` or `h3`. The default is `h3`.
- `headingSize`: optional CSS font size for all card headings in the group, such as `1.5rem` or `var(--heading-1-font-size)`.

Item fields:

- `heading`: card title.
- `headingTag`: optional heading tag for this card only.
- `headingSize`: optional CSS font size for this card only.
- `body`: card text.
- `route`: optional internal link.
- `href`: optional direct link.
- `label`: link text shown at the bottom of linked cards.

If an item has no `route` or `href`, it renders as a plain card.

## Stat Cards

Stats are regular cards. Use `headingTag` and `headingSize` when their heading should read larger than ordinary card titles.

```json
{
  "type": "cards",
  "columns": 3,
  "headingTag": "h2",
  "headingSize": "var(--heading-1-font-size)",
  "items": [
    {
      "heading": "1987",
      "body": "Founded as a nonprofit academy"
    }
  ]
}
```

## Gallery

Use `gallery` for the gallery carousel and thumbnail grid.

```json
{
  "type": "gallery",
  "groups": [],
  "images": [
    {
      "src": "/images/gallery/image-001.jpg",
      "thumb": "/images/gallery/image-001.jpg",
      "alt": "Image 001"
    }
  ]
}
```

Simple image fields:

- `src`: full image path.
- `thumb`: thumbnail path. It can be the same as `src`.
- `alt`: image description.

Grouped galleries can use this shape:

```json
{
  "type": "gallery",
  "groups": [
    {
      "year": "2026",
      "events": [
        {
          "event": "Splendid China",
          "images": [
            {
              "src": "/images/gallery/image-001.jpg",
              "thumb": "/images/gallery/image-001.jpg",
              "alt": "Performer on stage"
            }
          ]
        }
      ]
    }
  ]
}
```

## Zeffy Embed

Use `zeffyEmbed` for donation and ticket forms.

```json
{
  "type": "zeffyEmbed",
  "formUrl": "/embed/ticketing/splendid-china--2026",
  "iframeTitle": "Ticketing form powered by Zeffy"
}
```

Fields:

- `formUrl`: the Zeffy embed path.
- `iframeTitle`: accessible title for the fallback iframe.
- `iframeSrc`: optional full iframe URL. If omitted, the site builds it from `formUrl`.

## Site Routes

Internal route names live in `content/site.json`.

Use route names like this:

```json
{
  "route": "tickets",
  "label": "Purchase tickets"
}
```

Common route names include:

- `home`
- `about`
- `contact`
- `events`
- `services`
- `beginner-dancers`
- `intermediate-dancers`
- `advanced-dancers`
- `gallery`
- `tickets`
- `donate`
- `splendid-china-2026`

## Header JSON

`content/header.json` controls the logo, main navigation, and header action buttons.

Navigation items can link directly to a route:

```json
{
  "route": "gallery",
  "label": "Gallery"
}
```

Dropdown navigation uses `items`:

```json
{
  "label": "Programs",
  "items": [
    {
      "route": "beginner-dancers",
      "label": "Beginner Dancers"
    }
  ]
}
```

Header action buttons use:

```json
{
  "route": "tickets",
  "label": "Purchase Tickets",
  "style": "primary",
  "ariaLabel": "Purchase Tickets"
}
```

## Footer JSON

`content/footer.json` controls the footer brand text and columns.

```json
{
  "heading": "Quick Links",
  "links": [
    {
      "route": "home",
      "label": "Home"
    },
    {
      "href": "mailto:madison.chinese.dances@gmail.com",
      "label": "madison.chinese.dances@gmail.com"
    },
    {
      "label": "PO Box 10067 Rockville, MD 20849"
    }
  ]
}
```

Links with only `label` render as plain text.

## Announcements JSON

`content/announcements.json` controls the announcement bar.

```json
{
  "id": "splendid-china-2026",
  "enabled": true,
  "label": "Upcoming Event",
  "body": "Tickets are on sale now!",
  "actions": [
    {
      "route": "tickets",
      "label": "Purchase Tickets",
      "style": "primary",
      "ariaLabel": "Purchase Splendid China 2026 tickets"
    }
  ]
}
```

Set `enabled` to `false` to hide an announcement without deleting it.

The `highlights` object controls glowing highlights on nav or action routes:

```json
{
  "enabled": true,
  "color": "gold",
  "style": "pulse",
  "navRoutes": ["splendid-china-2026"],
  "actionRoutes": []
}
```

## Practical Editing Rules

- Keep valid JSON: every string uses double quotes, and every item in a list needs a comma except the last one.
- Page content belongs in the top-level `blocks` array.
- Use `hero` for the main top panel.
- Use `section` to group related content.
- Use `cards` for repeated cards or tile-like content.
- Use `columns` on `cards` to control the desktop layout.
- Prefer `route` for internal links and `href` for external links.
- Keep one `heading1` per page when possible.
- Reorder visible page content by moving objects inside the `blocks` array.
