
from django.shortcuts import render
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required

from inventory.models import Product, Order, Purchase


@login_required
def dashboard(request):
    total_products = Product.objects.count()

    total_stock_quantity = (
        Product.objects.aggregate(
            total=Sum('stock_quantity')
        )['total'] or 0
    )

    total_sales = (
        Order.objects.filter(status='Completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    total_purchase_value = (
        Purchase.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    )

    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('reorder_level')
    ).count()

    context = {
        'total_products': total_products,
        'total_stock_quantity': total_stock_quantity,
        'total_sales': total_sales,
        'total_purchase_value': total_purchase_value,
        'low_stock_products': low_stock_products,
    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )
