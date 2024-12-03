"""Django urlpatterns declaration for dns_models app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from dns_models import views

router = NautobotUIViewSetRouter()
router.register("dnszonemodel", views.DnsZoneModelUIViewSet)

urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("dns_models/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
