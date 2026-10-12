# Reusable blocks

A **reusable block** is a saved, admin-designed section of content that can be
imported into other pages, forms, menus, feed item cards and emails. It is a
**live reference**: editing the saved entry updates every place that imports it.

Reusable blocks are found under **Design → Reusable blocks** (web) and
**Emails → Reusable content** (email).

## How it works

Each entry stores a `StreamField` designed exactly like the content it will be
used in:

* a web **Reusable block** holds any top-level page-content block (the same
  set as a page body — sections, grids, cards, text, media, feedback, inputs…);
* a **Reusable content** email entry holds body-level MJML components
  (section, wrapper, hero, raw).

To use one, add a **Reusable block** (web) or **Reusable content** (email) block
and pick the saved entry. The referenced blocks render at the insertion point,
so the current theme, design channels, request, audience rules and context
values all apply as if the content were placed directly.

## Live reference semantics

* Editing the saved entry changes every page that imports it.
* Deleting the entry leaves the importing block in place but renders nothing.
* Reusable entries **cannot contain other reusable entries**, so references can
  never recurse.

## Web example

1. Create **Design → Reusable blocks → "Homepage promo"** and design a hero
   with a heading, text and button.
2. On any page, add a **Reusable block** and choose *Homepage promo*.
3. Later, edit *Homepage promo* once to update it everywhere.

The block also appears in menu item streams, so a designed call-to-action can be
shared between a page and a navigation menu.

## Email example

1. Create **Emails → Reusable content → "Standard footer"** and design a
   section.
2. In an **Email template**, add **Reusable content** and choose *Standard
   footer*.

Because an `mj-body` only accepts `mj-section`/`mj-wrapper`/`mj-hero`/`mj-raw`
children, the email chooser inlines the saved components with no wrapper
element.
