from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F, ProtectedError, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import (
    Product, Category, Supplier, Purchase, PurchaseItem,
    Customer, Order, OrderItem, StockMovement,
)


# ==================== PRODUCTS ====================

@login_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'inventory/product_list.html', {'products': products})


@login_required
def product_add(request):
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('product_name', request.POST.get('name', '')).strip()
        sku = request.POST.get('sku', '').strip()
        barcode = request.POST.get('barcode', '').strip()
        category_id = request.POST.get('category', '').strip()

        try:
            purchase_price = Decimal(request.POST.get('purchase_price', '0') or '0')
            selling_price = Decimal(request.POST.get('selling_price', request.POST.get('price', '0')) or '0')
            stock = int(request.POST.get('stock_quantity', '0'))
            reorder = int(request.POST.get('reorder_level', '10'))

            if not name or not sku or not category_id:
                messages.error(request, 'Product name, SKU and category are required.')
            elif min(purchase_price, selling_price) < 0 or stock < 0 or reorder < 0:
                messages.error(request, 'Values cannot be negative.')
            elif Product.objects.filter(sku__iexact=sku).exists():
                messages.error(request, 'SKU already exists.')
            else:
                category = get_object_or_404(Category, id=category_id)
                Product.objects.create(
                    name=name, sku=sku, barcode=barcode, category=category,
                    purchase_price=purchase_price, selling_price=selling_price,
                    stock_quantity=stock, reorder_level=reorder,
                )
                messages.success(request, 'Product added successfully.')
                return redirect('product_list')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Enter valid prices and quantities.')

    return render(request, 'inventory/product_add.html', {'categories': categories})


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category'), id=product_id
    )
    return render(request, 'inventory/product_detail.html', {'product': product})


@login_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get(
            'product_name', request.POST.get('name', product.name)
        ).strip()
        sku = request.POST.get('sku', product.sku).strip()
        barcode = request.POST.get('barcode', product.barcode).strip()
        category_id = request.POST.get('category', '').strip()

        try:
            purchase_price = Decimal(
                request.POST.get(
                    'purchase_price', str(product.purchase_price)
                ) or '0'
            )
            selling_price = Decimal(
                request.POST.get(
                    'selling_price',
                    request.POST.get('price', str(product.selling_price))
                ) or '0'
            )
            reorder = int(request.POST.get(
                'reorder_level', str(product.reorder_level)
            ))

            if not name or not sku or not category_id:
                messages.error(
                    request,
                    'Product name, SKU and category are required.'
                )
            elif Product.objects.filter(
                sku__iexact=sku
            ).exclude(id=product.id).exists():
                messages.error(request, 'SKU already exists.')
            elif purchase_price < 0 or selling_price < 0 or reorder < 0:
                messages.error(
                    request,
                    'Prices and reorder level cannot be negative.'
                )
            else:
                category = get_object_or_404(Category, id=category_id)

                # Stock quantity is intentionally not changed here.
                # Use the Stock Movement page to adjust inventory.
                product.name = name
                product.sku = sku
                product.barcode = barcode
                product.category = category
                product.purchase_price = purchase_price
                product.selling_price = selling_price
                product.reorder_level = reorder
                product.save(update_fields=[
                    'name', 'sku', 'barcode', 'category',
                    'purchase_price', 'selling_price',
                    'reorder_level', 'updated_at',
                ])

                messages.success(
                    request, 'Product updated successfully.'
                )
                return redirect('product_list')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Enter valid product values.')

    return render(request, 'inventory/product_edit.html', {
        'product': product,
        'categories': categories,
    })

@login_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        try:
            product.delete()
            messages.success(request, 'Product deleted successfully.')
        except ProtectedError:
            messages.error(request, 'This product is linked to transactions and cannot be deleted.')
    return redirect('product_list')


# ==================== CATEGORIES ====================

@login_required
def category_list(request):
    return render(request, 'inventory/categories.html', {
        'categories': Category.objects.all().order_by('name'),
    })


