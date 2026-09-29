import pytest

from django.conf import settings


@pytest.fixture(autouse=True)
def temporary_media_dir(settings, tmp_path: pytest.TempdirFactory):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture(scope="session", autouse=True)
def wagtail_bootstrap(django_db_setup, django_db_blocker):
    """Seed reference data that Wagtail data migrations normally create.

    Tests run with ``--no-migrations`` (syncdb), so
    ``wagtailcore.0002_initial_data`` (root page/site),
    ``wagtailcore.0025_collection_initial_data`` (root collection) and the
    locale migration never run. Recreate the minimum they provide.
    """
    from wagtail.coreutils import get_supported_content_language_variant
    from wagtail.models import Collection, Locale, Page, Site

    with django_db_blocker.unblock():
        # ``Locale.get_default()`` normalises ``LANGUAGE_CODE`` to a supported
        # content-language variant (e.g. "en-us" -> "en"), so seed that exact
        # code or every implicit page locale lookup raises DoesNotExist.
        language_code = get_supported_content_language_variant(settings.LANGUAGE_CODE)
        Locale.all_objects.get_or_create(language_code=language_code)
        if not Page.objects.filter(depth=1).exists():
            root = Page.add_root(title="Root", slug="root")
            home = root.add_child(instance=Page(title="Welcome", slug="home"))
            Site.objects.get_or_create(
                hostname="localhost",
                defaults={"root_page": home, "is_default_site": True},
            )
        if not Collection.objects.filter(depth=1).exists():
            Collection.objects.create(name="Root", path="0001", depth=1, numchild=0)
    yield
