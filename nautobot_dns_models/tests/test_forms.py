"""Tests for nautobot_dns_models Form Classes."""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import TestCase
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix
from nautobot.users.models import ObjectPermission

from nautobot_dns_models import forms
from nautobot_dns_models.choices import DNSZoneTypeChoices
from nautobot_dns_models.models import DNSRegistrar, DNSView, DNSZone, PTRRecord

User = get_user_model()


class DNSViewFormTestCase(TestCase):
    """Test DNSView forms."""

    form_class = forms.DNSViewForm

    @classmethod
    def setUpTestData(cls):
        active_status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        cls.prefix = Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, status=active_status)

    def test_specifying_all_fields_success(self):
        form = self.form_class(
            data={"name": "Test View", "description": "Test Description", "prefixes": [self.prefix.pk]}
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = self.form_class(data={"name": "Test View"})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_dnsview_is_required(self):
        form = self.form_class(data={"description": "Test Description"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])


class DNSZoneFormTestCase(TestCase):
    """Test DNSZone forms."""

    @classmethod
    def setUpTestData(cls):
        cls.dns_view = DNSView.objects.get(name="Default")
        cls.catalog_zone = DNSZone.objects.create(name="catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)

    def _zone_data(self, **overrides):
        """Return a valid DNSZoneForm payload, with any supplied overrides applied."""
        data = {
            "name": "Development",
            "type": DNSZoneTypeChoices.TYPE_PRIMARY,
            "dns_view": self.dns_view.id,
            "ttl": 1010101,
            "filename": "development.zone",
            "soa_mname": "ns1.example.com",
            "soa_rname": "admin@example.com",
            "soa_refresh": 10800,
            "soa_retry": 3600,
            "soa_expire": 604800,
            "soa_serial": 202,
            "soa_minimum": 3600,
        }
        data.update(overrides)
        return data

    def _user_permitted_to_change(self, *catalog_zones):
        """Return a user who may change only `catalog_zones`."""
        user = User.objects.create_user(username="zone-form-user")
        permission = ObjectPermission.objects.create(
            name="change some catalogs",
            actions=["change"],
            constraints={"pk__in": [str(zone.pk) for zone in catalog_zones]},
        )
        permission.object_types.set([ContentType.objects.get_for_model(DNSZone)])
        permission.users.add(user)
        return user

    def test_specifying_all_fields_success(self):
        registrar = DNSRegistrar.objects.create(
            name="Registrar One",
            portal_url="https://registrar.example",
            account_number="ACC-100",
        )
        form = forms.DNSZoneForm(
            data=self._zone_data(
                dns_registrar=registrar.id,
                description="Development Testing",
                expiration_date="2026-12-31",
                auto_renewal=True,
                registry_locked=True,
                transfer_locked=True,
                privacy_enabled=True,
                website_forwarding_enabled=True,
                renewal_term_months=24,
                dnssec_enabled=True,
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.DNSZoneForm(data=self._zone_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save())

    def test_soa_rname_accepts_value_without_at_sign(self):
        form = forms.DNSZoneForm(
            data=self._zone_data(
                name="Catalog",
                filename="catalog.zone",
                soa_mname="invalid.",
                soa_rname="invalid.",
            )
        )

        self.assertTrue(form.is_valid(), form.errors)
        # Single-label placeholder is stored without a trailing dot
        self.assertEqual(form.save().soa_rname, "invalid")

    def test_validate_name_dnszone_is_required(self):
        form = forms.DNSZoneForm(data={"ttl": "1010101"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])

    def test_name_case_variant_in_same_view_fails(self):
        DNSZone.objects.create(
            name="development",
            filename="development.zone",
            soa_mname="ns1.example.com",
            soa_rname="admin@example.com",
        )
        form = forms.DNSZoneForm(
            data={
                "name": "Development",
                "dns_view": DNSView.objects.get(name="Default").id,
                "ttl": 3600,
                "filename": "development.zone",
                "soa_mname": "ns1.example.com",
                "soa_rname": "admin@example.com",
                "soa_refresh": 10800,
                "soa_retry": 3600,
                "soa_expire": 604800,
                "soa_serial": 202,
                "soa_minimum": 3600,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "A DNS zone with this name (ignoring letter case) already exists in this view.", form.errors["name"]
        )

    def test_expiration_date_accepts_date_picker_value(self):
        form = forms.DNSZoneForm(data=self._zone_data(expiration_date="2026-12-31"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_can_create_catalog_zone(self):
        """The form creates a catalog zone."""
        form = forms.DNSZoneForm(data=self._zone_data(type=DNSZoneTypeChoices.TYPE_CATALOG))
        self.assertTrue(form.is_valid(), form.errors)
        zone = form.save()
        self.assertEqual(zone.type, DNSZoneTypeChoices.TYPE_CATALOG)

    def test_zone_type_is_disabled_when_editing(self):
        """The type field is disabled when editing a zone."""
        zone = DNSZone.objects.create(name="existing.example")
        form = forms.DNSZoneForm(instance=zone)
        self.assertTrue(form.fields["type"].disabled)

    def test_auto_create_ptr_is_disabled_when_editing_catalog_zone(self):
        """The `auto_create_ptr` field is disabled when editing a catalog zone."""
        form = forms.DNSZoneForm(instance=self.catalog_zone)
        self.assertTrue(form.fields["auto_create_ptr"].disabled)

    def test_auto_create_ptr_is_enabled_when_editing_primary_zone(self):
        """The `auto_create_ptr` field is enabled when editing a primary zone."""
        zone = DNSZone.objects.create(name="primary.example")
        form = forms.DNSZoneForm(instance=zone)
        self.assertFalse(form.fields["auto_create_ptr"].disabled)

    def test_the_catalog_field_offers_catalogs_in_the_chosen_view(self):
        """The catalog field offers catalog zones in the view chosen on the form."""
        query_params = forms.DNSZoneForm().fields["catalog_zone"].query_params
        self.assertEqual(query_params["type"], DNSZoneTypeChoices.TYPE_CATALOG)
        self.assertEqual(query_params["dns_view"], "$dns_view")

    def test_adding_to_a_catalog_publishes_the_zone(self):
        """Saving the form with a catalog zone adds the zone to it and publishes its PTR record."""
        form = forms.DNSZoneForm(data=self._zone_data(catalog_zone=self.catalog_zone.pk))
        self.assertTrue(form.is_valid(), form.errors)
        zone = form.save()

        self.assertEqual(zone.catalog_zone, self.catalog_zone)
        self.assertNotEqual(zone.member_label, "")
        self.assertTrue(PTRRecord.objects.filter(zone=self.catalog_zone, name=zone.ptr_record_name).exists())

    def test_removing_from_a_catalog_withdraws_the_zone(self):
        """Clearing the catalog field removes the zone from its catalog and withdraws its PTR record."""
        zone = DNSZone.objects.create(name="member.example", catalog_zone=self.catalog_zone)
        ptr_name = zone.ptr_record_name

        form = forms.DNSZoneForm(instance=zone, data=self._zone_data(name=zone.name, catalog_zone=""))
        self.assertTrue(form.is_valid(), form.errors)
        zone = form.save()

        self.assertIsNone(zone.catalog_zone)
        self.assertEqual(zone.member_label, "")
        self.assertFalse(PTRRecord.objects.filter(zone=self.catalog_zone, name=ptr_name).exists())

    def test_catalog_zone_is_disabled_when_editing_a_catalog_zone(self):
        """The catalog field is disabled when editing a catalog zone."""
        form = forms.DNSZoneForm(instance=self.catalog_zone)
        self.assertTrue(form.fields["catalog_zone"].disabled)

    def test_catalog_zone_is_enabled_when_editing_a_primary_zone(self):
        """The catalog field is enabled when editing a primary zone."""
        zone = DNSZone.objects.create(name="primary.example")
        form = forms.DNSZoneForm(instance=zone)
        self.assertFalse(form.fields["catalog_zone"].disabled)

    def test_the_catalog_field_asks_for_catalogs_the_user_can_change(self):
        """The catalog field asks for catalog zones the user may change."""
        query_params = forms.DNSZoneForm().fields["catalog_zone"].query_params
        self.assertEqual(query_params["can_change"], "True")

    def test_a_catalog_the_user_cannot_change_is_not_a_choice(self):
        """Given a user, only the catalog zones they may change are valid choices."""
        other_catalog = DNSZone.objects.create(name="other-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        user = self._user_permitted_to_change(self.catalog_zone)

        refused = forms.DNSZoneForm(data=self._zone_data(catalog_zone=other_catalog.pk), user=user)
        self.assertFalse(refused.is_valid())
        self.assertIn("catalog_zone", refused.errors)

        accepted = forms.DNSZoneForm(data=self._zone_data(catalog_zone=self.catalog_zone.pk), user=user)
        self.assertTrue(accepted.is_valid(), accepted.errors)

    def test_a_zone_in_a_catalog_the_user_cannot_change_stays_in_it(self):
        """The catalog field is disabled, so other edits save and the zone keeps its catalog."""
        zone = DNSZone.objects.create(name="member.example", catalog_zone=self.catalog_zone)
        user = self._user_permitted_to_change()

        form = forms.DNSZoneForm(
            instance=zone, data=self._zone_data(name=zone.name, description="Edited", catalog_zone=""), user=user
        )
        self.assertTrue(form.fields["catalog_zone"].disabled)
        self.assertTrue(form.is_valid(), form.errors)
        zone = form.save()

        self.assertEqual(zone.description, "Edited")
        self.assertEqual(zone.catalog_zone, self.catalog_zone)


def bulk_edit_form(zones, user=None, nullify=(), **data):
    """Return a bulk edit form posted for `zones`, with `zones` as its selection."""
    pks = [str(zone.pk) for zone in zones]
    posted = QueryDict(mutable=True)
    posted.setlist("pk", pks)
    posted.setlist("_nullify", list(nullify))
    for key, value in data.items():
        posted[key] = str(value)
    return forms.DNSZoneBulkEditForm(DNSZone, data=posted, selection=DNSZone.objects.filter(pk__in=pks), user=user)


class DNSZoneBulkEditFormTest(TestCase):
    """Test the DNSZone bulk edit form.

    Its catalog and PTR fields are judged against the zones the edit will reach and, given a user,
    against the catalog zones that user may change.
    """

    form_class = forms.DNSZoneBulkEditForm

    REFUSAL = "Some of the selected zones are in catalog zones you do not have permission to change."
    VIEW_MISMATCH = "The selected zones must be in the same view as the catalog zone."

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(
            name="bulk-rname.example",
            filename="bulk-rname.example.zone",
            soa_mname="ns1.bulk-rname.example.",
            soa_rname="admin@example.com",
        )
        cls.catalog_zone = DNSZone.objects.create(name="catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.other_catalog = DNSZone.objects.create(name="other-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG)
        cls.member = DNSZone.objects.create(name="member.example", catalog_zone=cls.catalog_zone)
        cls.other_member = DNSZone.objects.create(name="other-member.example", catalog_zone=cls.other_catalog)
        cls.zones = [DNSZone.objects.create(name=f"zone-{index}.example") for index in range(2)]
        cls.other_view = DNSView.objects.create(name="Other View")
        cls.other_view_zone = DNSZone.objects.create(name="other-view-zone.example", dns_view=cls.other_view)

        cls.user = User.objects.create_user(username="bulk-catalog-user")
        permission = ObjectPermission.objects.create(
            name="change all but other catalog",
            actions=["view", "change"],
            constraints={
                "pk__in": [str(zone.pk) for zone in (cls.catalog_zone, cls.member, cls.other_member, cls.zone)]
            },
        )
        permission.object_types.set([ContentType.objects.get_for_model(DNSZone)])
        permission.users.add(cls.user)

    def test_soa_rname_accepts_dns_style_mailbox(self):
        form = self.form_class(
            DNSZone,
            data={"pk": [self.zone.pk], "soa_rname": "admin.example.com"},
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.zone.soa_rname = form.cleaned_data["soa_rname"]
        self.zone.validated_save()
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.soa_rname, "admin@example.com")

    def test_soa_rname_accepts_single_label_placeholder(self):
        form = self.form_class(
            DNSZone,
            data={"pk": [self.zone.pk], "soa_rname": "invalid."},
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.zone.soa_rname = form.cleaned_data["soa_rname"]
        self.zone.validated_save()
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.soa_rname, "invalid")

    def test_soa_rname_rejects_invalid_value(self):
        form = self.form_class(
            DNSZone,
            data={"pk": [self.zone.pk], "soa_rname": "john.example"},
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.zone.soa_rname = form.cleaned_data["soa_rname"]
        with self.assertRaises(ValidationError) as context:
            self.zone.validated_save()
        self.assertIn("soa_rname", context.exception.message_dict)
        self.assertIn(
            "SOA RNAME must be a valid email address, a basic DNS-style mailbox with a fully qualified domain, "
            "or a single-label placeholder.",
            context.exception.message_dict["soa_rname"],
        )

    def test_the_catalog_can_be_nulled(self):
        """The catalog field can be set to null."""
        self.assertIn("catalog_zone", forms.DNSZoneBulkEditForm.Meta.nullable_fields)

    def test_a_selection_in_the_catalog_view_is_accepted(self):
        """A selection in the catalog zone's view is accepted."""
        form = bulk_edit_form(self.zones, catalog_zone=self.catalog_zone.pk)
        self.assertTrue(form.is_valid(), form.errors)

    def test_a_selection_in_one_view_narrows_the_catalog_field_to_it(self):
        """For a selection in one view, the catalog field offers only catalog zones in that view."""
        form = bulk_edit_form(self.zones)
        self.assertIn(
            str(self.catalog_zone.dns_view_id), form.fields["catalog_zone"].widget.attrs["data-query-param-dns_view"]
        )

    def test_a_zone_cannot_be_added_to_a_catalog_zone_in_a_different_view(self):
        """Zones cannot be added to a catalog zone in a different view."""
        other_view_catalog = DNSZone.objects.create(
            name="other-view-catalog.example", type=DNSZoneTypeChoices.TYPE_CATALOG, dns_view=self.other_view
        )
        form = bulk_edit_form(self.zones, catalog_zone=other_view_catalog.pk)
        self.assertFalse(form.is_valid())
        self.assertIn(self.VIEW_MISMATCH, form.errors["catalog_zone"])

    def test_a_selection_spanning_views_disables_the_field_but_keeps_set_null(self):
        """A selection spanning views disables the catalog field but still allows set null.

        No catalog zone can hold zones from two views, but removing them from their catalogs still works.
        """
        form = bulk_edit_form([*self.zones, self.other_view_zone], catalog_zone=self.catalog_zone.pk)
        self.assertTrue(form.fields["catalog_zone"].disabled)
        self.assertIn("catalog_zone", form.nullable_fields)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["catalog_zone"])

    def test_moving_the_selection_into_the_catalog_view_is_accepted(self):
        """Moving the selection into the catalog zone's view is accepted.

        The view submitted with the edit is the one the zones will be in, so it is checked instead of
        their current views.
        """
        form = bulk_edit_form(
            [self.other_view_zone],
            catalog_zone=self.catalog_zone.pk,
            dns_view=self.catalog_zone.dns_view_id,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_moving_the_selection_out_of_the_catalog_view_is_refused(self):
        """Moving the selection out of the catalog zone's view is refused."""
        form = bulk_edit_form(self.zones, catalog_zone=self.catalog_zone.pk, dns_view=self.other_view.pk)
        self.assertFalse(form.is_valid())
        self.assertIn(self.VIEW_MISMATCH, form.errors["catalog_zone"])

    def test_a_selection_holding_a_catalog_zone_disables_the_field(self):
        """A selection that includes a catalog zone disables the catalog field.

        A catalog zone cannot be added to a catalog, and one refusal would roll back the whole batch.
        """
        form = bulk_edit_form([self.zones[0], self.catalog_zone], catalog_zone=self.catalog_zone.pk)
        self.assertTrue(form.fields["catalog_zone"].disabled)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["catalog_zone"])

    def test_a_selection_holding_a_catalog_zone_disables_auto_create_ptr(self):
        """A selection that includes a catalog zone disables `auto_create_ptr`, so a submitted value is ignored.

        A catalog zone cannot enable automatic PTR creation, and one refusal would roll back the whole batch.
        """
        form = bulk_edit_form([self.zones[0], self.catalog_zone], auto_create_ptr=True)
        self.assertTrue(form.fields["auto_create_ptr"].disabled)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["auto_create_ptr"])

    def test_a_selection_without_a_catalog_zone_keeps_auto_create_ptr(self):
        """A selection without a catalog zone keeps `auto_create_ptr` editable."""
        form = bulk_edit_form(self.zones, auto_create_ptr=True)
        self.assertFalse(form.fields["auto_create_ptr"].disabled)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["auto_create_ptr"])

    def test_a_selection_holding_a_catalog_zone_withdraws_set_null(self):
        """A selection that includes a catalog zone cannot set the catalog field to null.

        Set null on a disabled field would still be applied, so it is withdrawn with the field.
        """
        form = bulk_edit_form([self.zones[0], self.catalog_zone])
        self.assertNotIn("catalog_zone", form.nullable_fields)
        self.assertIn("catalog_zone", forms.DNSZoneBulkEditForm.Meta.nullable_fields)

    def test_the_catalog_field_offers_only_catalogs_the_user_can_change(self):
        """The catalog field offers only catalog zones the user can change."""
        form = bulk_edit_form([self.zone], user=self.user)
        self.assertEqual(list(form.fields["catalog_zone"].queryset), [self.catalog_zone])

    def test_adding_to_a_catalog_the_user_can_change_is_accepted(self):
        """Adding zones to a catalog zone the user can change is accepted."""
        form = bulk_edit_form([self.zone], user=self.user, catalog_zone=self.catalog_zone.pk)
        self.assertTrue(form.is_valid(), form.errors)

    def test_moving_zones_out_of_a_catalog_the_user_cannot_change_is_refused(self):
        """Moving zones out of a catalog zone the user cannot change is refused."""
        form = bulk_edit_form([self.zone, self.other_member], user=self.user, catalog_zone=self.catalog_zone.pk)
        self.assertFalse(form.is_valid())
        self.assertIn(self.REFUSAL, form.errors["catalog_zone"])

    def test_nulling_zones_in_a_catalog_the_user_cannot_change_is_refused(self):
        """Setting the catalog to null for zones in a catalog the user cannot change is refused."""
        form = bulk_edit_form([self.member, self.other_member], user=self.user, nullify=["catalog_zone"])
        self.assertFalse(form.is_valid())
        self.assertIn(self.REFUSAL, form.errors["catalog_zone"])

    def test_nulling_zones_in_a_catalog_the_user_can_change_is_accepted(self):
        """Setting the catalog to null for zones in a catalog the user can change is accepted."""
        form = bulk_edit_form([self.member, self.zone], user=self.user, nullify=["catalog_zone"])
        self.assertTrue(form.is_valid(), form.errors)


class DNSRegistrarFormTestCase(TestCase):
    """Test DNSRegistrar forms."""

    form_class = forms.DNSRegistrarForm

    def test_specifying_all_fields_success(self):
        form = self.form_class(
            data={
                "name": "Registrar Test",
                "portal_url": "https://registrar.test",
                "account_number": "REG-100",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = self.form_class(data={"name": "Registrar Required"})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_is_required(self):
        form = self.form_class(data={"portal_url": "https://registrar.test"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])


class NSRecordFormTestCase(TestCase):
    """Test NSRecord forms."""

    form_class = forms.NSRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_all_fields_success(self):
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
            "description": "Development Testing",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_zone_is_required(self):
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("This field is required.", form.errors["zone"])

    # Testing the record `enabled` field here. If it works for NSRecord, it works for all other record types.
    def test_enabled_is_checked_by_default(self):
        """A new record form offers `enabled` pre-checked, matching the model default."""
        self.assertTrue(self.form_class().fields["enabled"].initial)

    def test_enabled_can_be_unchecked(self):
        """Submitting the form without `enabled` saves a disabled record."""
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.save().enabled)

    def test_enabled_can_be_checked(self):
        """Submitting the form with `enabled` saves an enabled record."""
        data = {
            "name": "ns-record",
            "server": "ns-record-server",
            "ttl": 3600,
            "zone": self.dns_zone,
            "enabled": True,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save().enabled)


class ARecordFormTestCase(TestCase):
    """Test ARecord forms."""

    form_class = forms.ARecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.0.0.0/24", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="10.0.0.1/32", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "a-record",
            "ip_address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "a-record",
            "ip_address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
            "comment": "example-comment",
            "description": "this is Gerasimo's description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_ip_address_obj_is_required(self):
        data = {
            "name": "a-record",
            "ip_address": "10.10.10.0/32",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("not a valid UUID.", form.errors["ip_address"][0])

    def test_ip_address_label(self):
        form = self.form_class()
        self.assertEqual(form.fields["ip_address"].label, "IP Address")


class AAAARecordFormTestCase(TestCase):
    """Test AAAARecord forms."""

    form_class = forms.AAAARecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="2001:db8:abcd:12::/64", namespace=namespace, type="Pool", status=status)
        cls.ip_address = IPAddress.objects.create(address="2001:db8:abcd:12::1/128", namespace=namespace, status=status)

    def test_specifying_only_required_success(self):
        data = {
            "name": "aaaa-record",
            "ip_address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "aaaa-record",
            "ip_address": self.ip_address,
            "ttl": 3600,
            "zone": self.dns_zone,
            "comment": "example-comment",
            "description": "this is Gerasimo's description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_ip_address_obj_is_required(self):
        data = {
            "name": "aaaa-record",
            "ip_address": "10.10.10.0/32",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

    def test_ip_address_label(self):
        form = self.form_class()
        self.assertEqual(form.fields["ip_address"].label, "IP Address")


class CNAMERecordFormTestCase(TestCase):
    """Test CNAMERecord forms."""

    form_class = forms.CNAMERecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "cname-record",
            "alias": "cname-alias",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "cname-record",
            "alias": "cname-alias",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is a cname description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class MXRecordFormTestCase(TestCase):
    """Test MXRecord forms."""

    form_class = forms.MXRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "mx-record",
            "preference": 10,
            "mail_server": "mail-server.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "mx-record",
            "preference": 10,
            "mail_server": "mail-server.com",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class TXTRecordFormTestCase(TestCase):
    """Test TXTRecord forms."""

    form_class = forms.TXTRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "txt-record",
            "text": "spf record",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "txt-record",
            "text": "spf record",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_accepts_dkim_key_longer_than_256_characters(self):
        data = {
            "name": "dkim",
            "text": "v=DKIM1; k=rsa; p=" + "A" * 582,
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save())

    def test_rejects_quoted_character_string_over_255_octets(self):
        data = {
            "name": "txt-record",
            "text": '"' + "a" * 300 + '"',
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)


class PTRRecordFormTestCase(TestCase):
    """Test PTRRecord forms."""

    form_class = forms.PTRRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "ptr-record",
            "ptrdname": "ptr-record",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "ptr-record",
            "ptrdname": "ptr-record",
            "ttl": 3600,
            "comment": "example-comment",
            "zone": self.dns_zone,
            "description": "this is a boring description",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class SRVRecordFormTestCase(TestCase):
    """Test SRVRecord forms."""

    form_class = forms.SRVRecordForm

    @classmethod
    def setUpTestData(cls):
        cls.dns_zone = DNSZone.objects.create(name="example.com")

    def test_specifying_only_required_success(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_all_fields_success(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
            "description": "this is an srv description",
            "comment": "example-comment",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_priority_range(self):
        data = {
            "name": "srv-record",
            "priority": 65536,  # Invalid priority (max is 65535)
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is less than or equal to 65535.", form.errors["priority"])

    def test_validate_weight_range(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 65536,  # Invalid weight (max is 65535)
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is less than or equal to 65535.", form.errors["weight"])

    def test_validate_port_range(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 65536,  # Invalid port (max is 65535)
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is less than or equal to 65535.", form.errors["port"])

    def test_zone_is_required(self):
        data = {
            "name": "srv-record",
            "priority": 10,
            "weight": 5,
            "port": 8080,
            "target": "server.example.com",
            "ttl": 3600,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["zone"])

    def test_validate_negative_values(self):
        data = {
            "name": "srv-record",
            "priority": -1,  # Invalid priority (min is 0)
            "weight": -1,  # Invalid weight (min is 0)
            "port": -1,  # Invalid port (min is 0)
            "target": "server.example.com",
            "ttl": 3600,
            "zone": self.dns_zone,
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertIn("Ensure this value is greater than or equal to 0.", form.errors["priority"])
        self.assertIn("Ensure this value is greater than or equal to 0.", form.errors["weight"])
        self.assertIn("Ensure this value is greater than or equal to 0.", form.errors["port"])
