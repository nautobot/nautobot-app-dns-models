"""Plugin declaration for nautobot_dns_models."""

from importlib import metadata

from django.conf import settings
from nautobot.apps import ConstanceConfigItem, NautobotAppConfig

__version__ = metadata.version(__name__)

constance_additional_fields = {
    "show_dns_panel": [
        "django.forms.fields.ChoiceField",
        {
            "widget": "django.forms.Select",
            "choices": [
                ("always", "Always"),
                ("if_present", "If records are present"),
                ("never", "Never"),
            ],
        },
    ],
}

# pylint:disable=no-member
settings.CONSTANCE_ADDITIONAL_FIELDS |= constance_additional_fields


class NautobotDnsModelsConfig(NautobotAppConfig):
    """Plugin configuration for the nautobot_dns_models plugin."""

    name = "nautobot_dns_models"
    verbose_name = "Nautobot DNS Models"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot DNS Models."
    base_url = "dns"
    required_settings = []
    min_version = "2.4.0"
    max_version = "2.9999"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_dns_models:docs"

    constance_config = {
        "SHOW_FORWARD_PANEL": ConstanceConfigItem(
            default="Always",
            help_text="Show A/AAAA Records panel in IP Address detailed view.",
            field_type="show_dns_panel",
        ),
        "SHOW_REVERSE_PANEL": ConstanceConfigItem(
            default="Always",
            help_text="Show PTR Records panel in IP Address detailed view.",
            field_type="show_dns_panel",
        ),
    }


config = NautobotDnsModelsConfig  # pylint:disable=invalid-name
