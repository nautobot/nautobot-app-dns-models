"""Menu items."""

from nautobot.extras.plugins import PluginMenuButton, PluginMenuItem
from nautobot.utilities.choices import ButtonColorChoices

menu_items = (
    PluginMenuItem(
        link="plugins:nautobot_dns_models:dnszonemodel_list",
        link_text="Nautobot DNS Models",
        permissions=["nautobot_dns_models.view_dnszonemodel"],
        buttons=(
            PluginMenuButton(
                link="plugins:nautobot_dns_models:dnszonemodel_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
                permissions=["nautobot_dns_models.add_dnszonemodel"],
            ),
        ),
    ),
)
