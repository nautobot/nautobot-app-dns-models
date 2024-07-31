"""Django urlpatterns declaration for nautobot_dns_models plugin."""

from django.urls import path
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_dns_models import models

from nautobot_dns_models import views

router = NautobotUIViewSetRouter()

router.register("dnszone", views.DNSZoneModelViewSet)
router.register("nsrecord", views.NSRecordModelViewSet)
router.register("arecord", views.ARecordModelViewSet)
router.register("aaaarecord", views.AAAARecordModelViewSet)
router.register("cnamerecord", views.CNAMERecordModelViewSet)
router.register("mxrecord", views.MXRecordModelViewSet)
router.register("txtrecord", views.TXTRecordModelViewSet)
router.register("ptrrecord", views.PTRRecordModelViewSet)

urlpatterns = []

urlpatterns += router.urls
