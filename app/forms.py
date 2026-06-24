from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')


class ProductForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    genero = StringField('Género', validators=[DataRequired()])
    altura = SelectField('Altura', choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')])
    tipo_servicio = SelectField('Tipo de servicio', choices=[('SaaS', 'SaaS'), ('PaaS', 'PaaS'), ('IaaS', 'IaaS')])
    capacidad_almacenamiento = FloatField('Almacenamiento (GB)')
    capacidad_procesamiento = FloatField('Procesamiento (vCPUs)')
    memoria_ram = FloatField('Memoria RAM (GB)')
    precio_mensual = FloatField('Precio mensual ($)')
    escalable = bool('Escalable')
    descripcion = TextAreaField('Descripción')
    stock_disponible = IntegerField('Stock disponible', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Guardar')


class MovementForm(FlaskForm):
    producto_id = SelectField('Producto', coerce=int)
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada'), ('salida', 'Salida')])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registrar movimiento')

    def __repr__(self):
        return f'<Nube {self.genero} ({self.tipo_servicio})>'