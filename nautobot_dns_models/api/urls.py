"""Django API urlpatterns declaration for nautobot_dns_models plugin."""

from nautobot.core.api.routers import OrderedDefaultRouter

from nautobot_dns_models.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("dns-zone-records", views.DNSZoneModelViewSet)
router.register("ns-records", views.NSRecordModelViewSet)
router.register("a-records", views.ARecordModelViewSet)
router.register("aaaa-records", views.AAAARecordModelViewSet)
router.register("cname-records", views.CNameRecordModelViewSet)
router.register("mx-records", views.MXRecordModelViewSet)
router.register("txt-records", views.TXTRecordModelViewSet)
router.register("ptr-records", views.PTRRecordModelViewSet)

app_name = "nautobot_dns_models-api"
urlpatterns = router.urls
