"""Compact block serialization for migrations.

Wagtail freezes declarative ``StructBlock``/``StreamBlock`` subclasses into
migration ``block_lookup`` tables by expanding every child recursively, which
makes this package's migrations enormous and slow to autodetect. These bases
instead serialise a declarative block as a stable registry key, resolved at load
by :class:`wagtail_daisIE.blockref.RegisteredBlock`. This mirrors
:class:`wagtail_daisIE.choicelist.ChoiceList`, which keeps choices out of
migrations the same way.

Only declarative instances are keyed; anything built with explicit
``local_blocks``/arguments falls back to Wagtail's expanded form, so
parameterised blocks cannot be reconstructed wrong.

Runtime behaviour (admin, revisions, telepath, rendering, data loading) is
untouched: ``StreamField.deconstruct`` is the only caller, and it is used solely
by the migration autodetector and ``migrate``.
"""

from wagtail import blocks
from wagtail.blocks.base import DeclarativeSubBlocksMetaclass

from wagtail_daisIE.blockref import register_block


class CompactBlockMetaclass(DeclarativeSubBlocksMetaclass):
    """Register every concrete block under a path-independent key."""

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        # The compact bases themselves are not serialisable blocks. ``Meta`` has
        # already been popped and rebuilt as ``_meta_class`` by now.
        if cls.__module__ == "wagtail_daisIE.base_blocks.compact":
            return cls
        meta = getattr(cls, "_meta_class", None)
        key = getattr(meta, "migration_key", None)
        if not key:
            key = f"{cls.__module__.split('.')[0]}.{cls.__name__}"
        register_block(key, cls)
        cls._migration_key = key
        return cls


class CompactBlockMixin:
    @property
    def _is_declarative(self):
        args, kwargs = self._constructor_args
        return not args and not kwargs

    def deconstruct_with_lookup(self, lookup):
        if self._is_declarative:
            return (
                "wagtail_daisIE.blockref.RegisteredBlock",
                [self._migration_key],
                {},
            )
        return super().deconstruct_with_lookup(lookup)


class DaisieStructBlock(
    CompactBlockMixin, blocks.StructBlock, metaclass=CompactBlockMetaclass
):
    pass


class DaisieStreamBlock(
    CompactBlockMixin, blocks.StreamBlock, metaclass=CompactBlockMetaclass
):
    pass
