from django.conf import settings


SETTING_NAME = "WAGTAIL_DAISIE_APPROVAL_WORKFLOWS"


def get_workflow_config():
    return getattr(settings, SETTING_NAME, {}) or {}
