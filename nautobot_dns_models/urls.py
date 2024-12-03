"""Django urlpatterns declaration for nautobot_dns_models plugin."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_dns_models import views

router = NautobotUIViewSetRouter()

router.register("dns-zones", views.DNSZoneModelViewSet)
router.register("ns-records", views.NSRecordModelViewSet)
router.register("a-records", views.ARecordModelViewSet)
router.register("aaaa-records", views.AAAARecordModelViewSet)
router.register("cname-records", views.CNAMERecordModelViewSet)
router.register("mx-records", views.MXRecordModelViewSet)
router.register("txt-records", views.TXTRecordModelViewSet)
router.register("ptr-records", views.PTRRecordModelViewSet)

urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("dns_models/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
