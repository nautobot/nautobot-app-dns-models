"""Menu items to the Nautobot navigation menu."""

from nautobot.apps.ui import (
    NavigationWeightChoices,
    NavMenuGroup,
    NavMenuItem,
    NavMenuTab,
)

menu_items = (
    NavMenuTab(
        name="DNS",
        icon="bus-globe",
        weight=NavigationWeightChoices.IPAM + 10,
        groups=(
            NavMenuGroup(
                name="Zones",
                weight=300,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_dns_models:dnszone_list",
                        name="DNS Zones",
                        weight=100,
                        permissions=["nautobot_dns_models.view_dnszone"],
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_dns_models:dnsview_list",
                        name="DNS Views",
                        weight=200,
                        permissions=["nautobot_dns_models.view_dnsview"],
                    ),
                ),
            ),
            NavMenuGroup(
                name="Registration",
                weight=300,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_dns_models:dnsregistrar_list",
                        name="DNS Registrars",
                        weight=300,
                        permissions=["nautobot_dns_models.view_dnsregistrar"],
                    ),
                ),
            ),
        ),
    ),
)
