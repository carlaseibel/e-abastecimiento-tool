from django.urls import path
from . import views

urlpatterns = [
    path("nova/<uuid:supplier_pk>/", views.PriceQuoteCreateView.as_view(), name="quote_create"),
]
