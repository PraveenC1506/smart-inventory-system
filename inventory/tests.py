
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Category,
    Product,
    Supplier,
    Purchase,
    PurchaseItem,
    Customer,
    Order,
    OrderItem,
    StockMovement,
)


class InventoryTestBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="inventory_test_user",
            password="TestPass123!Secure",
        )
        self.client.force_login(self.user)

        self.category = Category.objects.create(
            name="Test Category"
        )

        self.product = Product.objects.create(
            name="Test Pen",
            category=self.category,
            sku="TEST-PEN-001",
            purchase_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            stock_quantity=10,
            reorder_level=5,
        )

        self.supplier = Supplier.objects.create(
            name="Test Supplier"
        )

        self.customer = Customer.objects.create(
            name="Test Customer"
        )


# --------------------------------------------------
# CATEGORY MODEL TESTS
# --------------------------------------------------

class CategoryModelTests(InventoryTestBase):
    def test_category_can_be_created(self):
        self.assertTrue(
            Category.objects.filter(pk=self.category.pk).exists()
        )

    def test_category_name_is_saved(self):
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Test Category")


# --------------------------------------------------
# PRODUCT MODEL TESTS
# --------------------------------------------------

class ProductModelTests(InventoryTestBase):
    def test_product_is_saved(self):
        self.assertEqual(self.product.name, "Test Pen")
        self.assertEqual(self.product.stock_quantity, 10)

    def test_product_is_not_low_stock_above_reorder_level(self):
        self.assertFalse(self.product.is_low_stock)

    def test_product_is_low_stock_at_reorder_level(self):
        self.product.stock_quantity = 5
        self.assertTrue(self.product.is_low_stock)

    def test_product_is_low_stock_below_reorder_level(self):
        self.product.stock_quantity = 2
        self.assertTrue(self.product.is_low_stock)


# --------------------------------------------------
# STOCK MOVEMENT MODEL TESTS
# --------------------------------------------------

class StockMovementModelTests(InventoryTestBase):
    def test_stock_movement_is_saved(self):
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type="IN",
            quantity=5,
            previous_stock=10,
            updated_stock=15,
            reference="TEST-001",
            notes="Automated test",
        )

        self.assertTrue(
            StockMovement.objects.filter(pk=movement.pk).exists()
        )

    def test_stock_movement_records_stock_values(self):
        movement = StockMovement.objects.create(
            product=self.product,
            movement_type="OUT",
            quantity=3,
            previous_stock=10,
            updated_stock=7,
        )

        self.assertEqual(movement.previous_stock, 10)
        self.assertEqual(movement.updated_stock, 7)


# --------------------------------------------------
# PURCHASE WORKFLOW TESTS
# --------------------------------------------------

class PurchaseWorkflowTests(InventoryTestBase):
    def test_purchase_increases_stock_and_creates_history(self):
        response = self.client.post(
            reverse("purchase_add"),
            {
                "supplier": self.supplier.pk,
                "product": self.product.pk,
                "quantity": "5",
                "unit_price": "10.00",
                "purchase_date": timezone.localdate().isoformat(),
                "notes": "Automated test purchase",
            },
        )

        self.assertRedirects(response, reverse("purchases"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)

        purchase = Purchase.objects.get()
        self.assertEqual(purchase.total_amount, Decimal("50.00"))

        item = PurchaseItem.objects.get(purchase=purchase)
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.total_price, Decimal("50.00"))

        movement = StockMovement.objects.get(
            reference=f"Purchase #{purchase.pk}"
        )
        self.assertEqual(movement.movement_type, "IN")
        self.assertEqual(movement.previous_stock, 10)
        self.assertEqual(movement.updated_stock, 15)

    def test_purchase_rejects_zero_quantity(self):
        response = self.client.post(
            reverse("purchase_add"),
            {
                "supplier": self.supplier.pk,
                "product": self.product.pk,
                "quantity": "0",
                "unit_price": "10.00",
                "purchase_date": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertEqual(Purchase.objects.count(), 0)


# --------------------------------------------------
# ORDER WORKFLOW TESTS
# --------------------------------------------------

class OrderWorkflowTests(InventoryTestBase):
    def test_order_reduces_stock_and_creates_history(self):
        response = self.client.post(
            reverse("order_add"),
            {
                "customer": self.customer.pk,
                "product": self.product.pk,
                "quantity": "3",
            },
        )

        self.assertRedirects(response, reverse("orders"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 7)

        order = Order.objects.get()
        self.assertEqual(order.total_amount, Decimal("45.00"))

        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.total_price, Decimal("45.00"))

        movement = StockMovement.objects.get(
            reference=f"Order #{order.pk}"
        )
        self.assertEqual(movement.movement_type, "OUT")
        self.assertEqual(movement.previous_stock, 10)
        self.assertEqual(movement.updated_stock, 7)

    def test_order_rejects_insufficient_stock(self):
        response = self.client.post(
            reverse("order_add"),
            {
                "customer": self.customer.pk,
                "product": self.product.pk,
                "quantity": "11",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_order_rejects_zero_quantity(self):
        response = self.client.post(
            reverse("order_add"),
            {
                "customer": self.customer.pk,
                "product": self.product.pk,
                "quantity": "0",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertEqual(Order.objects.count(), 0)


# --------------------------------------------------
# REST API TESTS
# --------------------------------------------------

class InventoryAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="api_test_user",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name="API Test Category",
            description="Category for API testing",
        )

        self.product = Product.objects.create(
            name="API Test Product",
            category=self.category,
            sku="API-TEST-001",
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
            stock_quantity=10,
            reorder_level=2,
        )

    def test_product_list_api_returns_200(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_detail_api_returns_product(self):
        response = self.client.get(
            f"/api/products/{self.product.pk}/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "API Test Product")

    def test_category_list_api_returns_200(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_create_api(self):
        data = {
            "name": "New API Product",
            "sku": "API-NEW-001",
            "barcode": "API12345",
            "purchase_price": "200.00",
            "selling_price": "300.00",
            "stock_quantity": 5,
            "reorder_level": 2,
            "category": self.category.pk,
        }

        response = self.client.post(
            "/api/products/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=str(response.data),
        )
        self.assertTrue(
            Product.objects.filter(sku="API-NEW-001").exists()
        )

    def test_product_update_api(self):
        response = self.client.patch(
            f"/api/products/{self.product.pk}/",
            {"selling_price": "175.00"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=str(response.data),
        )

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.selling_price,
            Decimal("175.00"),
        )

    def test_product_delete_api(self):
        product_id = self.product.pk

        response = self.client.delete(
            f"/api/products/{product_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            Product.objects.filter(pk=product_id).exists()
        )

    def test_product_api_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/products/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ----------------------------------------------
    # API VALIDATION TESTS
    # ----------------------------------------------

    def test_product_api_rejects_duplicate_sku(self):
        data = {
            "name": "Duplicate SKU Product",
            "sku": self.product.sku,
            "purchase_price": "100.00",
            "selling_price": "150.00",
            "stock_quantity": 5,
            "reorder_level": 2,
            "category": self.category.pk,
        }

        response = self.client.post(
            "/api/products/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_product_api_rejects_negative_price(self):
        response = self.client.patch(
            f"/api/products/{self.product.pk}/",
            {"selling_price": "-10.00"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_product_api_rejects_negative_stock(self):
        response = self.client.patch(
            f"/api/products/{self.product.pk}/",
            {"stock_quantity": -5},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
