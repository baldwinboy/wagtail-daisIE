"""Guards for compact (registry-key) block serialization in migrations.

Wagtail freezes declarative blocks into ``block_lookup``; the package's bases
serialise them as stable registry keys instead (see
``wagtail_daisIE.base_blocks.compact``). Two guards keep that from regressing:
every model StreamField must round-trip through its deconstruction, and every
key already written into the shipped migrations must still resolve.
"""

import re

from pathlib import Path

from django.apps import apps
from wagtail.fields import StreamField


def _stream_fields():
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, StreamField):
                yield model, field


def test_streamfield_migration_round_trip():
    from wagtail_daisIE.blockref import get_block
    from wagtail_daisIE.blocks.content import CONTENT_BLOCK

    checked = 0
    for _model, field in _stream_fields():
        checked += 1
        _name, _path, args, kwargs = field.deconstruct()
        rebuilt = StreamField(*args, **kwargs)
        assert rebuilt.deconstruct()[3]["block_lookup"] == kwargs["block_lookup"]
    assert checked

    _name, _path, _args, kwargs = StreamField(CONTENT_BLOCK(), blank=True).deconstruct()
    lookup = kwargs["block_lookup"]
    paths = {entry[0] for entry in lookup.values()}
    assert "wagtail.blocks.StructBlock" not in paths
    assert "wagtail.blocks.StreamBlock" not in paths
    for entry in lookup.values():
        if entry[0].endswith("RegisteredBlock"):
            assert get_block(entry[1][0]) is not None


def test_shipped_migration_block_keys_resolve():
    from wagtail_daisIE.blockref import get_block

    root = Path(__file__).resolve().parents[2] / "src" / "wagtail_daisIE"
    pattern = re.compile(r"RegisteredBlock',\s*\[([^\]]+)\]")
    found = 0
    for path in root.rglob("migrations/*.py"):
        for raw in pattern.findall(path.read_text()):
            for key in re.findall(r"['\"]([^'\"]+)['\"]", raw):
                found += 1
                assert get_block(key) is not None, f"{path}: {key}"
    assert found
