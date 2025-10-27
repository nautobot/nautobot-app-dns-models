"""Tables for nautobot_dns_models."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, ButtonsColumn, ToggleColumn
from nautobot.tenancy.tables import TenantColumn

from nautobot_dns_models import models


class DNSRecordTable(BaseTable):  # pylint: disable=nb-no-model-found
    """Base table for DNS records list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    zone = tables.LinkColumn()
    ttl = tables.Column(accessor="ttl", verbose_name="TTL", orderable=False)


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


class DNSZoneTable(BaseTable):
    """Table for DNS Zone list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    tenant = TenantColumn()
    dns_view = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DNSZone,
        buttons=("changelog", "edit", "delete"),
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
            "tenant",
            "actions",
        )

        default_columns = ("pk", "name", "dns_view", "ttl", "filename", "soa_expire", "soa_rname", "actions")


class NSRecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.NSRecord,
        buttons=("changelog", "edit", "delete"),
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

    ip_address = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.ARecord,
        buttons=("changelog", "edit", "delete"),
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.ARecord
        fields = (
            "pk",
            "name",
            "ip_address",
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
            "ip_address",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class AAAARecordTable(DNSRecordTable):
    """Table for list view."""

    ip_address = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.AAAARecord,
        buttons=("changelog", "edit", "delete"),
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.AAAARecord
        fields = (
            "pk",
            "name",
            "ip_address",
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
            "ip_address",
            "zone",
            "comment",
            "ttl",
            "actions",
        )


class CNAMERecordTable(DNSRecordTable):
    """Table for list view."""

    actions = ButtonsColumn(
        models.CNAMERecord,
        buttons=("changelog", "edit", "delete"),
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
        buttons=("changelog", "edit", "delete"),
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
        buttons=("changelog", "edit", "delete"),
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
        buttons=("changelog", "edit", "delete"),
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
