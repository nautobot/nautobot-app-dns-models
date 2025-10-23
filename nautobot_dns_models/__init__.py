"""App declaration for nautobot_dns_models."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotDnsModelsConfig(NautobotAppConfig):
    """App configuration for the nautobot_dns_models app."""

    name = "nautobot_dns_models"
    verbose_name = "Nautobot DNS Models"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot DNS Models."
    base_url = "dns"
    required_settings = []
    default_settings = {}
    docs_view_name = "plugins:nautobot_dns_models:docs"
    searchable_models = ["dnszone"]


config = NautobotDnsModelsConfig  # pylint:disable=invalid-name
