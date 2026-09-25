# Demo fixtures

The demo loader (`demo/blog/management/commands/load_initial_data.py`) reads
flat page, post, author and image data from these files, then seeds related
snippets programmatically, including DaisyUI themes, menus, 403/404/500 error
pages, email templates, notification audiences and feeds.

## Layout

```
demo/fixtures/
├── content.json            # pages, posts, people and image specs
└── media/original_images/  # original image files referenced by content.json
```

## `content.json` schema

```jsonc
{
  "collections": {"1": "Root", "2": "Bakeries"},   // id -> name
  "images": {
    "<key>": {
      "collection": 2,
      "title": "…",
      "file": "original_images/breads1.jpg",       // relative to media/
      "description": "…",
      "created_at": "2019-02-17T08:10:34.237Z",
      "focal_point_x": null, "focal_point_y": null
    }
  },
  "people": [
    {"key": "roberta-johnson", "first_name": "…", "last_name": "…",
     "job_title": "…", "image": "<image key>"}
  ],
  "blog_index": {"title": "Blog", "slug": "blog", "seo_title": "…",
                 "introduction": "…", "image": "<image key>"},
  "posts": [
    {"slug": "…", "title": "…", "subtitle": "…", "introduction": "…",
     "image": "<image key>", "date_published": "2019-01-12",
     "tags": ["yeast"], "authors": ["roberta-johnson"],
     "body": [{"type": "paragraph_block", "value": "<p>…</p>"},
              {"type": "image_block", "value": {"image": "<image key>",
               "caption": "…", "attribution": "…"}}]}
  ],
  "home": {"title": "Home", "image": "<image key>",
           "body": [{"type": "rich_text", "value": "<p>…</p>"}]}
}
```

`body` block types are mapped by the loader to the package's `ContentBlock`
types (`paragraph_block`/`rich_text` → `rich_text`, `image_block` → `image`,
`block_quote` → `blockquote`, `embed_block` → `embed`).

The command is idempotent; pass `--force` to recreate content and seeded
snippets.
