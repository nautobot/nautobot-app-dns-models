"""Menu items to the Nautobot navigation menu."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

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
        ),
    )
]

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="DNS", items=tuple(items)),),
    ),
)
