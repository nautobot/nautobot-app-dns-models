"""Django API urlpatterns declaration for nautobot_dns_models plugin."""

from nautobot.core.api import OrderedDefaultRouter

from nautobot_dns_models.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("dnszonemodel", views.DnsZoneModelViewSet)


app_name = "nautobot_dns_models-api"
urlpatterns = router.urls
