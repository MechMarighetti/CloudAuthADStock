# FlaskCloud-ADauthStock

Aplicación de ejemplo: autenticación contra Active Directory y gestión de stock.

Resumen:
- Autenticación contra AD (dominio: `ifts.local`) usando `ldap3`.
- Roles basados en grupos de AD: `Admin`, `Operador`, `Consulta`.
- Restricción horaria: solo permitir login entre 8 y 18 hs.
- Gestión de productos (ABM), movimientos y exportes CSV.

Requisitos:
- Python 3.8+

Instalación (Windows PowerShell):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Instalación (Linux/macOS):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Variables de entorno (opcional):
- `SECRET_KEY` — clave Flask
- `DATABASE_URL` — URI SQLAlchemy (por defecto SQLite `sqlite:///flaskcloud_adauthstock.db`)
- `LDAP_SERVER` — por defecto `ldap://ifts.local`
- `LDAP_DOMAIN` — por defecto `ifts.local`

Inicializar la base de datos:

```bash
python -c "from app import create_app, db; app=create_app();
with app.app_context(): db.create_all()"
```

Ejecutar la aplicación:

```bash
python run.py
```

Notas:
- Revisa `app/config.py` y define las variables de entorno necesarias.
- Para producción, configura un servidor WSGI y gestiona secretos fuera del repo.
# CloudAuthADStock
Repo del trabajo ráctico final de Implementacion de Sistemas en la Nube IFTS 18 - 2026
