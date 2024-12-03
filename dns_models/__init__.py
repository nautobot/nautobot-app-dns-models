"""App declaration for dns_models."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotDnsModelsConfig(NautobotAppConfig):
    """App configuration for the dns_models app."""

    name = "dns_models"
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
    docs_view_name = "plugins:dns_models:docs"


config = NautobotDnsModelsConfig  # pylint:disable=invalid-name
