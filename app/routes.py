from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from io import StringIO
import csv

from . import db, login_manager
from .models import ADUser, Product, Movement
from .forms import LoginForm, ProductForm, MovementForm

from ldap3 import Server, Connection, ALL, NTLM

bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return ADUser.query.get(user_id)


def is_within_hours(start=8, end=18):
    now = datetime.now().hour
    return start <= now < end


def authenticate_ad(username, password):
    server_uri = current_app.config.get('LDAP_SERVER')
    domain = current_app.config.get('LDAP_DOMAIN')
    server = Server(server_uri, get_info=ALL)
    user = f"{domain}\\{username}"
    try:
        conn = Connection(server, user=user, password=password, authentication=NTLM, receive_timeout=10)
        if not conn.bind():
            return None
        # Obtener grupos del usuario (memberOf)
        conn.search(search_base=conn.server.info.other['defaultNamingContext'][0],
                    search_filter=f'(sAMAccountName={username})', attributes=['memberOf','displayName'])
        if conn.entries:
            entry = conn.entries[0]
            groups = []
            if 'memberOf' in entry:
                groups = [g.split(',')[0].replace('CN=','') for g in entry.memberOf]
            display = entry.displayName.value if 'displayName' in entry else username
            return {'username': username, 'display_name': display, 'groups': groups}
    except Exception as e:
        current_app.logger.exception('AD auth error')
    return None


@bp.route('/')
@login_required
def index():
    products = Product.query.all()
    return render_template('index.html', title='Inicio', products=products)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if not is_within_hours():
            flash('Acceso fuera del horario permitido (8-18 hs).', 'warning')
            return redirect(url_for('main.login'))
        data = authenticate_ad(form.username.data, form.password.data)
        if not data:
            flash('Credenciales inválidas.', 'danger')
            return redirect(url_for('main.login'))
        # Upsert user
        user = ADUser.query.get(data['username'])
        roles = ','.join(data.get('groups', []))
        if not user:
            user = ADUser(username=data['username'], display_name=data.get('display_name'), roles=roles)
            db.session.add(user)
        else:
            user.display_name = data.get('display_name')
            user.roles = roles
            user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user)
        flash('Ingreso exitoso.', 'success')
        return redirect(url_for('main.index'))
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


def has_role(user, role_name):
    if not user or not user.roles:
        return False
    return role_name in user.roles


@bp.route('/products')
@login_required
def products():
    prods = Product.query.all()
    return render_template('products.html', products=prods)


@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def product_new():
    if not has_role(current_user, 'Admin'):
        flash('Necesitas permisos de Admin para crear productos.', 'danger')
        return redirect(url_for('main.products'))
    form = ProductForm()
    if form.validate_on_submit():
        p = Product(nombre=form.nombre.data, descripcion=form.descripcion.data,
                    stock_actual=form.stock_actual.data or 0, stock_minimo=form.stock_minimo.data or 0,
                    precio=form.precio.data or 0.0)
        db.session.add(p)
        db.session.commit()
        flash('Producto creado.', 'success')
        return redirect(url_for('main.products'))
    return render_template('product_form.html', form=form)


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    if not has_role(current_user, 'Admin'):
        flash('Necesitas permisos de Admin para editar productos.', 'danger')
        return redirect(url_for('main.products'))
    p = Product.query.get_or_404(product_id)
    form = ProductForm(obj=p)
    if form.validate_on_submit():
        form.populate_obj(p)
        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('main.products'))
    return render_template('product_form.html', form=form)


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def product_delete(product_id):
    if not has_role(current_user, 'Admin'):
        flash('Necesitas permisos de Admin para eliminar productos.', 'danger')
        return redirect(url_for('main.products'))
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    flash('Producto eliminado.', 'success')
    return redirect(url_for('main.products'))


@bp.route('/movements', methods=['GET', 'POST'])
@login_required
def movements():
    if not (has_role(current_user, 'Admin') or has_role(current_user, 'Operador')):
        flash('No tienes permisos para cargar movimientos.', 'danger')
        return redirect(url_for('main.index'))
    form = MovementForm()
    form.producto_id.choices = [(p.id, p.nombre) for p in Product.query.all()]
    if form.validate_on_submit():
        m = Movement(producto_id=form.producto_id.data, tipo=form.tipo.data,
                     cantidad=form.cantidad.data, usuario=current_user.username)
        prod = Product.query.get(form.producto_id.data)
        if form.tipo.data == 'entrada':
            prod.stock_actual += form.cantidad.data
        else:
            prod.stock_actual -= form.cantidad.data
            if prod.stock_actual < 0:
                prod.stock_actual = 0
        db.session.add(m)
        db.session.commit()
        flash('Movimiento registrado.', 'success')
        return redirect(url_for('main.index'))
    movs = Movement.query.order_by(Movement.fecha.desc()).limit(100).all()
    return render_template('movements.html', form=form, movements=movs)


@bp.route('/reports/products.csv')
@login_required
def export_products_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'nombre', 'descripcion', 'stock_actual', 'stock_minimo', 'precio'])
    for p in Product.query.all():
        cw.writerow([p.id, p.nombre, p.descripcion or '', p.stock_actual, p.stock_minimo, p.precio])
    si.seek(0)
    return send_file(
        StringIO(si.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        attachment_filename='productos.csv')


@bp.route('/reports/movements.csv')
@login_required
def export_movements_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'producto_id', 'tipo', 'cantidad', 'fecha', 'usuario'])
    for m in Movement.query.order_by(Movement.fecha.desc()).all():
        cw.writerow([m.id, m.producto_id, m.tipo, m.cantidad, m.fecha.isoformat(), m.usuario])
    si.seek(0)
    return send_file(
        StringIO(si.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        attachment_filename='movimientos.csv')
