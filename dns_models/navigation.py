"""Menu items."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = (
    NavMenuItem(
        link="plugins:dns_models:dnszonemodel_list",
        name="Nautobot DNS Models",
        permissions=["dns_models.view_dnszonemodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:dns_models:dnszonemodel_add",
                permissions=["dns_models.add_dnszonemodel"],
            ),
        ),
    ),
)

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="Nautobot DNS Models", items=tuple(items)),),
    ),
)
