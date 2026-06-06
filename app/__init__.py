import logging
import os
from flask import Flask, jsonify, request

from app.config import get_config, validar_config_producao
from app.extensions import db, migrate, jwt, cors, limiter


def create_app(config_class=None):
    app = Flask(__name__)
    cfg = config_class or get_config()
    app.config.from_object(cfg)

    _configurar_logging(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)

    validar_config_producao(app)
    _registrar_blueprints(app)
    _registrar_error_handlers(app)
    _registrar_jwt_callbacks(app)
    _registrar_security_headers(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "app": "PANIFICA GESTOR PRO", "versao": "1.3"}), 200

    env = os.environ.get("FLASK_ENV", "development")
    app.logger.info("PANIFICA GESTOR PRO v1.3 iniciado em modo %s", env)
    return app


def _configurar_logging(app):
    nivel = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.logger.setLevel(nivel)


def _registrar_blueprints(app):
    from app.blueprints.auth.routes         import bp_auth
    from app.blueprints.dashboard.routes    import bp_dashboard
    from app.blueprints.financeiro.routes   import bp_financeiro
    from app.blueprints.fornecedores.routes import bp_fornecedores
    from app.blueprints.estoque.routes      import bp_estoque
    from app.blueprints.compras.routes      import bp_compras
    from app.blueprints.producao.routes     import bp_producao
    from app.blueprints.notificacoes.routes import bp_notificacoes
    from app.blueprints.lojas.routes         import bp_lojas
    from app.blueprints.relatorios.routes    import bp_relatorios

    app.register_blueprint(bp_auth,          url_prefix="/api/auth")
    app.register_blueprint(bp_dashboard,     url_prefix="/api/dashboard")
    app.register_blueprint(bp_financeiro,    url_prefix="/api/contas")
    app.register_blueprint(bp_fornecedores,  url_prefix="/api/fornecedores")
    app.register_blueprint(bp_estoque,       url_prefix="/api/estoque")
    app.register_blueprint(bp_compras,       url_prefix="/api/compras")
    app.register_blueprint(bp_producao,      url_prefix="/api/producao")
    app.register_blueprint(bp_notificacoes,  url_prefix="/api/notificacoes")
    app.register_blueprint(bp_lojas,          url_prefix="/api/lojas")
    app.register_blueprint(bp_relatorios,    url_prefix="/api/relatorios")


def _registrar_security_headers(app):
    @app.after_request
    def adicionar_headers(response):
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]            = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]         = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"]    = "default-src 'none'; frame-ancestors 'none'"
        response.headers.pop("Server", None)
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def _registrar_error_handlers(app):
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"ok": False, "error": "Requisição inválida.", "code": 400}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"ok": False, "error": "Não autenticado.", "code": 401}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"ok": False, "error": "Acesso negado.", "code": 403}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"ok": False, "error": "Recurso não encontrado.", "code": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"ok": False, "error": "Método não permitido.", "code": 405}), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"ok": False, "error": str(e), "code": 422}), 422

    @app.errorhandler(429)
    def rate_limit(e):
        return jsonify({"ok": False, "error": "Muitas requisições.", "code": 429}), 429

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception("Erro interno: %s", e)
        return jsonify({"ok": False, "error": "Erro interno do servidor.", "code": 500}), 500

    @app.errorhandler(HTTPException)
    def handle_http(e):
        return jsonify({"ok": False, "error": e.description, "code": e.code}), e.code


def _registrar_jwt_callbacks(app):
    @jwt.expired_token_loader
    def token_expirado(jwt_header, jwt_payload):
        return jsonify({"ok": False, "error": "Token expirado.", "code": 401}), 401

    @jwt.invalid_token_loader
    def token_invalido(reason):
        return jsonify({"ok": False, "error": "Token inválido.", "code": 401}), 401

    @jwt.unauthorized_loader
    def sem_token(reason):
        return jsonify({"ok": False, "error": "Token não fornecido.", "code": 401}), 401

    @jwt.revoked_token_loader
    def token_revogado(jwt_header, jwt_payload):
        return jsonify({"ok": False, "error": "Token revogado.", "code": 401}), 401
