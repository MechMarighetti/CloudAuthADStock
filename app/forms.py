from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')


class ProductForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')
    stock_actual = IntegerField('Stock actual', validators=[NumberRange(min=0)])
    stock_minimo = IntegerField('Stock mínimo', validators=[NumberRange(min=0)])
    precio = FloatField('Precio')
    submit = SubmitField('Guardar')


class MovementForm(FlaskForm):
    producto_id = SelectField('Producto', coerce=int)
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada'), ('salida', 'Salida')])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registrar movimiento')
