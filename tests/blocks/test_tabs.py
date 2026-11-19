import pytest

from django.core.exceptions import ImproperlyConfigured
from wagtail import blocks

from wagtail_daisIE.blocks.layout import (
    TabColumnBlock,
    TabGridBlock,
    TabLayoutItemBlock,
    TabRowBlock,
)
from wagtail_daisIE.blocks.layout_components import TabsBlock, TabsInlineBlock
from wagtail_daisIE.blocks.palettes import (
    get_palette,
    palette_keys,
)
from wagtail_daisIE.blocks.stream import (
    TabContentStreamBlock,
    TabLayoutContainerContentStreamBlock,
    TabLayoutStreamBlock,
)


pytestmark = pytest.mark.django_db


def _action_value():
    return {
        "action": "demo",
        "target_expression": "",
        "button": {"text": "Run", "design": {}, "audience": {}},
    }


def _walk_blocks(block, seen=None):
    seen = seen or set()
    if id(block) in seen:
        return
    seen.add(id(block))
    yield block
    if isinstance(block, blocks.StructBlock):
        for child in block.child_blocks.values():
            yield from _walk_blocks(child, seen)
    elif isinstance(block, blocks.StreamBlock):
        for child in block.child_blocks.values():
            yield from _walk_blocks(child, seen)
    elif isinstance(block, blocks.ListBlock):
        yield from _walk_blocks(block.child_block, seen)


