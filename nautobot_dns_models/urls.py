"""Django urlpatterns declaration for nautobot_dns_models plugin."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_dns_models import views

app_name = "nautobot_dns_models"
router = NautobotUIViewSetRouter()

router.register("dns-views", views.DNSViewUIViewSet)
router.register("dns-zones", views.DNSZoneUIViewSet)
router.register("a-records", views.ARecordUIViewSet)
router.register("aaaa-records", views.AAAARecordUIViewSet)
router.register("ns-records", views.NSRecordUIViewSet)
router.register("cname-records", views.CNAMERecordUIViewSet)
router.register("mx-records", views.MXRecordUIViewSet)
router.register("txt-records", views.TXTRecordUIViewSet)
router.register("ptr-records", views.PTRRecordUIViewSet)
router.register("srv-records", views.SRVRecordUIViewSet)

urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("nautobot_dns_models/docs/index.html")), name="docs"),
    # Paths for buttons used in DNS zone viewset
    path(
        "dns-zones/<uuid:pk>/a-records/add/",
        RedirectView.as_view(url="/plugins/dns/a-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"),
        name="zone_a_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/aaaa-records/add/",
        RedirectView.as_view(
            url="/plugins/dns/aquiaaa-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"
        ),
        name="zone_aaaa_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/cname-records/add/",
        RedirectView.as_view(
            url="/plugins/dns/cname-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"
        ),
        name="zone_cname_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/mx-records/add/",
        RedirectView.as_view(url="/plugins/dns/mx-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"),
        name="zone_mx_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/ns-records/add/",
        RedirectView.as_view(url="/plugins/dns/ns-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"),
        name="zone_ns_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/ptr-records/add/",
        RedirectView.as_view(url="/plugins/dns/ptr-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"),
        name="zone_ptr_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/srv-records/add/",
        RedirectView.as_view(url="/plugins/dns/srv-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"),
        name="zone_srv_records_add",
    ),
    path(
        "dns-zones/<uuid:pk>/txt-records/add/",
        RedirectView.as_view(url="/plugins/dns/txt-records/add/?zone=%(pk)s&return_url=/plugins/dns/dns-zones/%(pk)s"),
        name="zone_txt_records_add",
    ),
]

urlpatterns += router.urls
