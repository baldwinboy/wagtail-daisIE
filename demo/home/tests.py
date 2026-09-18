from django.core.management import call_command
from django.test import override_settings
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import HomePage


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")

    def test_page_default_design_applies_to_body_blocks(self):
        self.homepage.page_design = [
            ("defaults", {"text": {"typography": {"text_color": "text-primary"}}})
        ]
        self.homepage.body = [
            {"type": "text", "value": {"text": "Hello", "design": {}}}
        ]
        self.homepage.save_revision().publish()

        response = self.client.get(self.homepage.url)
        content = response.content.decode()
        assert "text-primary" in content


@override_settings(MEDIA_ROOT="/tmp/wagtail-daisie-demo-test-media")
class LoadInitialDataTests(WagtailPageTestCase):
    """The demo loader reads demo/fixtures and is idempotent."""

    def setUp(self):
        from wagtail_daisIE.models import DaisyUITheme

        root_page = Page.get_first_root_node()
        if not Site.objects.filter(is_default_site=True).exists():
            Site.objects.create(
                hostname="testsite", root_page=root_page, is_default_site=True
            )
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)
        self.homepage.save_revision().publish()
        DaisyUITheme.objects.all().delete()

    def test_load_initial_data_seeds_content_and_is_idempotent(self):
        from wagtail_daisIE.models import DaisyUIMenu, DaisyUITheme

        call_command("load_initial_data")

        assert DaisyUITheme.objects.filter(default=True).exists()
        assert DaisyUIMenu.objects.filter(name="Main navigation").exists()
        assert DaisyUIMenu.objects.filter(name="Footer").exists()

        call_command("load_initial_data")

        assert DaisyUIMenu.objects.filter(name="Main navigation").count() == 1
        assert DaisyUIMenu.objects.filter(name="Footer").count() == 1
