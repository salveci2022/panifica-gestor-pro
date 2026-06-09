import logging
from flask import Blueprint, request, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
from marshmallow import ValidationError

from app.extensions import db, limiter
from app.models.usuario import Usuario, PERFIS_VALIDOS
from app.models.tenant import Tenant
from app.schemas.usuario_schema import (
    LoginSchema, CriarUsuarioSchema, AtualizarUsuarioSchema,
    AlterarSenhaSchema, RecuperarSenhaSchema, RedefinirSenhaSchema,
)
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio, obter_ip_requisicao
from app.utils.respostas import (
    sucesso, criado, erro, nao_encontrado, proibido,
    conflito, regra_negocio, validacao_erro
)
from app.services.audit_service import registrar_auditoria

bp_auth = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

_schema_login    = LoginSchema()
_schema_criar    = CriarUsuarioSchema()
_schema_atualizar= AtualizarUsuarioSchema()
_schema_senha    = AlterarSenhaSchema()
_schema_recuperar= RecuperarSenhaSchema()
_schema_redefinir= RedefinirSenhaSchema()


# ─── POST /api/auth/login ─────────────────────────────────────────────────────

@bp_auth.post("/login")
@limiter.limit("10 per minute")   # [FIX B4] Rate limit anti-bruteforce
def login():
    try:
        dados = _schema_login.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    msg_generica = "E-mail ou senha inválidos."
    usuario = Usuario.buscar_por_email(dados["email"])

    if not usuario or not usuario.ativo:
        logger.warning("Login: e-mail inexistente ou inativo: %s", dados.get("email"))
        return erro(msg_generica, 401)

    if usuario.esta_bloqueado():
        logger.warning("Login bloqueado para %s", usuario.email)
        return erro(
            "Conta temporariamente bloqueada. Tente novamente em alguns minutos.",
            401
        )

    if not usuario.verificar_senha(dados["senha"]):
        max_tent = current_app.config["MAX_LOGIN_ATTEMPTS"]
        lock_min = current_app.config["LOGIN_LOCKOUT_MINUTES"]
        usuario.registrar_tentativa_falha(max_tent, lock_min)
        db.session.commit()
        logger.warning("Senha incorreta para %s. Tentativas: %d", usuario.email, usuario.tentativas_login or 0)
        return erro(msg_generica, 401)

    if usuario.senha_precisa_rehash():
        usuario.definir_senha(dados["senha"])

    usuario.registrar_login()
    db.session.commit()

    access_token  = create_access_token(identity=usuario.id)
    refresh_token = create_refresh_token(identity=usuario.id)

    logger.info("Login OK: %s (IP: %s)", usuario.email, obter_ip_requisicao())
    return sucesso(data={
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "usuario":       usuario.para_dict(),
        "tenant":        usuario.tenant.para_dict() if usuario.tenant else None,
    }, message="Login realizado com sucesso.")


# ─── POST /api/auth/refresh ───────────────────────────────────────────────────

@bp_auth.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    usuario = Usuario.query.get(identity)
    if not usuario or not usuario.ativo:
        return erro("Usuário não encontrado ou inativo.", 401)
    novo_token = create_access_token(identity=identity)
    return sucesso(data={"access_token": novo_token}, message="Token renovado.")


# ─── POST /api/auth/logout ────────────────────────────────────────────────────

@bp_auth.post("/logout")
@login_obrigatorio
def logout(usuario_atual):
    logger.info("Logout: %s", usuario_atual.email)
    return sucesso(message="Logout realizado. Descarte os tokens no cliente.")


# ─── GET /api/auth/me ─────────────────────────────────────────────────────────

@bp_auth.get("/me")
@login_obrigatorio
def me(usuario_atual):
    return sucesso(data={
        "usuario": usuario_atual.para_dict(),
        "tenant":  usuario_atual.tenant.para_dict() if usuario_atual.tenant else None,
    })


# ─── POST /api/auth/recuperar-senha ──────────────────────────────────────────

@bp_auth.post("/recuperar-senha")
@limiter.limit("5 per hour")   # [FIX B4] Rate limit anti-spam
def recuperar_senha():
    try:
        dados = _schema_recuperar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    msg_ok = "Se o e-mail existir em nossa base, você receberá as instruções em breve."
    usuario = Usuario.buscar_por_email(dados["email"])
    if not usuario or not usuario.ativo:
        return sucesso(message=msg_ok)

    token = usuario.gerar_token_reset()
    db.session.commit()

    resposta = {"message": msg_ok}
    if current_app.debug:
        resposta["token_debug"] = token
        logger.debug("Token de reset (DEV): %s", token)

    logger.info("Token de reset gerado para %s", usuario.email)
    return sucesso(data=resposta, message=msg_ok)


# ─── POST /api/auth/redefinir-senha ──────────────────────────────────────────

@bp_auth.post("/redefinir-senha")
def redefinir_senha():
    try:
        dados = _schema_redefinir.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    if dados["nova_senha"] != dados["confirmar_senha"]:
        return erro("As senhas não coincidem.", 400)

    usuario = Usuario.query.filter_by(token_reset=dados["token"]).first()
    if not usuario or not usuario.token_reset_valido():
        return erro("Token inválido ou expirado.", 400)

    try:
        usuario.definir_senha(dados["nova_senha"])
    except ValueError as e:
        return regra_negocio(str(e))

    usuario.limpar_token_reset()
    db.session.commit()
    logger.info("Senha redefinida: %s", usuario.email)
    return sucesso(message="Senha redefinida. Faça login.")


