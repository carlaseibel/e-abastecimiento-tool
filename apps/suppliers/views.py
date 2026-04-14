import json

from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import CSVUploadForm, SupplierForm
from .models import Supplier
from .services import import_suppliers_from_csv, run_risk_scoring


class DashboardView(View):
    template_name = "dashboard.html"

    def get(self, request):
        suppliers = (
            Supplier.objects.all()
            .prefetch_related("quotes")
            .annotate(quote_count=Count("quotes"))
        )
        stats = {
            "total": suppliers.count(),
            "alto_critico": suppliers.filter(nivel_risco__in=["ALTO", "CRÍTICO"]).count(),
            "sem_score": suppliers.filter(score_risco__isnull=True).count(),
            "score_medio": suppliers.aggregate(avg=Avg("score_risco"))["avg"],
        }
        return render(request, self.template_name, {"suppliers": suppliers, "stats": stats})


class SupplierListView(View):
    template_name = "suppliers/list.html"

    def get(self, request):
        suppliers = Supplier.objects.all().annotate(quote_count=Count("quotes"))
        return render(request, self.template_name, {"suppliers": suppliers})


class SupplierDetailView(View):
    template_name = "suppliers/detail.html"

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        quotes = supplier.quotes.order_by("-data")
        return render(request, self.template_name, {"supplier": supplier, "quotes": quotes})


class SupplierCreateView(View):
    template_name = "suppliers/form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": SupplierForm()})

    def post(self, request):
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"Fornecedor {supplier.nome} cadastrado com sucesso.")
            return redirect("supplier_detail", pk=supplier.pk)
        return render(request, self.template_name, {"form": form})


class SupplierUploadView(View):
    template_name = "suppliers/upload.html"

    def get(self, request):
        return render(request, self.template_name, {"form": CSVUploadForm()})

    def post(self, request):
        form = CSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        result = import_suppliers_from_csv(request.FILES["arquivo"])

        if result.errors and result.imported == 0:
            messages.error(request, f"Erro no arquivo: {result.errors[0]['error']}")
            return render(request, self.template_name, {"form": form})

        messages.success(
            request,
            f"{result.imported} fornecedor(es) importado(s). "
            f"{result.skipped} ignorado(s)."
            + (f" {len(result.errors)} linha(s) com erro." if result.errors else ""),
        )
        return redirect("supplier_list")


class TriggerScoreView(View):
    """POST /fornecedores/<uuid>/score/ — calls Claude, returns JSON."""

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        try:
            supplier = run_risk_scoring(supplier)
            return JsonResponse({
                "ok": True,
                "score_risco": float(supplier.score_risco),
                "nivel_risco": supplier.nivel_risco,
                "resumo_ia": supplier.resumo_ia,
            })
        except ValueError as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"Erro ao chamar IA: {e}"}, status=500)
