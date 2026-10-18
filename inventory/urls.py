
from django.urls import path
from . import views

urlpatterns = [
    # =========================================================
    # PRODUCTS
    # =========================================================

    path('', views.product_list, name='product_list'),

    path('add/', views.product_add, name='product_add'),

    path(
        '<int:product_id>/edit/',
        views.product_edit,
        name='product_edit'
    ),

    path(
        '<int:product_id>/delete/',
        views.product_delete,
        name='product_delete'
    ),

    path(
        '<int:product_id>/',
        views.product_detail,
        name='product_detail'
    ),

    # =========================================================
    # CATEGORIES
    # =========================================================

    path('categories/', views.category_list, name='category_list'),

    path(
        'categories/add/',
        views.category_add,
        name='category_add'
    ),

    path(
        'categories/<int:category_id>/edit/',
        views.category_edit,
        name='category_edit'
    ),

    path(
        'categories/<int:category_id>/delete/',
        views.category_delete,
        name='category_delete'
    ),

    # =========================================================
    # SUPPLIERS
    # =========================================================

    path('suppliers/', views.suppliers, name='suppliers'),

    path(
        'suppliers/add/',
        views.supplier_add,
        name='supplier_add'
    ),

    path(
        'suppliers/<int:supplier_id>/edit/',
        views.supplier_edit,
        name='supplier_edit'
    ),

    path(
        'suppliers/<int:supplier_id>/delete/',
        views.supplier_delete,
        name='supplier_delete'
    ),

    # =========================================================
    # PURCHASES
    # =========================================================

    path('purchases/', views.purchases, name='purchases'),

    path(
        'purchases/add/',
        views.purchase_add,
        name='purchase_add'
    ),

    # =========================================================
    # CUSTOMERS
    # =========================================================

    path('customers/', views.customers, name='customers'),

    path(
        'customers/add/',
        views.customer_add,
        name='customer_add'
    ),

    path(
        'customers/<int:customer_id>/edit/',
        views.customer_edit,
        name='customer_edit'
    ),

    path(
        'customers/<int:customer_id>/delete/',
        views.customer_delete,
        name='customer_delete'
    ),

    # =========================================================
    # ORDERS
    # =========================================================

    path('orders/', views.orders, name='orders'),

    path(
        'orders/add/',
        views.order_add,
        name='order_add'
    ),

    # =========================================================
    # INVENTORY
    # =========================================================

    path(
        'current_stock/',
        views.current_stock,
        name='current_stock'
    ),

    path(
        'stock/low/',
        views.low_stock,
        name='low_stock'
    ),

    path(
        'stock/movement/',
        views.stock_movement,
        name='stock_movement'
    ),

    # =========================================================
    # REPORTS
    # =========================================================

    path(
        'reports/sales/',
        views.sales_report,
        name='sales_report'
    ),

    path(
        'reports/reorder-suggestions/',
        views.reorder_suggestions,
        name='reorder_suggestions'
    ),

    # =========================================================
    # SETTINGS
    # =========================================================

    path('settings/', views.settings, name='settings'),
]
