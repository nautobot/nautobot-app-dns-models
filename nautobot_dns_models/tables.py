"""Tables for nautobot_dns_models."""

import django_tables2 as tables
from nautobot.core.tables import BaseTable, ButtonsColumn, ToggleColumn

from nautobot_dns_models import models
from nautobot_dns_models.template_code import DNS_RECORDS_NAME, DNS_RECORDS_TYPE, DNS_RECORDS_VALUE, DNS_RECORDS_ACTIONS


class DNSZoneModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DNSZoneModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
        # pk_field="pk",
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSZoneModel
        fields = (
            "pk",
            "name",
            "ttl",
            "filename",
            "description",
            "soa_expire",
            "soa_rname",
            "soa_refresh",
            "soa_retry",
            "soa_serial",
            "soa_minimum",
        )

        default_columns = (
            "pk",
            "name",
            "ttl",
            "filename",
            "soa_expire",
            "soa_rname",
        )


class RecordsTable(tables.Table):
    """Table for DNS Zone records list view."""

    pk = ToggleColumn()

    type_ = tables.TemplateColumn(template_code=DNS_RECORDS_TYPE, verbose_name="Type", orderable=False)
    name = tables.TemplateColumn(template_code=DNS_RECORDS_NAME, verbose_name="Name", orderable=False)

    value = tables.TemplateColumn(
        template_code=DNS_RECORDS_VALUE,
        verbose_name="Value",
        orderable=False,
    )
    description = tables.TemplateColumn(
        template_code="""{{ record.description }}""", verbose_name="Description", orderable=False
    )
    actions = tables.TemplateColumn(template_code=DNS_RECORDS_ACTIONS, verbose_name="Actions", orderable=False)

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        fields = (
            "type_",
            "name",
            "value",
            "description",
            "actions",
        )
        default_columns = (
            "type_",
            "name",
            "value",
            "description",
            "actions",
        )


class NSRecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.NSRecordModel,
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.NSRecordModel
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
            "ttl," "actions",
        )


class ARecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.ARecordModel,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.ARecordModel
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


class AAAARecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.AAAARecordModel,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.AAAARecordModel
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


class CNAMERecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.CNAMERecordModel,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.CNAMERecordModel
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


class MXRecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.MXRecordModel,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.MXRecordModel
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


class TXTRecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.TXTRecordModel,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.TXTRecordModel
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


class PTRRecordModelTable(BaseTable):  # pylint: disable=too-few-public-methods
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.PTRRecordModel,
        # Option for modifying the default action buttons on each row:
        buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.PTRRecordModel
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
