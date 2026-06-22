import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cambiar_esta_clave_para_produccion')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///flaskcloud_adauthstock.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LDAP_SERVER = os.environ.get('LDAP_SERVER', 'ldap://localhost:389')
    LDAP_DOMAIN = os.environ.get('LDAP_DOMAIN', 'ifts.local')
    REMEMBER_COOKIE_DURATION = timedelta(days=7)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