@login_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, 'Category already exists.')
        else:
            Category.objects.create(name=name, description=description)
            messages.success(request, 'Category added successfully.')
            return redirect('category_list')

    return render(request, 'inventory/category_add.html')


@login_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exclude(id=category.id).exists():
            messages.error(request, 'Category already exists.')
        else:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')

    return render(request, 'inventory/category_edit.html', {'category': category})


@login_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, 'Category deleted successfully.')
        except ProtectedError:
            messages.error(request, 'This category is linked to products and cannot be deleted.')
    return redirect('category_list')


# ==================== SUPPLIERS ====================

@login_required
def suppliers(request):
    return render(request, 'inventory/suppliers.html', {
        'suppliers': Supplier.objects.all().order_by('-id'),
    })


@login_required
def supplier_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, 'Supplier name is required.')
        else:
            Supplier.objects.create(
                name=name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                address=address,
            )
            messages.success(request, 'Supplier added successfully.')
            return redirect('suppliers')

    return render(request, 'inventory/supplier_add.html')


@login_required
def supplier_edit(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, 'Supplier name is required.')
        else:
            supplier.name = name
            supplier.contact_person = contact_person
            supplier.phone = phone
            supplier.email = email
            supplier.address = address
            supplier.save()
            messages.success(request, 'Supplier updated successfully.')
            return redirect('suppliers')

    return render(request, 'inventory/supplier_edit.html', {'supplier': supplier})


@login_required
def supplier_delete(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        try:
            supplier.delete()
            messages.success(request, 'Supplier deleted successfully.')
        except ProtectedError:
            messages.error(request, 'This supplier is linked to purchases and cannot be deleted.')
    return redirect('suppliers')


# ==================== PURCHASES ====================

@login_required
def purchases(request):
    purchase_list = Purchase.objects.select_related(
        'supplier'
    ).prefetch_related('items__product').order_by('-id')

    return render(request, 'inventory/purchases.html', {'purchases': purchase_list})


@login_required
def purchase_add(request):
    suppliers_list = Supplier.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier', '').strip()
        product_id = request.POST.get('product', '').strip()
        notes = request.POST.get('notes', '').strip()

        try:
            quantity = int(request.POST.get('quantity', '0'))
            price_text = request.POST.get('unit_price', request.POST.get('purchase_price', '0'))
            price = Decimal(price_text or '0')
            date_text = request.POST.get('purchase_date', '').strip()

            if quantity <= 0 or price < 0:
                messages.error(request, 'Quantity must be positive and price cannot be negative.')
            elif not supplier_id or not product_id:
                messages.error(request, 'Select a supplier and product.')
            else:
                purchase_date = (
                    datetime.strptime(date_text, '%Y-%m-%d').date()
                    if date_text else timezone.localdate()
                )

                with transaction.atomic():
                    supplier = get_object_or_404(Supplier, id=supplier_id)
                    product = get_object_or_404(
                        Product.objects.select_for_update(), id=product_id
                    )
                    line_total = price * quantity

                    purchase = Purchase.objects.create(
                        supplier=supplier,
                        purchase_date=purchase_date,
                        total_amount=line_total,
                        notes=notes,
                    )
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=quantity,
                        purchase_price=price,
                        total_price=line_total,
                    )

                    previous_stock = product.stock_quantity
                    product.stock_quantity += quantity
                    product.save()

                    StockMovement.objects.create(
                        product=product,
                        movement_type='IN',
                        quantity=quantity,
                        previous_stock=previous_stock,
                        updated_stock=product.stock_quantity,
                        reference=f'Purchase #{purchase.id}',
                        notes=notes,
                    )

                messages.success(request, 'Purchase added and stock updated successfully.')
                return redirect('purchases')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Enter a valid date, quantity and price.')

    return render(request, 'inventory/purchase_add.html', {
        'suppliers': suppliers_list, 'products': products,
    })


# ==================== CUSTOMERS ====================

@login_required
def customers(request):
    customer_list = Customer.objects.annotate(
        total_orders=Count('orders', distinct=True)
    ).order_by('-id')
    return render(request, 'inventory/customers.html', {'customers': customer_list})


