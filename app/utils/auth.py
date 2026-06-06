import logging
from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.models.usuario import Usuario

logger = logging.getLogger(__name__)


def _obter_usuario_atual() -> Usuario | None:
    """Obtém o usuário logado a partir do JWT identity."""
    identidade = get_jwt_identity()
    if not identidade:
        return None
    return Usuario.query.get(identidade)


def login_obrigatorio(f):
    """Decorator: exige JWT válido. Injeta `usuario_atual` no kwargs."""
    @wraps(f)
    def decorada(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({"ok": False, "error": "Autenticação necessária.", "code": 401}), 401

        usuario = _obter_usuario_atual()
        if not usuario:
            return jsonify({"ok": False, "error": "Usuário não encontrado.", "code": 401}), 401
        if not usuario.ativo:
            return jsonify({"ok": False, "error": "Conta desativada.", "code": 403}), 403

        kwargs["usuario_atual"] = usuario
        return f(*args, **kwargs)
    return decorada


def perfil_obrigatorio(*perfis):
    """Decorator: exige um dos perfis listados após autenticação."""
    def decorador(f):
        @wraps(f)
        @login_obrigatorio
        def decorada(*args, **kwargs):
            usuario = kwargs.get("usuario_atual")
            if usuario.perfil not in perfis:
                logger.warning(
                    "Acesso negado: usuário %s (perfil=%s) tentou acessar rota restrita a %s",
                    usuario.email, usuario.perfil, perfis
                )
                return jsonify({
                    "ok": False,
                    "error": f"Acesso restrito a: {', '.join(perfis)}.",
                    "code": 403
                }), 403
            return f(*args, **kwargs)
        return decorada
    return decorador


def proprietario_obrigatorio(f):
    """Atalho para @perfil_obrigatorio('proprietario')."""
    return perfil_obrigatorio("proprietario")(f)


def obter_ip_requisicao() -> str:
    """Extrai IP real considerando proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "desconhecido"


def obter_user_agent() -> str:
    return request.headers.get("User-Agent", "")[:500]
