"""Tests for SOA serial auto-increment."""

from constance.test import override_config
from django.db import connection, transaction
from django.test import TransactionTestCase
from nautobot.apps.testing import TestCase
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from nautobot_dns_models.models import (
    AAAARecord,
    ARecord,
    CNAMERecord,
    DNSZone,
    MXRecord,
    NSRecord,
    PTRRecord,
    SRVRecord,
    TXTRecord,
    _reset_dirty_zones_for_testing,
)


def _refresh_serial(zone):
    """Reload zone from DB and return soa_serial."""
    zone.refresh_from_db()
    return zone.soa_serial


@override_config(nautobot_dns_models__SOA_SERIAL_AUTO_INCREMENT=True)
class SOASerialRecordCRUDTestCase(TestCase):
    """Test that record CRUD triggers exactly one serial increment on the parent zone."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(
            name="signal-test.example",
            filename="signal-test.example.zone",
            soa_mname="ns1.signal-test.example",
            soa_rname="admin@signal-test.example",
            soa_serial=0,
        )
        # IP setup for A/AAAA records
        status = Status.objects.get(name="Active")
        namespace = Namespace.objects.get(name="Global")
        Prefix.objects.create(prefix="10.50.0.0/24", namespace=namespace, type="Pool", status=status)
        Prefix.objects.create(prefix="2001:db8:face::/64", namespace=namespace, type="Pool", status=status)
        cls.ipv4 = IPAddress.objects.create(address="10.50.0.1/32", namespace=namespace, status=status)
        cls.ipv4_2 = IPAddress.objects.create(address="10.50.0.2/32", namespace=namespace, status=status)
        cls.ipv6 = IPAddress.objects.create(address="2001:db8:face::1/128", namespace=namespace, status=status)

    def setUp(self):
        """Reset zone serial to 0 before each test."""
        DNSZone.objects.filter(pk=self.zone.pk).update(soa_serial=0)
        self.zone.refresh_from_db()
        # Clear any leftover transaction coalescing state.
        _reset_dirty_zones_for_testing()

    # ── per-record-type create tests ──

    def test_nsrecord_create_increments_serial(self):
        NSRecord.objects.create(name="ns-sig", server="ns.signal-test.example.", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_arecord_create_increments_serial(self):
        ARecord.objects.create(name="a-sig", ip_address=self.ipv4, zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_aaaarecord_create_increments_serial(self):
        AAAARecord.objects.create(name="aaaa-sig", ip_address=self.ipv6, zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_cnamerecord_create_increments_serial(self):
        CNAMERecord.objects.create(name="cname-sig", alias="target.example.", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_mxrecord_create_increments_serial(self):
        MXRecord.objects.create(name="mx-sig", mail_server="mail.example.", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_txtrecord_create_increments_serial(self):
        TXTRecord.objects.create(name="txt-sig", text="v=spf1 -all", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_ptrrecord_create_increments_serial(self):
        PTRRecord.objects.create(name="ptr-sig", ptrdname="host.example.", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_srvrecord_create_increments_serial(self):
        SRVRecord.objects.create(
            name="_sip._tcp.sig", priority=10, weight=5, port=5060, target="sip.example.", zone=self.zone
        )
        self.assertEqual(_refresh_serial(self.zone), 1)

    # ── update and delete ──

    def test_record_update_increments_serial(self):
        record = TXTRecord.objects.create(name="upd-sig", text="original", zone=self.zone)
        serial_after_create = _refresh_serial(self.zone)

        # Clear coalescing state so the update can increment again.
        _reset_dirty_zones_for_testing()

        record.text = "updated"
        record.save()
        self.assertEqual(_refresh_serial(self.zone), serial_after_create + 1)

    def test_record_delete_increments_serial(self):
        record = TXTRecord.objects.create(name="del-sig", text="to-delete", zone=self.zone)
        serial_after_create = _refresh_serial(self.zone)

        _reset_dirty_zones_for_testing()

        record.delete()
        self.assertEqual(_refresh_serial(self.zone), serial_after_create + 1)

    def test_record_zone_change_increments_old_and_new_zones(self):
        """Moving a record increments both the zone losing it and the zone receiving it."""
        other_zone = DNSZone.objects.create(
            name="move-target.example",
            filename="move-target.example.zone",
            soa_mname="ns1.move-target.example",
            soa_rname="admin@move-target.example",
            soa_serial=100,
        )
        record = TXTRecord.objects.create(name="move", text="moving", zone=self.zone)
        serial_after_create = _refresh_serial(self.zone)

        _reset_dirty_zones_for_testing()
        record.zone = other_zone
        record.save()

        self.assertEqual(_refresh_serial(self.zone), serial_after_create + 1)
        self.assertEqual(_refresh_serial(other_zone), 101)

    # ── config disabled ──

    @override_config(nautobot_dns_models__SOA_SERIAL_AUTO_INCREMENT=False)
    def test_no_increment_when_config_disabled(self):
        TXTRecord.objects.create(name="no-inc", text="nope", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 0)

    # ── multi-zone isolation ──

    def test_increment_only_affects_parent_zone(self):
        other_zone = DNSZone.objects.create(
            name="other-signal.example",
            filename="other-signal.example.zone",
            soa_mname="ns1.other-signal.example",
            soa_rname="admin@other-signal.example",
            soa_serial=100,
        )
        TXTRecord.objects.create(name="iso", text="isolated", zone=self.zone)
        self.assertEqual(_refresh_serial(self.zone), 1)
        self.assertEqual(_refresh_serial(other_zone), 100)  # Unchanged


@override_config(nautobot_dns_models__SOA_SERIAL_AUTO_INCREMENT=True)
class SOASerialBulkCoalescingTestCase(TestCase):
    """Test that multiple record changes within a single transaction produce only one serial bump."""

    @classmethod
    def setUpTestData(cls):
        cls.zone = DNSZone.objects.create(
            name="bulk-test.example",
            filename="bulk-test.example.zone",
            soa_mname="ns1.bulk-test.example",
            soa_rname="admin@bulk-test.example",
            soa_serial=0,
        )

    def setUp(self):
        DNSZone.objects.filter(pk=self.zone.pk).update(soa_serial=0)
        self.zone.refresh_from_db()
        _reset_dirty_zones_for_testing()

    def test_bulk_creates_coalesce_to_one_increment(self):
        """Multiple record creates in one atomic block should increment serial by 1."""
        _reset_dirty_zones_for_testing()
        try:
            with transaction.atomic():
                TXTRecord.objects.create(name="bulk1", text="t1", zone=self.zone)
                TXTRecord.objects.create(name="bulk2", text="t2", zone=self.zone)
                TXTRecord.objects.create(name="bulk3", text="t3", zone=self.zone)
        finally:
            _reset_dirty_zones_for_testing()

        self.assertEqual(_refresh_serial(self.zone), 1)

    def test_mixed_record_types_coalesce(self):
        """Creates of different record types in one atomic block should coalesce."""
        _reset_dirty_zones_for_testing()
        try:
            with transaction.atomic():
                TXTRecord.objects.create(name="mix-txt", text="mixed", zone=self.zone)
                NSRecord.objects.create(name="mix-ns", server="ns.example.", zone=self.zone)
                CNAMERecord.objects.create(name="mix-cname", alias="target.example.", zone=self.zone)
        finally:
            _reset_dirty_zones_for_testing()

        self.assertEqual(_refresh_serial(self.zone), 1)


@override_config(nautobot_dns_models__SOA_SERIAL_AUTO_INCREMENT=True)
class SOASerialRollbackIsolationTestCase(TransactionTestCase):
    """Rollback of the outer atomic must discard dedup state.

    Regression: the prior ``threading.local`` implementation left
    ``incremented_zones`` populated when the outer transaction rolled back,
    causing the next request on a reused worker thread to silently skip its
    first increment. Connection-bound state with an ``on_commit`` freshness
    guard fixes the leak.
    """

    def setUp(self):
        _reset_dirty_zones_for_testing()
        self.zone = DNSZone.objects.create(
            name="rollback-isolation.example",
            filename="rollback-isolation.example.zone",
            soa_mname="ns1.rollback-isolation.example",
            soa_rname="admin@rollback-isolation.example",
            soa_serial=0,
        )

    def tearDown(self):
        _reset_dirty_zones_for_testing()

    def test_rollback_clears_dedup_state(self):
        """A rolled-back outer atomic must not leak dedup state into the next transaction."""
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                TXTRecord.objects.create(name="rb-1", text="first", zone=self.zone)
                raise RuntimeError("intentional rollback")

        self.zone.refresh_from_db()
        self.assertEqual(self.zone.soa_serial, 0, "rolled-back bump should not persist")

        with transaction.atomic():
            TXTRecord.objects.create(name="rb-2", text="second", zone=self.zone)

        self.zone.refresh_from_db()
        self.assertEqual(
            self.zone.soa_serial,
            1,
            "second transaction must increment — dedup state leaked across rollback",
        )


@override_config(nautobot_dns_models__SOA_SERIAL_AUTO_INCREMENT=True)
class SOASerialThreadReuseTestCase(TransactionTestCase):
    """Two sequential atomic blocks separated by ``connection.close()`` must
    both bump the serial — belt-and-braces complement to the rollback test
    that exercises the on-commit cleanup path on a reused connection wrapper.
    """

    def setUp(self):
        _reset_dirty_zones_for_testing()
        self.zone = DNSZone.objects.create(
            name="thread-reuse.example",
            filename="thread-reuse.example.zone",
            soa_mname="ns1.thread-reuse.example",
            soa_rname="admin@thread-reuse.example",
            soa_serial=0,
        )

    def tearDown(self):
        _reset_dirty_zones_for_testing()

    def test_back_to_back_transactions_both_increment(self):
        with transaction.atomic():
            TXTRecord.objects.create(name="reuse-1", text="first", zone=self.zone)
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.soa_serial, 1)

        # Simulate worker-thread reuse across requests.
        connection.close()

        with transaction.atomic():
            TXTRecord.objects.create(name="reuse-2", text="second", zone=self.zone)
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.soa_serial, 2)