@login_required
def customer_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, 'Customer name is required.')
        else:
            Customer.objects.create(
                name=name, phone=phone, email=email, address=address
            )
            messages.success(request, 'Customer added successfully.')
            return redirect('customers')

    return render(request, 'inventory/customer_add.html')


@login_required
def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Customer name is required.')
        else:
            customer.name = name
            customer.phone = request.POST.get('phone', '').strip()
            customer.email = request.POST.get('email', '').strip()
            customer.address = request.POST.get('address', '').strip()
            customer.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('customers')

    return render(request, 'inventory/customer_edit.html', {'customer': customer})


@login_required
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        try:
            customer.delete()
            messages.success(request, 'Customer deleted successfully.')
        except ProtectedError:
            messages.error(request, 'This customer is linked to orders and cannot be deleted.')
    return redirect('customers')


# ==================== ORDERS ====================

@login_required
def orders(request):
    order_list = Order.objects.select_related(
        'customer'
    ).prefetch_related('items__product').order_by('-id')
    return render(request, 'inventory/orders.html', {'orders': order_list})


@login_required
def order_add(request):
    customers_list = Customer.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer', '').strip()
        product_id = request.POST.get('product', '').strip()

        try:
            quantity = int(request.POST.get('quantity', '0'))

            if quantity <= 0:
                messages.error(request, 'Quantity must be greater than zero.')
            elif not customer_id or not product_id:
                messages.error(request, 'Select a customer and product.')
            else:
                order_created = False

                with transaction.atomic():
                    customer = get_object_or_404(Customer, id=customer_id)
                    product = get_object_or_404(
                        Product.objects.select_for_update(), id=product_id
                    )

                    if product.stock_quantity < quantity:
                        messages.error(request, 'Insufficient stock for this product.')
                    else:
                        price = product.selling_price
                        subtotal = price * quantity

                        order = Order.objects.create(
                            customer=customer,
                            total_amount=subtotal,
                            status='Completed',
                        )
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            selling_price=price,
                            total_price=subtotal,
                        )

                        previous_stock = product.stock_quantity
                        product.stock_quantity -= quantity
                        product.save()

                        StockMovement.objects.create(
                            product=product,
                            movement_type='OUT',
                            quantity=quantity,
                            previous_stock=previous_stock,
                            updated_stock=product.stock_quantity,
                            reference=f'Order #{order.id}',
                            notes='Stock reduced for order',
                        )
                        order_created = True

                if order_created:
                    messages.success(request, 'Order added and stock updated successfully.')
                    return redirect('orders')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Enter a valid quantity.')

    return render(request, 'inventory/order_add.html', {
        'customers': customers_list, 'products': products,
    })


# ==================== STOCK ====================

@login_required
def current_stock(request):
    products = Product.objects.select_related('category').order_by('name')
    return render(request, 'inventory/current_stock.html', {'products': products})


@login_required
def low_stock(request):
    products = Product.objects.select_related('category').filter(
        stock_quantity__lte=F('reorder_level')
    ).order_by('stock_quantity', 'name')
    return render(request, 'inventory/low_stock.html', {'products': products})


