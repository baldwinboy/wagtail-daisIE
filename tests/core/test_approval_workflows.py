import pytest

from wagtail_daisIE.approval.bridges import connect_signals, disconnect_signals
from wagtail_daisIE.approval.registry import (
    get_workflows,
    reset_workflows,
    workflow_for_instance,
)
from wagtail_daisIE.test.models import ApprovalSource, ApprovalTarget


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _workflows(settings):
    settings.WAGTAIL_DAISIE_APPROVAL_WORKFLOWS = {
        "source": {
            "label": "Source",
            "model": "wagtail_daisIE_test.ApprovalSource",
            "approval_field": "is_approved",
            "handler": "wagtail_daisIE.test.approval.approve_source",
            "converted_field": "converted",
        }
    }
    reset_workflows()
    disconnect_signals()
    connect_signals()
    yield
    disconnect_signals()
    reset_workflows()


class TestRegistry:
    def test_builds_and_matches(self):
        assert "source" in get_workflows()
        source = ApprovalSource(name="Rye")
        assert workflow_for_instance(source).key == "source"


class TestConversion:
    def test_approval_creates_target_once(self):
        source = ApprovalSource.objects.create(name="Rye loaf")
        assert source.converted is None

        source.is_approved = True
        source.save()
        source.refresh_from_db()
        assert source.converted is not None
        assert source.converted.name == "Rye loaf"

        source.save()
        assert ApprovalTarget.objects.count() == 1

    def test_unapproved_source_does_not_convert(self):
        ApprovalSource.objects.create(name="Sourdough")
        assert ApprovalTarget.objects.count() == 0