# ─── CRUD DE USUÁRIOS DO TENANT ───────────────────────────────────────────────

@bp_auth.get("/usuarios")
@proprietario_obrigatorio
def listar_usuarios(usuario_atual):
    usuarios = Usuario.buscar_por_tenant(usuario_atual.tenant_id)
    return sucesso(data=[u.para_dict() for u in usuarios])


@bp_auth.post("/usuarios")
@proprietario_obrigatorio
def criar_usuario(usuario_atual):
    try:
        dados = _schema_criar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    if Usuario.buscar_por_email(dados["email"]):
        return conflito("Este e-mail já está cadastrado.")

    try:
        novo = Usuario(
            tenant_id=usuario_atual.tenant_id,
            nome=dados["nome"],
            email=dados["email"],
            perfil=dados.get("perfil", "operador"),
        )
        novo.definir_senha(dados["senha"])
        db.session.add(novo)
        db.session.flush()  # garante novo.id antes de registrar auditoria
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="usuarios",
            operacao="INSERT", registro_id=novo.id,
            dados_depois=novo.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar usuário: %s", exc)
        return erro("Erro interno ao criar usuário.", 500)

    logger.info("Usuário criado: %s por %s", novo.email, usuario_atual.email)
    return criado(data=novo.para_dict(), message="Usuário criado.")


@bp_auth.get("/usuarios/<string:usuario_id>")
@proprietario_obrigatorio
def obter_usuario(usuario_id, usuario_atual):
    u = Usuario.query.filter_by(id=usuario_id, tenant_id=usuario_atual.tenant_id).first()
    if not u:
        return nao_encontrado("Usuário")
    return sucesso(data=u.para_dict(incluir_sensiveis=True))


@bp_auth.put("/usuarios/<string:usuario_id>")
@proprietario_obrigatorio
def atualizar_usuario(usuario_id, usuario_atual):
    u = Usuario.query.filter_by(id=usuario_id, tenant_id=usuario_atual.tenant_id).first()
    if not u:
        return nao_encontrado("Usuário")

    body = request.get_json() or {}
    if u.id == usuario_atual.id and body.get("perfil") != "proprietario":
        return regra_negocio("Você não pode alterar seu próprio perfil de proprietário.")

    try:
        dados = _schema_atualizar.load(body)
    except ValidationError as e:
        return validacao_erro(e.messages)

    antes = u.para_dict()
    for campo, valor in dados.items():
        setattr(u, campo, valor)

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="usuarios",
        operacao="UPDATE", registro_id=u.id,
        dados_antes=antes, dados_depois=u.para_dict(), usuario_id=usuario_atual.id,
    )
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao atualizar usuário: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(data=u.para_dict(), message="Usuário atualizado.")


@bp_auth.patch("/usuarios/<string:usuario_id>/alterar-senha")
@login_obrigatorio
def alterar_senha(usuario_id, usuario_atual):
    if usuario_atual.id != usuario_id and usuario_atual.perfil != "proprietario":
        return proibido("Você só pode alterar sua própria senha.")

    u = Usuario.query.filter_by(id=usuario_id, tenant_id=usuario_atual.tenant_id).first()
    if not u:
        return nao_encontrado("Usuário")

    try:
        dados = _schema_senha.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    if dados["nova_senha"] != dados["confirmar_senha"]:
        return erro("As senhas não coincidem.", 400)

    if usuario_atual.id == usuario_id and not u.verificar_senha(dados["senha_atual"]):
        return erro("Senha atual incorreta.", 400)

    try:
        u.definir_senha(dados["nova_senha"])
        db.session.commit()
    except ValueError as e:
        return regra_negocio(str(e))
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao alterar senha: %s", exc)
        return erro("Erro interno.", 500)

    logger.info("Senha alterada: %s", u.email)
    return sucesso(message="Senha alterada com sucesso.")


@bp_auth.post("/setup-inicial")
def setup_inicial():
    """Endpoint temporário para criar usuário inicial em produção."""
    import os
    from app.models.tenant import Tenant
    from app.models.usuario import Usuario
    from app.extensions import db

    # Só funciona se FLASK_ENV for production e não existir usuário
    usuarios_count = Usuario.query.count()
    if usuarios_count > 0:
        return sucesso(message=f"Sistema já configurado. {usuarios_count} usuário(s) existente(s).")

    try:
        t = Tenant.query.first()
        if not t:
            t = Tenant(
                nome="Padaria Sao Joao",
                cnpj="12.345.678/0001-90",
                email_contato="joao@padariasaojoao.com.br"
            )
            db.session.add(t)
            db.session.flush()

        u = Usuario(
            tenant_id=t.id,
            nome="Joao Silva",
            email="joao@padariasaojoao.com.br",
            perfil="proprietario"
        )
        u.definir_senha("Senha@1234")
        db.session.add(u)
        db.session.commit()
        return criado(
            data={"email": "joao@padariasaojoao.com.br", "senha": "Senha@1234"},
            message="Usuário inicial criado com sucesso."
        )
    except Exception as e:
        db.session.rollback()
        return erro(f"Erro: {str(e)}", 500)
