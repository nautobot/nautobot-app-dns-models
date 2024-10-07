"""Django API urlpatterns declaration for nautobot_dns_models plugin."""

from nautobot.apps.api import OrderedDefaultRouter

from nautobot_dns_models.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("dns-zones", views.DNSZoneModelViewSet)
router.register("ns-records", views.NSRecordModelViewSet)
router.register("a-records", views.ARecordModelViewSet)
router.register("aaaa-records", views.AAAARecordModelViewSet)
router.register("cname-records", views.CNameRecordModelViewSet)
router.register("mx-records", views.MXRecordModelViewSet)
router.register("txt-records", views.TXTRecordModelViewSet)
router.register("ptr-records", views.PTRRecordModelViewSet)

urlpatterns = router.urls
