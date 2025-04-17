"""Plugin declaration for nautobot_dns_models."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.apps import NautobotAppConfig


class NautobotDnsModelsConfig(NautobotAppConfig):
    """Plugin configuration for the nautobot_dns_models plugin."""

    name = "nautobot_dns_models"
    verbose_name = "Nautobot DNS Models"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot DNS Models."
    base_url = "dns"
    required_settings = []
    min_version = "3.0.0a1"  # TODO: Update to 3.0.0 when Nautobot v3.0.0 is released
    max_version = "3.9999"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_dns_models:docs"


config = NautobotDnsModelsConfig  # pylint:disable=invalid-name
