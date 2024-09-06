"""Menu items to the Nautobot navigation menu."""

from nautobot.apps.ui import NavMenuButton, NavMenuItem, NavMenuTab, NavMenuGroup, NavMenuAddButton
from nautobot.core.choices import ButtonColorChoices


items = [
    NavMenuItem(
        link="plugins:nautobot_dns_models:nsrecordmodel_list",
        name="NS Records",
        permissions=["nautobot_dns_models.view_nsrecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:nsrecordmodel_add",
                permissions=["nautobot_dns_models.add_nsrecordmodel"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:nautobot_dns_models:arecordmodel_list",
        name="A Records",
        permissions=["nautobot_dns_models.view_arecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:arecordmodel_add",
                permissions=["nautobot_dns_models.add_arecordmodel"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:nautobot_dns_models:aaaarecordmodel_list",
        name="AAAA Records",
        permissions=["nautobot_dns_models.view_aaaarecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:aaaarecordmodel_add",
                permissions=["nautobot_dns_models.add_aaaarecordmodel"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:nautobot_dns_models:cnamerecordmodel_list",
        name="CNAME Records",
        permissions=["nautobot_dns_models.view_cnamerecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:cnamerecordmodel_add",
                permissions=["nautobot_dns_models.add_cnamerecordmodel"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:nautobot_dns_models:mxrecordmodel_list",
        name="MX Records",
        permissions=["nautobot_dns_models.view_mxrecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:mxrecordmodel_add",
                permissions=["nautobot_dns_models.add_mxrecordmodel"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:nautobot_dns_models:txtrecordmodel_list",
        name="TXT Records",
        permissions=["nautobot_dns_models.view_txtrecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:txtrecordmodel_add",
                permissions=["nautobot_dns_models.add_txtrecordmodel"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:nautobot_dns_models:ptrrecordmodel_list",
        name="PTR Records",
        permissions=["nautobot_dns_models.view_ptrrecordmodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_dns_models:ptrrecordmodel_add",
                permissions=["nautobot_dns_models.add_ptrrecordmodel"],
            ),
        ),
    ),
]

menu_items = (
    NavMenuTab(
        name="DNS Models",
        groups=(
            NavMenuGroup(
                name="DNS Zones",
                items=(
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
                    ),
                ),
            ),
            NavMenuGroup(name="DNS Records", items=tuple(items)),
        ),
    ),
)
