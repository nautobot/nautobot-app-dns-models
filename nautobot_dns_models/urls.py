"""Django urlpatterns declaration for nautobot_dns_models plugin."""

from django.urls import path
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_dns_models import models

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

urlpatterns = []

urlpatterns += router.urls
