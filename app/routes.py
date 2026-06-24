from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from io import StringIO
from functools import wraps
import csv
import io

from . import db, login_manager
from .models import ADUser, Product, Movement
from .forms import LoginForm, ProductForm, MovementForm

from ldap3 import Server, Connection, ALL, SIMPLE

bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return ADUser.query.get(user_id)


def is_within_hours(start=8, end=23):
    now = datetime.now().hour
    return start <= now < end

def map_ad_groups_to_roles(ad_groups):
    mapped = set()
    for g in ad_groups:
        g_str = str(g)
        if 'SC_Administradores' in g_str:
            mapped.add('admin')
        if 'SC_Operadores' in g_str:
            mapped.add('operador')
        if 'SC_Consultores' in g_str:
            mapped.add('consultor')
    return list(mapped)


def autenticar_ad(username: str, password: str) -> dict | None:
    AD_SERVER = "ldap://192.168.56.10"
    AD_DOMAIN = "IFTS.LOCAL"
    AD_BASE_DN = "DC=IFTS,DC=LOCAL"

    server = Server(AD_SERVER, get_info=ALL)
    conn = Connection(
        server,
        user=f"{username}@{AD_DOMAIN}",
        password=password,
        authentication=SIMPLE,
        auto_bind=True
    )

    conn.search(
        search_base=AD_BASE_DN,
        search_filter=f"(sAMAccountName={username})",
        attributes=["memberOf", "displayName", "mail"]
    )

    if not conn.entries:
        return None

    entry = conn.entries[0]
    ad_groups = entry.memberOf.values if hasattr(entry.memberOf, 'values') else entry.memberOf
    internal_roles = map_ad_groups_to_roles(ad_groups)

    return {
        "username": username,
        "display_name": str(entry.displayName),
        "ad_groups": ad_groups,
        "roles": internal_roles
    }

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
        data = autenticar_ad(form.username.data, form.password.data)
        if not data:
            flash('Credenciales inválidas.', 'danger')
            return redirect(url_for('main.login'))
        # Upsert user
        user = ADUser.query.get(data['username'])
        roles = ','.join(data.get('roles', []))  # ahora son roles internos: 'admin','operador','consultor'
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


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            for r in roles:
                if current_user.has_role(r):
                    return f(*args, **kwargs)
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('main.index'))
        return wrapped
    return decorator

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

def products():
    prods = Product.query.all()
    return render_template('products.html', products=prods)


@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'operador')
def product_new():
    if has_role(current_user, 'consultor'):
        flash('Necesitas permisos para crear productos.', 'danger')
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
@roles_required('admin', 'operador')
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
@roles_required('admin')
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
@roles_required('admin', 'operador', 'consultor')
def movements():
    """ if not (has_role(current_user, 'Admin') or has_role(current_user, 'Operador')):
        flash('No tienes permisos para cargar movimientos.', 'danger')
        return redirect(url_for('main.index')) """
    form = MovementForm()
    form.producto_id.choices = [(p.id, p.nombre) for p in Product.query.all()]
    if form.validate_on_submit():
        m = Movement(producto_id=form.producto_id.data, tipo=form.tipo.data,
                     cantidad=form.cantidad.data, usuario=current_user.username)
        prod = Product.query.get(form.producto_id.data)
        if form.tipo.data == 'entrada':
            prod.stock_disponible += form.cantidad.data
        else:
            prod.stock_disponible -= form.cantidad.data
            if prod.stock_disponible < 0:
                prod.stock_disponible = 0
        db.session.add(m)
        db.session.commit()
        flash('Movimiento registrado.', 'success')
        return redirect(url_for('main.index'))
    movs = Movement.query.order_by(Movement.fecha.desc()).limit(100).all()
    return render_template('movements.html', form=form, movements=movs)


@bp.route('/reports/products.csv')
@login_required
@roles_required('admin', 'operador', 'consultor')
def export_products_csv():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'nombre', 'descripcion', 'stock_disponible', 'precio'])
    for p in Product.query.all():
        cw.writerow([p.id, p.nombre, p.descripcion or '', p.stock_disponible, p.precio_mensual])
    si_bytes = io.BytesIO(si.getvalue().encode('utf-8'))
    si_bytes.seek(0)
    return send_file(
        si_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name='productos.csv')


@bp.route('/reports/movements.csv')
@login_required
@roles_required('admin', 'operador', 'consultor')
def export_movements_csv():
    # 1. Escribir el CSV en un StringIO (texto)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'producto_id', 'tipo', 'cantidad', 'fecha', 'usuario'])
    for m in Movement.query.order_by(Movement.fecha.desc()).all():
        writer.writerow([m.id, m.producto_id, m.tipo, m.cantidad, m.fecha.isoformat(), m.usuario])
    
    # 2. Convertir a BytesIO (binario) y posicionar al inicio
    output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
    output_bytes.seek(0)
    
    # 3. Enviar como adjunto
    return send_file(
        output_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name='movimientos.csv'
    )