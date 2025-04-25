"""Django urlpatterns declaration for nautobot_dns_models app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter


from nautobot_dns_models import views


app_name = "nautobot_dns_models"
router = NautobotUIViewSetRouter()

# The standard is for the route to be the hyphenated version of the model class name plural.
# for example, ExampleModel would be example-models.
router.register("dns-zone-models", views.DnsZoneModelUIViewSet)


urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("nautobot_dns_models/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
