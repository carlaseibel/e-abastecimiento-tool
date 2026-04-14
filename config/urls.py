from django.contrib import admin
from django.urls import path, include
from apps.suppliers.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DashboardView.as_view(), name="dashboard"),
    path("fornecedores/", include("apps.suppliers.urls")),
    path("cotacoes/", include("apps.quotes.urls")),
]
