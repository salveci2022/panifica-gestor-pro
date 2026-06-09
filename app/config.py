import os
import logging
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Chaves padrão com 32+ chars para satisfazer RFC 7518
_SECRET_KEY_DEFAULT     = "panifica-dev-secret-key-troque-em-producao-2026"
_JWT_SECRET_KEY_DEFAULT = "panifica-jwt-secret-key-troque-em-producao-2026"


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", _SECRET_KEY_DEFAULT)
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True

    # Banco de dados
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///panifica_dev.db")
    # Supabase requer postgresql+psycopg2:// e não postgresql://
    if _db_url and _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 120,
        "pool_size": 2,
        "max_overflow": 3,
        "pool_timeout": 30,
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
        } if os.environ.get("DATABASE_URL", "").startswith("postgresql") else {},
    }

    # JWT — chaves com mínimo de 32 bytes conforme RFC 7518
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", _JWT_SECRET_KEY_DEFAULT)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 8))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # Logs
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Segurança
    MAX_LOGIN_ATTEMPTS   = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))
    LOGIN_LOCKOUT_MINUTES= int(os.environ.get("LOGIN_LOCKOUT_MINUTES", 15))


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)


def validar_config_producao(app):
    """
    Chamado no startup. Loga aviso se chaves padrão são usadas em produção.
    Não bloqueia em desenvolvimento.
    """
    env = os.environ.get("FLASK_ENV", "development")
    if env != "production":
        return

    problemas = []
    if app.config["SECRET_KEY"] == _SECRET_KEY_DEFAULT:
        problemas.append("SECRET_KEY está com valor padrão — defina no .env")
    if app.config["JWT_SECRET_KEY"] == _JWT_SECRET_KEY_DEFAULT:
        problemas.append("JWT_SECRET_KEY está com valor padrão — defina no .env")
    if len(app.config["JWT_SECRET_KEY"]) < 32:
        problemas.append(f"JWT_SECRET_KEY tem {len(app.config['JWT_SECRET_KEY'])} chars — mínimo 32")

    for p in problemas:
        logger.critical("SEGURANÇA: %s", p)

    if problemas:
        raise RuntimeError(
            f"Configuração de produção insegura: {'; '.join(problemas)}"
        )
