"""Django urlpatterns declaration for nautobot_dns_models plugin."""
from django.urls import path
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView
from nautobot.apps.urls import NautobotUIViewSetRouter

from nautobot_dns_models import models

from nautobot_dns_models import views

router = NautobotUIViewSetRouter()

router.register("dnszonemodel", views.DnsZoneModelViewSet)
router.register("nsrecordmodel", views.NSRecordModelViewSet)
router.register("arecordmodel", views.ARecordModelViewSet)
router.register("aaaarecordmodel", views.AAAARecordModelViewSet)
router.register("cnamerecordmodel", views.CNAMERecordModelViewSet)
router.register("mxrecordmodel", views.MXRecordModelViewSet)
router.register("txtrecordmodel", views.TXTRecordModelViewSet)
router.register("ptrrecordmodel", views.PTRRecordModelViewSet)

urlpatterns = [
    # path(
    #     "dnszonemodel/<uuid:pk>/changelog/",
    #     ObjectChangeLogView.as_view(),
    #     name="dnszonemodel_changelog",
    #     kwargs={"model": models.DnsZoneModel},
    # ),
    # path(
    #     "dnszonemodel/<slug:slug>/changelog/",
    #     ObjectChangeLogView.as_view(),
    #     name="dnszonemodel_changelog",
    #     kwargs={"model": models.DnsZoneModel},
    # ),
    # path(
    #     "dnszonemodel/<uuid:pk>/notes/",
    #     ObjectNotesView.as_view(),
    #     name="dnszonemodel_notes",
    #     kwargs={"model": models.DnsZoneModel},
    # ),
]

urlpatterns += router.urls

# urlpatterns = [
#     # DnsZoneModel URLs
#     path("dnszonemodel/", dnszonemodel.DnsZoneModelListView.as_view(), name="dnszonemodel_list"),
#     # Order is important for these URLs to work (add/delete/edit) to be before any that require uuid/slug
#     path("dnszonemodel/add/", dnszonemodel.DnsZoneModelCreateView.as_view(), name="dnszonemodel_add"),
#     path("dnszonemodel/delete/", dnszonemodel.DnsZoneModelBulkDeleteView.as_view(), name="dnszonemodel_bulk_delete"),
#     path("dnszonemodel/edit/", dnszonemodel.DnsZoneModelBulkEditView.as_view(), name="dnszonemodel_bulk_edit"),
#     path("dnszonemodel/<slug:slug>/", dnszonemodel.DnsZoneModelView.as_view(), name="dnszonemodel"),
#     path("dnszonemodel/<slug:slug>/delete/", dnszonemodel.DnsZoneModelDeleteView.as_view(), name="dnszonemodel_delete"),
#     path("dnszonemodel/<slug:slug>/edit/", dnszonemodel.DnsZoneModelEditView.as_view(), name="dnszonemodel_edit"),
#     path(
#         "dnszonemodel/<slug:slug>/changelog/",
#         ObjectChangeLogView.as_view(),
#         name="dnszonemodel_changelog",
#         kwargs={"model": models.DnsZoneModel},
#     ),
# ]
