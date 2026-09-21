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
        from wagtail_daisIE.models import (
            Audience,
            DaisyUIMenu,
            DaisyUITheme,
            EmailTemplate,
            ErrorPage,
        )

        call_command("load_initial_data")

        assert DaisyUITheme.objects.filter(default=True).exists()
        assert DaisyUIMenu.objects.filter(name="Main navigation").exists()
        assert DaisyUIMenu.objects.filter(name="Footer").exists()
        assert Audience.objects.filter(name="Newsletter").exists()
        assert ErrorPage.objects.filter(status_code=403).exists()
        assert EmailTemplate.objects.filter(name="Account confirmation").exists()

        call_command("load_initial_data")

        assert DaisyUIMenu.objects.filter(name="Main navigation").count() == 1
        assert DaisyUIMenu.objects.filter(name="Footer").count() == 1
        assert Audience.objects.filter(name="Newsletter").count() == 1

    def test_showcase_pages_and_form(self):
        from blog.models import BreadSuggestion, BreadSuggestionFormPage
        from home.models import DemoPage

        call_command("load_initial_data")

        context_page = DemoPage.objects.get(slug="context-and-components")
        assert self.client.get(context_page.url).status_code == 200

        gated_page = DemoPage.objects.get(slug="members-only")
        assert self.client.get(gated_page.url).status_code == 403

        form_page = BreadSuggestionFormPage.objects.get(slug="suggest-a-bread")
        response = self.client.post(
            form_page.url,
            {"title": "Rye loaf", "description": "Dark rye please"},
            follow=True,
        )
        assert response.status_code == 200
        assert BreadSuggestion.objects.filter(
            title="Rye loaf", is_approved=False
        ).exists()

    def test_data_pages_and_basket(self):
        from blog.models import Bread
        from home.models import DemoPage

        call_command("load_initial_data")

        bread = Bread.objects.first()
        assert bread is not None

        breads_page = DemoPage.objects.get(slug="breads")
        response = self.client.get(breads_page.url)
        assert response.status_code == 200
        content = response.content.decode()
        assert bread.name in content
        assert "Add to basket" in content

        calendar_page = DemoPage.objects.get(slug="bread-calendar")
        response = self.client.get(calendar_page.url)
        assert response.status_code == 200
        assert "cally" in response.content.decode()

        response = self.client.post(
            "/daisie/actions/basket.add/", {"target": bread.pk}
        )
        assert response.status_code == 302
        content = self.client.get(breads_page.url).content.decode()
        assert bread.name in content

    def test_blog_index_feed_renders_posts(self):
        from blog.models import BlogIndexPage, BlogPage

        call_command("load_initial_data")

        index = BlogIndexPage.objects.first()
        post = BlogPage.objects.first()
        assert index is not None
        assert post is not None

        content = self.client.get(index.url).content.decode()
        assert post.title in content
