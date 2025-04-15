"""Plugin declaration for nautobot_dns_models."""

from importlib import metadata

from nautobot.apps import ConstanceConfigItem, NautobotAppConfig

__version__ = metadata.version(__name__)


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
        "IPADDRESS_PANELS": ConstanceConfigItem(
            default={"forward": "always", "reverse": "always"},
            help_text="Show DNS Records panels in IP Address detailed view (always/if_present/never).",
            field_type="optional_json_field",
        ),
    }


config = NautobotDnsModelsConfig  # pylint:disable=invalid-name
