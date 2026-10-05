# Migrations and block serialization

This document explains how `wagtail_daisIE` keeps its StreamField migrations
small, how that interacts with Wagtail's normal behaviour, and what it means for
projects that consume the package.

## The problem

Wagtail freezes the full block definition of every `StreamField` into each
migration's `block_lookup` table. Its docs call this out explicitly:

> "StructBlock, StreamBlock, and ChoiceBlock implement additional logic to
> ensure that any subclasses of these blocks are deconstructed to plain
> instances of StructBlock, StreamBlock and ChoiceBlock ... In this way, the
> migrations avoid having any references to your custom class definitions ...
> which would cause problems later on if those definitions are moved or
> deleted."

The trade-off is size. `wagtail_daisIE` ships well over a hundred composable
blocks, each built from design, typography, size, spacing and background
primitives. Inlining every subclass recursively produced a single `StreamField`
`block_lookup` of ~390 entries (~90 KB) and made `makemigrations` take minutes;
on a large project with many models the migration run reached tens of minutes.

## How compaction works

The package's blocks derive from `DaisieStructBlock` / `DaisieStreamBlock`
(`src/wagtail_daisIE/base_blocks/compact.py`). A concrete block class is
registered, once, in a process-wide registry (`src/wagtail_daisIE/blockref.py`)
under a stable key. Instead of expanding a block's children, its
`deconstruct_with_lookup` writes a single reference:

```python
block_lookup = {
    0: (
        "wagtail_daisIE.blockref.RegisteredBlock",
        ["wagtail_daisIE.InlineTextBlock"],
        {},
    ),
    1: ("wagtail_daisIE.blockref.RegisteredBlock", ["wagtail_daisIE.ImageBlock"], {}),
    # ...
}
```

When Django reads the migration, `BlockDefinitionLookup` imports
`wagtail_daisIE.blockref`, calls `RegisteredBlock.construct_from_lookup`, and the
registry returns a fresh instance built from the live class definition. The
registry is populated when block modules are imported, which happens while
Django loads the owning app's models - before any migration is read or written.

This mirrors `wagtail_daisIE.choicelist.ChoiceList`, which keeps static choice
options out of migrations by storing a registry key.

Only declarative blocks are keyed. A block built with explicit constructor
arguments or `local_blocks` falls back to Wagtail's expanded form, so
parameterised blocks can never be reconstructed incorrectly.

## The key contract

The default key is `"<top_level_package>.<ClassName>"`, e.g.
`wagtail_daisIE.InlineTextBlock` or `home.MyBlock`.

| Change | Effect on history |
|---|---|
| Move a class within the same top-level package | Key unchanged - nothing to do |
| Rename a class | Set `class Meta: migration_key = "<old key>"` on the renamed class |
| Move a class to a different top-level package | Same as a rename: freeze the key |
| Delete a class that migrations reference | Migrations raise a clear `KeyError`; restore the class or its key |
| Two classes with the same key | `register_block` raises at import time |

`migration_key` is the stable contract; the class name and module path are not.
Because only `StructBlock`/`StreamBlock` subclasses are keyed, custom
`FieldBlock` subclasses (for example `IconChooserBlock`) still serialise by
module path and should not be renamed or moved.

## What is stored per migration

A compact entry is `component name (key) + content + design`:

- the **key** identifies the block class;
- the **stored value** (in the database) is unchanged - block type plus its
  value, including design/CSS fields;
- the **field's top-level block set** (`block_types`) is still recorded in
  full, so adding or removing a top-level block still produces a migration.

Internal changes to a block's fields (adding, removing or reordering a child
field) no longer produce a migration. This is safe because `StreamField` is a
`JSONField`: there is no schema/DDL change. The trade-off is that the migration
is no longer an audit trail for block shape; see the guards below.

## Runtime is unaffected

Compaction changes only what is written to and read from migration files.
Everything at runtime uses the live block classes:

- the Wagtail admin editor and its telepath block definitions;
- page revisions, previews and draft state;
- template rendering and the `block_css` pipeline;
- fixture/profile seeding (`load_initial_data`), which assigns values to live
  model fields and therefore goes through `StreamField.to_python` and
  `get_prep_value` on the live `stream_block`.

No `StreamField` subclass is involved, which is why the previous
`LazyStreamField` failure (revisions serialising empty bodies) cannot recur
here.

## Adding a block

Subclass the package bases, not Wagtail's, so the block is registered and
compacted:

```python
from wagtail_daisIE.base_blocks import DaisieStructBlock


class MyBlock(DaisieStructBlock):
    heading = blocks.CharBlock()

    class Meta:
        icon = "placeholder"
        template = "wagtail_daisIE/blocks/my_block.html"
```

Blocks that subclass `ThemedBlock` (and the other `Themed*`/`Design*` bases)
inherit this automatically. If you rename a class later, set
`Meta.migration_key` to its previous key first.

## Upgrading / regenerating migrations

When the package's migration files change (release 2.0) or when a project adds
blocks, regenerate migrations in the owning apps and commit the result:

```bash
python manage.py makemigrations wagtail_daisIE wagtail_daisIE_assets \
  wagtail_daisIE_menus wagtail_daisIE_feeds wagtail_daisIE_errors \
  wagtail_daisIE_notifications wagtail_daisIE_allauth_ui wagtail_daisIE_allauth_emails
python manage.py makemigrations <your_apps>
python manage.py makemigrations --check --noinput   # must be clean
```

## Data-loss guarantees and limits

- Compaction is a migration-state-only change. `StreamField` columns are
  `JSONField`, so the database schema is identical and existing content is
  untouched. A correct upgrade requires migration **file names** to be
  unchanged (Django tracks migrations by name, not content); verify with
  `git status` and `makemigrations --check`.
- Removed, renamed or moved blocks without a preserved key break historical
  migrations with an explicit error; there is no compatibility shim.
- Removing a field from a block silently drops that key from stored JSON on the
  next load/save (standard `StructBlock.to_python` behaviour). Back up before
  removing fields.

## Guards

Two tests in `tests/core/test_compact_blocks.py` protect the mechanism:

1. `test_streamfield_migration_round_trip` - every model `StreamField`
   deconstructs, rebuilds and deconstructs identically, and the content block
   set contains no frozen `StructBlock`/`StreamBlock` trees.
2. `test_shipped_migration_block_keys_resolve` - every registry key already
   written into the shipped migrations still resolves, catching an unguarded
   rename.

CI additionally runs `makemigrations --check --noinput`, which still detects
added/removed/renamed top-level blocks.
