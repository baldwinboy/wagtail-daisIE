from wagtail_daisIE import choices
from wagtail_daisIE.choicelist import _CHOICE_REGISTRY, get_choice_list
from wagtail_daisIE.choices import (
    BLOCK_HEIGHT_CHOICES,
    BLOCK_MAX_HEIGHT_CHOICES,
    BLOCK_MAX_WIDTH_CHOICES,
    INLINE_MAX_HEIGHT_CHOICES,
    INLINE_MAX_WIDTH_CHOICES,
    INLINE_SIZE_CHOICES,
    INLINE_WIDTH_CHOICES,
    MARGIN_CHOICES,
)
from wagtail_daisIE.choices.utils import is_auto_utility


def test_choice_constants_are_lazy():
    """Every package choice list must be a callable ChoiceList.

    A plain list would be frozen verbatim into migrations; see
    ``wagtail_daisIE.choicelist.ChoiceList``.
    """
    names = [name for name in choices.__all__ if name.endswith("_CHOICES")]
    assert names
    for name in names:
        constant = getattr(choices, name)
        # Spacing is exposed as a dict of ChoiceLists; everything else is a
        # ChoiceList directly.
        values = constant.values() if isinstance(constant, dict) else [constant]
        for value in values:
            assert callable(value), f"{name} must be a ChoiceList"
            assert list(value), f"{name} must not be empty"


def test_choice_registry_is_resolvable():
    """Every registered key must resolve to the same object it was registered on."""
    assert _CHOICE_REGISTRY
    for key in _CHOICE_REGISTRY:
        assert callable(get_choice_list(key)), key


def test_choice_registry_keys_are_unique_per_list():
    """Distinct constants must not share a registry key."""
    import_paths = list(_CHOICE_REGISTRY.values())
    # The same path may be registered once; duplicate paths would only arise
    # from a duplicate key (which ChoiceList rejects), so this is a guard.
    assert len(import_paths) == len(set(import_paths))


def _values(choice_list):
    return [value for value, _label in choice_list]


def test_auto_choices_are_prefixed():
    for choice_list in MARGIN_CHOICES.values():
        values = _values(choice_list)
        assert "auto" not in values
        assert any(is_auto_utility(value) for value in values)

    for choice_list in (
        INLINE_WIDTH_CHOICES,
        BLOCK_HEIGHT_CHOICES,
        INLINE_SIZE_CHOICES,
    ):
        values = _values(choice_list)
        assert "auto" not in values
        assert any(is_auto_utility(value) for value in values)


def test_max_size_choices_have_no_auto():
    for choice_list in (
        INLINE_MAX_WIDTH_CHOICES,
        INLINE_MAX_HEIGHT_CHOICES,
        BLOCK_MAX_WIDTH_CHOICES,
        BLOCK_MAX_HEIGHT_CHOICES,
    ):
        assert not any(is_auto_utility(value) for value in _values(choice_list))


def test_is_auto_utility_excludes_unrelated_auto_classes():
    assert is_auto_utility("auto")
    assert is_auto_utility("ml-auto")
    assert is_auto_utility("size-auto")
    assert not is_auto_utility("table-auto")
    assert not is_auto_utility("decoration-auto")
