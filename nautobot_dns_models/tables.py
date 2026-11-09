"""Tables for nautobot_dns_models."""

import django_tables2 as tables
from django.db.models import BooleanField, Exists, ExpressionWrapper, OuterRef, Q, QuerySet
from django.template.defaultfilters import truncatechars
from django.utils.html import format_html
from nautobot.apps.tables import BaseTable, BooleanColumn, ButtonsColumn, ToggleColumn
from nautobot.tenancy.tables import TenantColumn

from nautobot_dns_models import models
from nautobot_dns_models.choices import DNSZoneTypeChoices

DNSZONE_CATALOG_BUTTONS = """
{% if record.user_can_change and not record.is_catalog_zone %}
    {% if record.catalog_zone_id %}
        {% if record.user_can_change_catalog %}
            <li>
                <a href="{% url 'plugins:nautobot_dns_models:dnszone_remove_from_catalog' pk=record.pk %}?return_url={{ request.path }}" class="dropdown-item text-danger">
                    <span class="mdi mdi-folder-minus-outline me-4" aria-hidden="true"></span>Remove from Catalog
                </a>
            </li>
        {% endif %}
    {% elif record.user_has_catalog_in_view %}
        <li>
            <a href="{% url 'plugins:nautobot_dns_models:dnszone_add_to_catalog' pk=record.pk %}?return_url={{ request.path }}" class="dropdown-item text-success">
                <span class="mdi mdi-folder-plus-outline me-4" aria-hidden="true"></span>Add to Catalog
            </a>
        </li>
    {% endif %}
{% endif %}
"""


def annotate_catalog_actions(queryset, user):
    """Annotate each zone with what `user` may do with its catalog membership.

    `user_can_change` covers the zone itself, `user_can_change_catalog` the catalog zone holding it,
    and `user_has_catalog_in_view` whether any catalog zone in its view could take it.
    """
    changeable = models.DNSZone.objects.restrict(user, "change")
    # Uncorrelated, so the database finds the views once per query rather than once per row.
    catalog_view_ids = changeable.filter(type=DNSZoneTypeChoices.TYPE_CATALOG).values("dns_view_id")
    return queryset.annotate(
        user_can_change=Exists(changeable.filter(pk=OuterRef("pk"))),
        user_can_change_catalog=Exists(changeable.filter(pk=OuterRef("catalog_zone_id"))),
        user_has_catalog_in_view=ExpressionWrapper(Q(dns_view_id__in=catalog_view_ids), output_field=BooleanField()),
    )


class CatalogActionsTableMixin:
    """Offer catalog actions only on rows where the table's user may carry them out."""

    def __init__(self, data, *args, user=None, **kwargs):
        """Annotate `data` for the catalog action menu items; without a user they stay hidden."""
        if user is not None and isinstance(data, QuerySet):
            data = annotate_catalog_actions(data, user)
        super().__init__(data, *args, user=user, **kwargs)


class TruncatedTextColumn(tables.Column):
    """Render a long text value truncated, with the full value available as a tooltip.

    TXT record content can be up to 65535 octets (RFC 1035 §3.3.14), which would otherwise break the
    list view layout.
    """

    def __init__(self, *args, truncate_chars=64, **kwargs):
        """Store the truncation length."""
        super().__init__(*args, **kwargs)
        self.truncate_chars = truncate_chars

    def render(self, value):
        """Truncate the rendered value, keeping the full text in the cell's title attribute."""
        if not value:
            return self.default
        truncated = truncatechars(value, self.truncate_chars)
        if truncated == value:
            return value
        return format_html('<span title="{}">{}</span>', value, truncated)


class DNSRecordTable(BaseTable):  # pylint: disable=nb-no-model-found
    """Base table for DNS records list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    zone = tables.LinkColumn()
    ttl = tables.Column(accessor="ttl", verbose_name="TTL", orderable=False)
    enabled = BooleanColumn()


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


class DNSRegistrarTable(BaseTable):
    """Table for DNS Registrar list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DNSRegistrar,
        buttons=("changelog", "edit", "delete"),
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSRegistrar
        fields = (
            "pk",
            "name",
            "portal_url",
            "account_number",
            "actions",
        )

        default_columns = (
            "pk",
            "name",
            "portal_url",
            "account_number",
            "actions",
        )


class DNSRegistrationTable(BaseTable):
    """Table for DNS Registration list view."""

    pk = ToggleColumn()
    dns_registrar = tables.Column(linkify=True)
    dns_zone = tables.Column(linkify=True)
    status = tables.Column(linkify=True)
    actions = ButtonsColumn(
        models.DNSRegistration,
        buttons=("changelog", "edit", "delete"),
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSRegistration
        fields = (
            "pk",
            "dns_registrar",
            "dns_zone",
            "status",
            "expiration_date",
            "auto_renewal",
            "registry_locked",
            "transfer_locked",
            "privacy_enabled",
            "website_forwarding_enabled",
            "renewal_term_months",
            "dnssec_enabled",
            "actions",
        )

        default_columns = (
            "pk",
            "dns_registrar",
            "dns_zone",
            "status",
            "expiration_date",
            "auto_renewal",
            "actions",
        )


class DNSZoneTable(CatalogActionsTableMixin, BaseTable):
    """Table for DNS Zone list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    tenant = TenantColumn()
    dns_view = tables.Column(linkify=True)
    catalog_zone = tables.Column(linkify=True, verbose_name="Catalog Zone")
    enabled = BooleanColumn()
    auto_create_ptr = BooleanColumn()
    actions = ButtonsColumn(
        models.DNSZone,
        buttons=("changelog", "edit", "delete"),
        prepend_template=DNSZONE_CATALOG_BUTTONS,
    )

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSZone
        fields = (
            "pk",
            "name",
            "type",
            "dns_view",
            "catalog_zone",
            "member_label",
            "enabled",
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
            "auto_create_ptr",
            "actions",
        )

        default_columns = (
            "pk",
            "name",
            "type",
            "dns_view",
            "catalog_zone",
            "enabled",
            "ttl",
            "filename",
            "soa_expire",
            "soa_rname",
            "actions",
        )


class CatalogMemberZoneTable(CatalogActionsTableMixin, BaseTable):  # pylint: disable=nb-sub-class-name
    """Table of the member zones on a catalog zone's detail page."""

    name = tables.Column(linkify=True, verbose_name="Member Zone")
    ptr_record_name = tables.Column(
        accessor="ptr_record_name", order_by=("member_label",), verbose_name="PTR Record Name"
    )
    actions = ButtonsColumn(models.DNSZone, buttons=("edit",), prepend_template=DNSZONE_CATALOG_BUTTONS)

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.DNSZone
        fields = ("name", "ptr_record_name", "actions")
        default_columns = ("name", "ptr_record_name", "actions")


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
            "enabled",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "name",
            "server",
            "zone",
            "ttl",
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "preference",
            "zone",
            "comment",
            "ttl",
            "description",
            "enabled",
            "actions",
        )

        # Option for modifying the columns that show up in the list view by default:
        default_columns = (
            "pk",
            "name",
            "mail_server",
            "preference",
            "zone",
            "comment",
            "ttl",
            "enabled",
            "actions",
        )


class TXTRecordTable(DNSRecordTable):
    """Table for list view."""

    text = TruncatedTextColumn()
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
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
            "enabled",
            "actions",
        )