@login_required
def stock_movement(request):
    products = Product.objects.all().order_by('name')
    movements = StockMovement.objects.select_related(
        'product'
    ).order_by('-created_at', '-id')
    search_query = request.GET.get('q', '').strip()

    if search_query:
        movements = movements.filter(
            product__name__icontains=search_query
        )

    if request.method == 'POST':
        product_id = request.POST.get('product', '').strip()
        movement_type = request.POST.get('movement_type', '').strip()
        reference = request.POST.get('reference', '').strip()
        notes = request.POST.get('notes', '').strip()

        try:
            quantity = int(request.POST.get('quantity', ''))

            if not product_id:
                messages.error(request, 'Select a product.')
            elif movement_type not in ('IN', 'OUT', 'ADJUSTMENT'):
                messages.error(request, 'Select a valid movement type.')
            elif quantity < 0 or (
                quantity == 0 and movement_type != 'ADJUSTMENT'
            ):
                messages.error(
                    request,
                    'Quantity must be positive. For adjustment, enter '
                    'the final stock quantity (zero or greater).'
                )
            else:
                with transaction.atomic():
                    product = get_object_or_404(
                        Product.objects.select_for_update(), id=product_id
                    )
                    previous_stock = product.stock_quantity

                    if movement_type == 'IN':
                        updated_stock = previous_stock + quantity
                        recorded_quantity = quantity
                    elif movement_type == 'OUT':
                        if quantity > previous_stock:
                            messages.error(
                                request,
                                'Stock Out exceeds available stock.'
                            )
                            return redirect('stock_movement')
                        updated_stock = previous_stock - quantity
                        recorded_quantity = quantity
                    else:
                        # ADJUSTMENT quantity is the desired final stock.
                        updated_stock = quantity
                        recorded_quantity = abs(
                            updated_stock - previous_stock
                        )
                        if updated_stock == previous_stock:
                            messages.info(
                                request,
                                'Stock is already at that quantity. '
                                'No changes were made.'
                            )
                            return redirect('stock_movement')

                    product.stock_quantity = updated_stock
                    product.save(update_fields=[
                        'stock_quantity', 'updated_at'
                    ])

                    StockMovement.objects.create(
                        product=product,
                        movement_type=movement_type,
                        quantity=recorded_quantity,
                        previous_stock=previous_stock,
                        updated_stock=updated_stock,
                        reference=reference,
                        notes=notes,
                    )

                messages.success(
                    request, 'Stock movement saved successfully.'
                )
                return redirect('stock_movement')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Enter a valid whole-number quantity.')

    return render(request, 'inventory/stock_movement.html', {
        'products': products,
        'movements': movements,
        'search_query': search_query,
    })

# ==================== SALES REPORT ====================

@login_required
def sales_report(request):
    orders_list = Order.objects.filter(status='Completed').select_related(
        'customer'
    ).prefetch_related('items__product')

    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    if from_date:
        try:
            start_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(datetime.combine(start_date, time.min))
            orders_list = orders_list.filter(order_date__gte=start_datetime)
        except ValueError:
            from_date = ''

    if to_date:
        try:
            end_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            end_datetime = timezone.make_aware(
                datetime.combine(end_date + timedelta(days=1), time.min)
            )
            orders_list = orders_list.filter(order_date__lt=end_datetime)
        except ValueError:
            to_date = ''

    orders_list = orders_list.order_by('-order_date')
    total_sales = orders_list.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_orders = orders_list.count()
    items_sold = OrderItem.objects.filter(
        order__in=orders_list
    ).aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, 'inventory/sales_report.html', {
        'orders': orders_list,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'items_sold': items_sold,
        'from_date': from_date,
        'to_date': to_date,
    })


# ==================== REORDER SUGGESTIONS ====================

@login_required
def reorder_suggestions(request):
    products = list(
        Product.objects.select_related('category').filter(
            stock_quantity__lte=F('reorder_level')
        ).order_by('stock_quantity', 'name')
    )

    for product in products:
        product.suggested_quantity = max(
            (product.reorder_level * 2) - product.stock_quantity, 0
        )

    return render(request, 'inventory/reorder_suggestions.html', {'products': products})


# ==================== SETTINGS ====================

@login_required
def settings(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'profile':
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not full_name:
                messages.error(request, 'Full name is required.')
            else:
                name_parts = full_name.split(maxsplit=1)
                user.first_name = name_parts[0]
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                user.email = email
                user.save()
                messages.success(request, 'Profile updated successfully.')

        elif action == 'account':
            username = request.POST.get('username', '').strip()

            if not username:
                messages.error(request, 'Username is required.')
            elif user.__class__.objects.filter(
                username=username
            ).exclude(pk=user.pk).exists():
                messages.error(request, 'Username already exists.')
            else:
                user.username = username
                user.save()
                messages.success(request, 'Username updated successfully.')

        return redirect('settings')

    return render(request, 'inventory/settings.html')
