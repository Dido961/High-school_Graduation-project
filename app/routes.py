from flask import session, Blueprint, render_template, request, redirect, url_for, current_app, flash
from app.models import Product, User, Order, OrderItem, UserProduct, PaymentStatus
from app import bcrypt
import os
from werkzeug.utils import secure_filename
import random

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    session_db = current_app.session

    query = request.args.get('query')
    category = request.args.get('category')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    products_query = session_db.query(Product)

    if query:
        products_query = products_query.filter(Product.name.ilike(f'%{query}%'))

    if category:
        products_query = products_query.filter_by(category=category)

    if min_price:
        products_query = products_query.filter(Product.price >= float(min_price))

    if max_price:
        products_query = products_query.filter(Product.price <= float(max_price))

    products = products_query.all()

    categories = session_db.query(Product.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    is_admin = False
    user_id = session.get('user_id')
    if user_id:
        user = session_db.query(User).get(user_id)
        if user and user.is_admin:
            is_admin = True

    return render_template('index.html', products=products, categories=categories, is_admin=is_admin)


@main.route('/add-product', methods=['GET', 'POST'])
def add_product():
    db_session = current_app.session

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category = request.form['category']
        image_url = request.form.get('image_url')  # Optional

        image_file = request.files.get('image_file')
        filename = None

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(os.path.join(current_app.root_path, image_path))
            image_url = '/' + image_path.replace('\\', '/')  # За HTML достъп

        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            image_url=image_url
        )
        db_session.add(product)
        db_session.commit()

        # Добави асоциация потребител-продукт
        user_product = UserProduct(user_id=session['user_id'], product_id=product.id)
        db_session.add(user_product)
        db_session.commit()

        flash('Продуктът беше добавен успешно.')
        return redirect(url_for('main.my_products'))

    return render_template('add_product.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    session_db = current_app.session

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = session_db.query(User).filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Успешен вход!')
            return redirect(url_for('main.index'))
        else:
            flash('Невалидни данни за вход.')

    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    session_db = current_app.session

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        admin_secret = request.form.get('admin_secret')

        if not username or not email or not password:
            flash('Моля, попълнете всички задължителни полета.')
            return redirect(url_for('main.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        # Проверка за админ секретна парола
        is_admin = admin_secret == "admin"

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            is_admin=is_admin
        )

        session_db.add(new_user)
        session_db.commit()
        flash('Регистрацията е успешна.')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/logout')
def logout():
    session.clear()
    flash('Излезе от акаунта.')
    return redirect(url_for('main.index'))

@main.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    session_db = current_app.session
    product = session_db.query(Product).filter_by(id=product_id).first()

    if not product:
        flash('Продуктът не съществува.')
        return redirect(url_for('main.index'))

    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash('Добавено в количката.')
    return redirect(url_for('main.index'))

@main.route('/cart')
def cart():
    session_db = current_app.session
    cart = session.get('cart', {})
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = session_db.query(Product).get(int(product_id))
        if product:
            subtotal = product.price * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

    return render_template('cart.html', items=items, total=total)

def is_admin():
    user_id = session.get('user_id')
    if not user_id:
        return False
    session_db = current_app.session
    user = session_db.query(User).get(user_id)
    return user and user.is_admin

@main.route('/admin/products')
def admin_products():
    if not is_admin():
        flash('Достъп само за администратори.')
        return redirect(url_for('main.index'))

    session_db = current_app.session
    products = session_db.query(Product).all()
    return render_template('admin_products.html', products=products)

@main.route('/admin/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_admin():
        flash('Достъп само за администратори.')
        return redirect(url_for('main.index'))

    session_db = current_app.session
    product = session_db.query(Product).get(product_id)
    if product:
        session_db.delete(product)
        session_db.commit()
        flash('Продуктът е изтрит.')
    else:
        flash('Продуктът не беше намерен.')

    return redirect(url_for('main.admin_products'))

@main.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not is_admin():
        flash('Достъп само за администратори.')
        return redirect(url_for('main.index'))

    session_db = current_app.session
    product = session_db.query(Product).get(product_id)

    if not product:
        flash('Продуктът не съществува.')
        return redirect(url_for('main.admin_products'))

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.stock = int(request.form.get('stock'))
        product.image_url = request.form.get('image_url')

        session_db.commit()
        flash('Продуктът е обновен успешно.')
        return redirect(url_for('main.admin_products'))

    return render_template('edit_product.html', product=product)

@main.route('/place-order', methods=['GET', 'POST'])
def place_order():
    if not session.get('user_id'):
        flash('Трябва да влезеш в акаунта си, за да направиш поръчка.')
        return redirect(url_for('main.login'))

    db_session = current_app.session
    cart = session.get('cart', {})
    if not cart:
        flash('Количката е празна.')
        return redirect(url_for('main.cart'))

    if request.method == 'POST':
        user_id = session['user_id']
        new_order = Order(user_id=user_id, status='pending', payment_status='pending')
        db_session.add(new_order)
        db_session.flush()  # За да получим order.id

        for product_id, quantity in cart.items():
            product = db_session.query(Product).get(int(product_id))
            if product:
                if product.stock >= quantity:
                    product.stock -= quantity  # ← Намаляване на наличността

                    order_item = OrderItem(
                        order=new_order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    db_session.add(order_item)
                else:
                    flash(f'Недостатъчна наличност за {product.name}')
                    return redirect(url_for('main.cart'))

        db_session.commit()
        session.pop('cart', None)
        return redirect(url_for('main.pay_order', order_id=new_order.id))

    # GET: показваме избор на метод за плащане
    return render_template('confirm_order.html')


@main.route('/my-products')
def my_products():
    if not session.get('user_id'):
        flash('Моля, влез в акаунта си.')
        return redirect(url_for('main.login'))

    session_db = current_app.session
    user = session_db.query(User).get(session['user_id'])

    return render_template('my_products.html', products=user.added_products)

@main.route('/my-products/edit/<int:product_id>', methods=['GET', 'POST'])
def user_edit_product(product_id):
    db_session = current_app.session
    user_id = session.get('user_id')
    if not user_id:
        flash('Моля, влез в акаунта си.')
        return redirect(url_for('main.login'))

    # Проверка дали потребителят притежава продукта
    link = db_session.query(UserProduct).filter_by(user_id=user_id, product_id=product_id).first()
    if not link:
        flash('Нямаш достъп до този продукт.')
        return redirect(url_for('main.my_products'))

    product = db_session.query(Product).get(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.stock = int(request.form.get('stock'))
        product.image_url = request.form.get('image_url')

        db_session.commit()
        flash('Продуктът е обновен.')
        return redirect(url_for('main.my_products'))

    return render_template('edit_product.html', product=product)

@main.route('/my-products/delete/<int:product_id>', methods=['POST'])
def user_delete_product(product_id):
    db_session = current_app.session
    user_id = session.get('user_id')
    if not user_id:
        flash('Моля, влез в акаунта си.')
        return redirect(url_for('main.login'))

    # Проверка дали потребителят е свързан с продукта
    link = db_session.query(UserProduct).filter_by(user_id=user_id, product_id=product_id).first()
    if not link:
        flash('Нямаш достъп до този продукт.')
        return redirect(url_for('main.my_products'))

    product = db_session.query(Product).get(product_id)

    # Изтриване на релацията и самия продукт
    db_session.delete(link)
    db_session.delete(product)
    db_session.commit()
    flash('Продуктът е изтрит.')
    return redirect(url_for('main.my_products'))

@main.route('/admin/users')
def admin_users():
    if not is_admin():
        flash('Достъп само за администратори.')
        return redirect(url_for('main.index'))

    session_db = current_app.session
    users = session_db.query(User).all()
    return render_template('admin_users.html', users=users)

@main.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not is_admin():
        flash('Достъп само за администратори.')
        return redirect(url_for('main.index'))

    session_db = current_app.session
    current_user_id = session.get('user_id')

    if user_id == current_user_id:
        flash('Не можеш да изтриеш собствения си акаунт.')
        return redirect(url_for('main.admin_users'))

    user = session_db.query(User).get(user_id)
    if user:
        # Може да добавим каскадно изтриване при нужда
        session_db.delete(user)
        session_db.commit()
        flash('Потребителят беше изтрит.')
    else:
        flash('Потребителят не съществува.')

    return redirect(url_for('main.admin_users'))

@main.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    db_session = current_app.session
    user_id = session.get('user_id')

    if not user_id:
        flash('Моля, влез в акаунта си.')
        return redirect(url_for('main.login'))

    user = db_session.query(User).get(user_id)

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')

        if new_username:
            user.username = new_username

        if new_email:
            user.email = new_email


        db_session.commit()
        flash('Профилът е обновен успешно.')
        return redirect(url_for('main.index'))

    return render_template('edit_profile.html', user=user)

@main.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart_quantity(product_id):
    quantity = request.form.get('quantity')
    cart = session.get('cart', {})
    try:
        quantity = int(quantity)
        if quantity > 0:
            cart[str(product_id)] = quantity
            session['cart'] = cart
            flash('Количеството е обновено.')
    except (ValueError, TypeError):
        flash('Невалидно количество.')

    return redirect(url_for('main.cart'))


@main.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        session['cart'] = cart
        flash('Продуктът беше премахнат от количката.')

    return redirect(url_for('main.cart'))

@main.route('/cart/clear', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    flash('Количката е изчистена.')
    return redirect(url_for('main.cart'))

@main.route('/my-orders')
def my_orders():
    user_id = session.get('user_id')
    if not user_id:
        flash('Моля, влез в акаунта си.')
        return redirect(url_for('main.login'))

    db_session = current_app.session
    orders = db_session.query(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    for order in orders:
        order.total_price = sum(item.price * item.quantity for item in order.items)
    return render_template('my_orders.html', orders=orders)


@main.route('/admin/orders')
def admin_orders():
    if not is_admin():
        flash('Достъп само за администратори.')
        return redirect(url_for('main.index'))

    db_session = current_app.session
    orders = db_session.query(Order).order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)


@main.route('/pay/<int:order_id>', methods=['GET', 'POST'])
def pay_order(order_id):
    db_session = current_app.session
    user_id = session.get('user_id')
    if not user_id:
        flash('Моля, влез в акаунта си.')
        return redirect(url_for('main.login'))

    order = db_session.query(Order).get(order_id)

    if not order or order.user_id != user_id:
        flash('Нямаш достъп до тази поръчка.')
        return redirect(url_for('main.my_orders'))

    if request.method == 'POST':
        # Симулираме резултат от "плащане"
        success = random.choice([True, False])
        if success:
            order.payment_status = PaymentStatus.success
            flash('Плащането е успешно!')
        else:
            order.payment_status = PaymentStatus.failed
            flash('Плащането е отказано.')

        db_session.commit()
        return redirect(url_for('main.my_orders'))
    total = sum(item.price * item.quantity for item in order.items)
    return render_template('pay_order.html', order=order, total=round(total, 2))


@main.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():
        flash("Само за администратори.")
        return redirect(url_for('main.index'))
    return render_template('admin_dashboard.html')

@main.route('/admin/orders/<int:order_id>/update', methods=['POST'])
def update_order_status(order_id):
    db = current_app.session
    order = db.query(Order).get(order_id)

    if not order:
        flash('Поръчката не е намерена.')
        return redirect(url_for('main.admin_orders'))

    order.status = request.form.get('status')
    order.payment_status = request.form.get('payment_status')
    db.commit()

    flash('Статусите бяха обновени успешно.')
    return redirect(url_for('main.admin_orders'))

from werkzeug.security import generate_password_hash

@main.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
def admin_edit_profile(user_id):
    db = current_app.session
    user = db.query(User).get(user_id)

    if not user:
        flash('Потребителят не е намерен.')
        return redirect(url_for('main.admin_users'))

    if request.method == 'POST':
        if 'delete_user' in request.form:
            db.delete(user)
            db.commit()
            flash('Потребителят беше изтрит.')
            return redirect(url_for('main.admin_users'))

        user.username = request.form['username']
        user.email = request.form['email']
        user.is_admin = 'is_admin' in request.form

        # Промяна на парола (по избор)
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.commit()
        flash('Профилът беше обновен успешно.')
        return redirect(url_for('main.admin_users'))

    return render_template('admin_edit_profile.html', user=user)

@main.route('/pay/test/<int:order_id>', methods=['GET', 'POST'])
def pay_test(order_id):
    db = current_app.session
    order = db.query(Order).get(order_id)

    if not order or order.user_id != session.get('user_id'):
        flash('Невалидна поръчка.')
        return redirect(url_for('main.cart'))

    if request.method == 'POST':
        # Тук се предполага, че сме въвели валидна информация
        order.payment_status = PaymentStatus.success
        order.status = 'pending'
        db.commit()
        flash('Плащането е успешно обработено (тестово).')
        return redirect(url_for('main.my_orders'))

    return render_template('pay_test.html', order=order)



