"""Menu items to the Nautobot navigation menu."""

from nautobot.apps.ui import NavMenuButton, NavMenuItem, NavMenuTab, NavMenuGroup, NavMenuAddButton
from nautobot.core.choices import ButtonColorChoices


items = [
    NavMenuItem(
        link="plugins:nautobot_dns_models:dnszonemodel_list",
        name="DNS Zones",
        permissions=["nautobot_dns_models.view_dnszonemodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:dnszonemodel_add",
                permissions=["nautobot_dns_models.add_dnszonemodel"],
            ),
        )
    )
]

menu_items = (
    NavMenuTab(
        name="Plugins",
        groups=(NavMenuGroup(name="Nautobot DNS Models", items=tuple(items)),),
    ),
)