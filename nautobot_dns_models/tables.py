"""Tables for nautobot_dns_models."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, ToggleColumn
from nautobot.core.tables import (
    BaseTable,
    ButtonsColumn,
    LinkedCountColumn,
    ToggleColumn,
)
from nautobot.extras.tables import RoleTableMixin, StatusTableMixin
from nautobot.ipam.models import (
    Prefix,
)
from nautobot.ipam.tables import PREFIX_COPY_LINK
from nautobot.tenancy.tables import TenantColumn

from nautobot_dns_models import models


# class CustomPrefixTable(StatusTableMixin, RoleTableMixin, BaseTable):
#     pk = ToggleColumn()
#     prefix = tables.TemplateColumn(
#         template_code=PREFIX_COPY_LINK, attrs={"td": {"class": "text-nowrap"}}, order_by=("network", "prefix_length")
#     )
#     vrf_count = LinkedCountColumn(
#         viewname="ipam:vrf_list",
#         url_params={"prefix": "pk"},
#         # display_field="name",
#         reverse_lookup="prefixes",
#         verbose_name="VRFs",
#     )
#     views_count = LinkedCountColumn(
#         viewname="nautobot_dns_models:dns-view_list",
#         url_params={"prefix": "pk"},
#         # display_field="name",
#         reverse_lookup="prefixes",
#         verbose_name="DNS Views",
#     )
#     tenant = TenantColumn()
#     namespace = tables.Column(linkify=True)
#     vlan = tables.Column(linkify=True, verbose_name="VLAN")
#     rir = tables.Column(linkify=True)
#     children = tables.Column(accessor="descendants_count", orderable=False)
#     date_allocated = tables.DateTimeColumn()
#     location_count = LinkedCountColumn(
#         viewname="dcim:location_list",
#         url_params={"prefixes": "pk"},
#         # display_field="name",
#         verbose_name="Locations",
#     )
#     cloud_networks_count = LinkedCountColumn(
#         viewname="cloud:cloudnetwork_list", url_params={"prefixes": "pk"}, verbose_name="Cloud Networks"
#     )
#     actions = ButtonsColumn(Prefix)

#     class Meta(BaseTable.Meta):
#         model = Prefix
#         fields = (
#             "pk",
#             "prefix",
#             "type",
#             "status",
#             "children",
#             "vrf_count",
#             "views_count",
#             "namespace",
#             "tenant",
#             "location_count",
#             "cloud_networks_count",
#             "vlan",
#             "role",
#             "rir",
#             "date_allocated",
#             "description",
#             "actions",
#         )
#         default_columns = (
#             "pk",
#             "prefix",
#             "type",
#             "status",
#             "vrf_count",
#             "views_count",
#             "namespace",
#             "tenant",
#             "location_count",
#             "vlan",
#             "role",
#             "description",
#             "actions",
#         )
#         row_attrs = {
#             "class": lambda record: "success" if not record.present_in_database else "",
#         }


class DNSRecordTable(BaseTable):  # pylint: disable=nb-no-model-found
    """Base table for DNS records list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    zone = tables.LinkColumn()
    ttl = tables.Column(accessor="ttl", verbose_name="TTL")


class DNSViewTable(BaseTable):
    """Table for DNS View list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DNSView,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
        # pk_field="pk",
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSView
        fields = (
            "pk",
            "name",
            "description",
            "actions",
        )

        default_columns = (
            "pk",
            "name",
            "description",
            "actions",
        )


# class DNSViewPrefixAssignmentTable(BaseTable):
#     """Table for DNS View Prefix Assignment view."""


#     class Meta(BaseTable.Meta):
#         """Meta attributes."""

#         model = models.DNSView.prefixes.through
#         fields = (
#             "pk",
#             "prefix",
#             "actions",
#         )

#         default_columns = (
#             "pk",
#             "prefix",
#             "actions",
#         )


class DNSZoneTable(BaseTable):
    """Table for DNS Zone list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    dns_view = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DNSZone,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
        # pk_field="pk",
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSZone
        fields = (
            "pk",
            "name",
            "dns_view",
            "ttl",
            "filename",
            "description",
            "soa_expire",
            "soa_rname",
            "soa_refresh",
            "soa_retry",
            "soa_serial",
            "soa_minimum",
            "actions",
        )

        default_columns = ("pk", "name", "dns_view", "ttl", "filename", "soa_expire", "soa_rname", "actions")


class NSRecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.NSRecord,
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.NSRecord
        fields = (
            "pk",
            "name",
            "server",
            "zone",
            "description",
            "comment",
            "ttl",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "name",
            "server",
            "zone",
            "ttl",
            "actions",
        )


class ARecordTable(DNSRecordTable):
    """Table for list view."""

    address = tables.LinkColumn()
    actions = ButtonsColumn(
        models.ARecord,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.ARecord
        fields = (
            "pk",
            "name",
            "address",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "address",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class AAAARecordTable(DNSRecordTable):
    """Table for list view."""

    address = tables.LinkColumn()
    actions = ButtonsColumn(
        models.AAAARecord,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.AAAARecord
        fields = (
            "pk",
            "name",
            "address",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "address",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class CNAMERecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.CNAMERecord,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.CNAMERecord
        fields = (
            "pk",
            "name",
            "alias",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "alias",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class MXRecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.MXRecord,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.MXRecord
        fields = (
            "pk",
            "name",
            "mail_server",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "mail_server",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class TXTRecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.TXTRecord,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.TXTRecord
        fields = (
            "pk",
            "name",
            "text",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "text",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class PTRRecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.PTRRecord,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.PTRRecord
        fields = (
            "pk",
            "name",
            "ptrdname",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "ptrdname",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class SRVRecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.SRVRecord,
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.SRVRecord
        fields = (
            "pk",
            "name",
            "priority",
            "weight",
            "port",
            "target",
            "zone",
            "comment",
            "ttl",
            "description",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "priority",
            "weight",
            "port",
            "target",
            "zone",
            "actions",
        )
