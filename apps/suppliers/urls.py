from django.urls import path
from . import views

urlpatterns = [
    path("", views.SupplierListView.as_view(), name="supplier_list"),
    path("novo/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path("upload/", views.SupplierUploadView.as_view(), name="supplier_upload"),
    path("<uuid:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),
    path("<uuid:pk>/score/", views.TriggerScoreView.as_view(), name="supplier_score"),
]
