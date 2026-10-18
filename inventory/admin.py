
from django.contrib import admin
from .models import Category, Product, Supplier, Customer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'purchase_price',
        'selling_price',
        'stock_quantity',
        'reorder_level',
    )

    search_fields = ('name', 'sku', 'barcode')
    list_filter = ('category',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'contact_person',
        'phone',
        'email',
        'created_at',
    )

    search_fields = (
        'name',
        'contact_person',
        'phone',
        'email',
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'email',
        'created_at',
    )

    search_fields = (
        'name',
        'phone',
        'email',
    )
