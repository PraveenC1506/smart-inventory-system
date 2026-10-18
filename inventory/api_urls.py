from django.urls import path
from . import api_views

urlpatterns = [
    # Products
    path(
        "products/",
        api_views.ProductListCreateAPIView.as_view(),
        name="api_product_list_create",
    ),
    path(
        "products/<int:pk>/",
        api_views.ProductDetailAPIView.as_view(),
        name="api_product_detail",
    ),

    # Categories
    path(
        "categories/",
        api_views.CategoryListCreateAPIView.as_view(),
        name="api_category_list_create",
    ),
    path(
        "categories/<int:pk>/",
        api_views.CategoryDetailAPIView.as_view(),
        name="api_category_detail",
    ),
]