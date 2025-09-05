"""Menu items to the Nautobot navigation menu."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = [
    NavMenuItem(
        link="plugins:nautobot_dns_models:dnszone_list",
        name="DNS Zones",
        permissions=["nautobot_dns_models.view_dnszone"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:dnszone_add",
                permissions=["nautobot_dns_models.add_dnszone"],
            ),
        ),
    )
]

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="DNS", items=tuple(items)),),
    ),
)
