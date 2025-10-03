"""Django API urlpatterns declaration for nautobot_dns_models plugin."""

from nautobot.apps.api import OrderedDefaultRouter

from nautobot_dns_models.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("dns-views", views.DNSViewViewSet)
router.register("dns-view-prefix-assignments", views.DNSViewPrefixAssignmentViewSet)
router.register("dns-zones", views.DNSZoneViewSet)
router.register("ns-records", views.NSRecordViewSet)
router.register("a-records", views.ARecordViewSet)
router.register("aaaa-records", views.AAAARecordViewSet)
router.register("cname-records", views.CNameRecordViewSet)
router.register("mx-records", views.MXRecordViewSet)
router.register("txt-records", views.TXTRecordViewSet)
router.register("ptr-records", views.PTRRecordViewSet)
router.register("srv-records", views.SRVRecordViewSet)

app_name = "nautobot_dns_models-api"
urlpatterns = router.urls
