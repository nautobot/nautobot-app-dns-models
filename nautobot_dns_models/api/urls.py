"""Django API urlpatterns declaration for nautobot_dns_models plugin."""

from nautobot.core.api.routers import OrderedDefaultRouter

from nautobot_dns_models.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("dnszonemodel", views.DNSZoneModelViewSet)
router.register("nsrecordmodel", views.NSRecordModelViewSet)
router.register("arecordmodel", views.ARecordModelViewSet)
router.register("aaaarecordmodel", views.AAAARecordModelViewSet)
router.register("cnamerecordmodel", views.CNameRecordModelViewSet)
router.register("mxrecordmodel", views.MXRecordModelViewSet)
router.register("txtrecordmodel", views.TXTRecordModelViewSet)
router.register("ptrrecordmodel", views.PTRRecordModelViewSet)

app_name = "nautobot_dns_models-api"
urlpatterns = router.urls
