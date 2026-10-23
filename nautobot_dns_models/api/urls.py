"""Django API urlpatterns declaration for nautobot_dns_models plugin."""

from nautobot.apps.api import OrderedDefaultRouter

from nautobot_dns_models.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("dns-views", views.DNSViewViewSet)
router.register("dns-view-prefix-assignments", views.DNSViewPrefixAssignmentViewSet)
router.register("dns-registrars", views.DNSRegistrarViewSet)
router.register("dns-registrations", views.DNSRegistrationViewSet)
router.register("dns-zones", views.DNSZoneViewSet)
router.register("dns-delegations", views.DNSDelegationViewSet)
router.register("ns-records", views.NSRecordViewSet)
router.register("a-records", views.ARecordViewSet)
router.register("aaaa-records", views.AAAARecordViewSet)
router.register("cname-records", views.CNameRecordViewSet)
router.register("mx-records", views.MXRecordViewSet)
router.register("txt-records", views.TXTRecordViewSet)
router.register("ptr-records", views.PTRRecordViewSet)
router.register("srv-records", views.SRVRecordViewSet)
router.register("dns-forwarders", views.DNSForwarderViewSet)
router.register("dns-forwarding-rules", views.DNSForwardingRuleViewSet)
router.register("dns-forwarding-rule-forwarder-assignments", views.DNSForwardingRuleForwarderAssignmentViewSet)

app_name = "nautobot_dns_models-api"
urlpatterns = router.urls
