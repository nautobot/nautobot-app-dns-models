"""Tables for nautobot_dns_models."""

import django_tables2 as tables
from nautobot.utilities.tables import BaseTable, ButtonsColumn, ToggleColumn

from nautobot_dns_models import models


class DnsZoneModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DnsZoneModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
        # pk_field="pk",
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DnsZoneModel
        fields = (
            "pk",
            "name",
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )


class NSRecordModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.NSRecordModel,
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
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )


class ARecordModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.ARecordModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.ARecordModel
        fields = (
            "pk",
            "name",
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )


class AAAARecordModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.AAAARecordModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.AAAARecordModel
        fields = (
            "pk",
            "name",
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )


class CNAMERecordModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.CNAMERecordModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.CNAMERecordModel
        fields = (
            "pk",
            "name",
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )


class MXRecordModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.MXRecordModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.MXRecordModel
        fields = (
            "pk",
            "name",
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )


class TXTRecordModelTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.TXTRecordModel,
        # Option for modifying the default action buttons on each row:
        # buttons=("changelog", "edit", "delete"),
        # Option for modifying the pk for the action buttons:
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.TXTRecordModel
        fields = (
            "pk",
            "name",
            "description",
        )

        # Option for modifying the columns that show up in the list view by default:
        # default_columns = (
        #     "pk",
        #     "name",
        #     "description",
        # )
