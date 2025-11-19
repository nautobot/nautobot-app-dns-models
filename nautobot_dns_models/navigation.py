"""Menu items to the Nautobot navigation menu."""

from nautobot.apps.ui import (
    NavigationIconChoices,
    NavigationWeightChoices,
    NavMenuGroup,
    NavMenuItem,
    NavMenuTab,
)

menu_items = (
    NavMenuTab(
        name="Apps",
        icon=NavigationIconChoices.APPS,
        weight=NavigationWeightChoices.APPS,
        groups=(
            NavMenuGroup(
                name="DNS",
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
        ),
    ),
)