class TestTabPalettes:
    def test_tab_content_is_superset_of_layout(self):
        assert set(palette_keys("layout")) <= set(palette_keys("tab_content"))

    def test_tab_content_has_expected_keys(self):
        keys = set(palette_keys("tab_content"))
        for key in (
            "layout_item",
            "row",
            "column",
            "grid",
            "feed",
            "action",
            "action_form",
            "autocomplete",
            "tabs_inline",
        ):
            assert key in keys
        assert "tabs" not in keys

    def test_tab_palette_classes(self):
        from wagtail_daisIE.blocks.layout import (
            TabColumnBlock,
            TabGridBlock,
            TabLayoutItemBlock,
            TabRowBlock,
        )

        assert palette_keys("tab_content").index("layout_item") >= 0
        stream = TabContentStreamBlock()
        assert type(stream.child_blocks["layout_item"]) is TabLayoutItemBlock
        assert type(stream.child_blocks["row"]) is TabRowBlock
        assert type(stream.child_blocks["column"]) is TabColumnBlock
        assert type(stream.child_blocks["grid"]) is TabGridBlock

    def test_tab_stream_palettes(self):
        assert TabLayoutStreamBlock().palette == "tab_layout"
        assert (
            TabLayoutContainerContentStreamBlock().palette
            == "tab_layout_container_content"
        )
        assert TabContentStreamBlock().palette == "tab_content"

    def test_tab_layout_item_content_palette(self):
        assert TabLayoutItemBlock().child_blocks["content"].palette == "tab_layout"

    def test_tab_container_content_palette(self):
        assert (
            TabRowBlock().child_blocks["content"].palette
            == "tab_layout_container_content"
        )
        assert (
            TabColumnBlock().child_blocks["content"].palette
            == "tab_layout_container_content"
        )
        assert (
            TabGridBlock().child_blocks["content"].palette
            == "tab_layout_container_content"
        )

    def test_palette_deconstructs_compactly(self):

        from wagtail.blocks.definition_lookup import BlockDefinitionLookupBuilder

        lookup = BlockDefinitionLookupBuilder()
        path, _args, _kwargs = TabContentStreamBlock().deconstruct_with_lookup(lookup)
        assert path == "wagtail_daisIE.blockref.RegisteredBlock"
        assert lookup.get_lookup_as_dict() == {}

    def test_no_full_tabs_reachable(self):
        blocks_to_check = [
            TabContentStreamBlock(),
            TabLayoutItemBlock(),
            TabRowBlock(),
            TabColumnBlock(),
            TabGridBlock(),
        ]
        for block in blocks_to_check:
            walked = list(_walk_blocks(block))
            assert not any(type(b) is TabsBlock for b in walked), type(block).__name__
        # tabs_inline is reachable and allowed
        all_walked = []
        for block in blocks_to_check:
            all_walked.extend(_walk_blocks(block))
        assert any(type(b) is TabsInlineBlock for b in all_walked)

    def test_tab_palette_rejects_full_tabs(self, monkeypatch):
        from wagtail_daisIE.blocks import palettes
        from wagtail_daisIE.blocks.layout_components import TabsBlock

        original = palettes._BUILDERS["tab_content"]

        def builder():
            return [*original(), ("tabs", TabsBlock())]

        monkeypatch.setattr(
            palettes, "_BUILDERS", {**palettes._BUILDERS, "tab_content": builder}
        )
        palettes._PALETTES.pop("tab_content", None)
        try:
            with pytest.raises(ImproperlyConfigured):
                get_palette("tab_content")
        finally:
            palettes._BUILDERS["tab_content"] = original
            palettes._PALETTES.pop("tab_content", None)

    def test_render_tab_with_row_and_layout_item(self):
        from django.conf import settings as django_settings

        django_settings.WAGTAIL_DAISIE_ACTIONS = {
            "demo": {"label": "Demo", "handler": "handler"}
        }

        tabs = TabsBlock().to_python(
            {
                "tabs": [
                    {
                        "label": "First",
                        "content": [
                            {
                                "type": "row",
                                "value": {
                                    "content": [
                                        {
                                            "type": "layout_item",
                                            "value": {
                                                "content": [
                                                    {
                                                        "type": "text",
                                                        "value": {
                                                            "text": "Hello",
                                                            "design": {},
                                                            "audience": {},
                                                        },
                                                    }
                                                ],
                                                "design": {
                                                    "grow": "grow",
                                                    "width": "w-1/2",
                                                },
                                                "audience": {},
                                                "visibility": {},
                                            },
                                        }
                                    ],
                                    "design": {},
                                    "audience": {},
                                    "wrap": "flex-wrap",
                                },
                            }
                        ],
                        "audience": {},
                    }
                ],
                "style": "tabs-box",
            }
        )
        html = TabsBlock().render(tabs)
        assert "Hello" in html
        assert "flex" in html
        assert "w-1/2" in html

    def test_render_tab_with_action_placement(self):
        from django.conf import settings as django_settings

        django_settings.WAGTAIL_DAISIE_ACTIONS = {
            "demo": {"label": "Demo", "handler": "handler"}
        }

        tabs = TabsBlock().to_python(
            {
                "tabs": [
                    {
                        "label": "First",
                        "content": [
                            {
                                "type": "layout_item",
                                "value": {
                                    "content": [
                                        {
                                            "type": "action",
                                            "value": {
                                                "action": "demo",
                                                "target_expression": "",
                                                "button": {
                                                    "text": "Run",
                                                    "design": {},
                                                    "audience": {},
                                                },
                                                "visibility": {},
                                            },
                                        }
                                    ],
                                    "design": {},
                                    "audience": {},
                                    "visibility": {},
                                },
                            }
                        ],
                        "audience": {},
                    }
                ],
                "style": "tabs-box",
            }
        )
        html = TabsBlock().render(tabs)
        assert "Run" in html
        assert "/daisie/actions/demo/" in html

    def test_tab_grid_spans(self):
        tabs = TabsBlock().to_python(
            {
                "tabs": [
                    {
                        "label": "First",
                        "content": [
                            {
                                "type": "grid",
                                "value": {
                                    "num_columns": 2,
                                    "content": [
                                        {
                                            "type": "layout_item",
                                            "value": {
                                                "content": [
                                                    {
                                                        "type": "text",
                                                        "value": {
                                                            "text": "Cell",
                                                            "design": {},
                                                            "audience": {},
                                                        },
                                                    }
                                                ],
                                                "design": {
                                                    "grid_column_span": "col-span-2",
                                                    "grid_row_span": "row-span-2",
                                                },
                                                "audience": {},
                                                "visibility": {},
                                            },
                                        }
                                    ],
                                    "design": {},
                                    "audience": {},
                                },
                            }
                        ],
                        "audience": {},
                    }
                ],
                "style": "tabs-box",
            }
        )
        html = TabsBlock().render(tabs)
        assert "Cell" in html
        assert "col-span-2" in html
        assert "row-span-2" in html
