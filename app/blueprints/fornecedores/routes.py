import logging
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.fornecedor import Fornecedor, CATEGORIAS_FORNECEDOR
from app.schemas.fornecedor_schema import CriarFornecedorSchema, AtualizarFornecedorSchema
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import (
    sucesso, criado, sem_conteudo, erro, nao_encontrado,
    conflito, regra_negocio, validacao_erro
)
from app.services.audit_service import registrar_auditoria

bp_fornecedores = Blueprint("fornecedores", __name__)
logger = logging.getLogger(__name__)

_schema_criar = CriarFornecedorSchema()
_schema_atualizar = AtualizarFornecedorSchema()


# ─── GET /api/fornecedores ────────────────────────────────────────────────────

@bp_fornecedores.get("")
@login_obrigatorio
def listar(usuario_atual):
    """
    Lista fornecedores do tenant.
    Query params: busca (nome), categoria, inativos (bool)
    """
    tid = usuario_atual.tenant_id
    busca = request.args.get("busca")
    categoria = request.args.get("categoria")
    incluir_inativos = request.args.get("inativos", "false").lower() == "true"

    q = Fornecedor.query.filter_by(tenant_id=tid)
    if not incluir_inativos:
        q = q.filter_by(ativo=True)
    if busca:
        q = q.filter(Fornecedor.nome.ilike(f"%{busca}%"))
    if categoria:
        q = q.filter_by(categoria=categoria)

    fornecedores = q.order_by(Fornecedor.nome.asc()).all()
    return sucesso(data=[f.para_dict() for f in fornecedores])


# ─── POST /api/fornecedores ───────────────────────────────────────────────────

@bp_fornecedores.post("")
@login_obrigatorio
def criar(usuario_atual):
    """Cadastra novo fornecedor."""
    try:
        dados = _schema_criar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    # Verifica duplicidade por CNPJ/CPF dentro do tenant
    if dados.get("cnpj_cpf"):
        existente = Fornecedor.query.filter_by(
            tenant_id=usuario_atual.tenant_id,
            cnpj_cpf=dados["cnpj_cpf"],
        ).first()
        if existente:
            return conflito(f"Já existe um fornecedor com o CNPJ/CPF '{dados['cnpj_cpf']}'.")

    try:
        forn = Fornecedor(
            tenant_id=usuario_atual.tenant_id,
            nome=dados["nome"],
            cnpj_cpf=dados.get("cnpj_cpf"),
            categoria=dados["categoria"],
            telefone=dados.get("telefone"),
            whatsapp=dados.get("whatsapp"),
            email=dados.get("email"),
            contato_nome=dados.get("contato_nome"),
            endereco=dados.get("endereco"),
            observacoes=dados.get("observacoes"),
        )
        db.session.add(forn)
        db.session.flush()  # garante forn.id antes de registrar auditoria
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id,
            tabela="fornecedores",
            operacao="INSERT",
            registro_id=forn.id,
            dados_depois=forn.para_dict(),
            usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar fornecedor: %s", exc)
        return erro("Erro interno ao criar fornecedor.", 500)

    logger.info("Fornecedor criado: %s por %s", forn.nome, usuario_atual.email)
    return criado(data=forn.para_dict(), message="Fornecedor cadastrado com sucesso.")


# ─── GET /api/fornecedores/<id> ───────────────────────────────────────────────

@bp_fornecedores.get("/<string:forn_id>")
@login_obrigatorio
def obter(forn_id, usuario_atual):
    """Detalha fornecedor com totais de contas abertas."""
    forn = Fornecedor.buscar_por_tenant_e_id(usuario_atual.tenant_id, forn_id)
    if not forn:
        return nao_encontrado("Fornecedor")

    # Histórico recente de contas
    from app.models.conta_pagar import ContaPagar
    contas = ContaPagar.query.filter_by(
        tenant_id=usuario_atual.tenant_id,
        fornecedor_id=forn_id
    ).order_by(ContaPagar.criado_em.desc()).limit(10).all()

    dados = forn.para_dict(incluir_totais=True)
    dados["contas_recentes"] = [c.para_dict() for c in contas]
    return sucesso(data=dados)


# ─── PUT /api/fornecedores/<id> ───────────────────────────────────────────────

@bp_fornecedores.put("/<string:forn_id>")
@login_obrigatorio
def atualizar(forn_id, usuario_atual):
    """Atualiza dados do fornecedor."""
    forn = Fornecedor.buscar_por_tenant_e_id(usuario_atual.tenant_id, forn_id)
    if not forn:
        return nao_encontrado("Fornecedor")

    try:
        dados = _schema_atualizar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    # Verifica duplicidade de CNPJ se estiver sendo alterado
    if "cnpj_cpf" in dados and dados["cnpj_cpf"]:
        existente = Fornecedor.query.filter(
            Fornecedor.tenant_id == usuario_atual.tenant_id,
            Fornecedor.cnpj_cpf == dados["cnpj_cpf"],
            Fornecedor.id != forn_id,
        ).first()
        if existente:
            return conflito(f"Já existe outro fornecedor com o CNPJ/CPF '{dados['cnpj_cpf']}'.")

    antes = forn.para_dict()
    for campo, valor in dados.items():
        setattr(forn, campo, valor)

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id,
        tabela="fornecedores",
        operacao="UPDATE",
        registro_id=forn.id,
        dados_antes=antes,
        dados_depois=forn.para_dict(),
        usuario_id=usuario_atual.id,
    )

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao atualizar fornecedor: %s", exc)
        return erro("Erro interno ao atualizar fornecedor.", 500)

    return sucesso(data=forn.para_dict(), message="Fornecedor atualizado.")


# ─── DELETE /api/fornecedores/<id> ────────────────────────────────────────────

@bp_fornecedores.delete("/<string:forn_id>")
@proprietario_obrigatorio
def deletar(forn_id, usuario_atual):
    """Soft delete do fornecedor (marca ativo=False)."""
    forn = Fornecedor.buscar_por_tenant_e_id(usuario_atual.tenant_id, forn_id)
    if not forn:
        return nao_encontrado("Fornecedor")

    # Verifica se há contas pendentes vinculadas
    from app.models.conta_pagar import ContaPagar
    contas_abertas = ContaPagar.query.filter_by(
        tenant_id=usuario_atual.tenant_id,
        fornecedor_id=forn_id,
        status="pendente"
    ).count()

    if contas_abertas > 0:
        return regra_negocio(
            f"Este fornecedor possui {contas_abertas} conta(s) pendente(s). "
            f"Resolva-as antes de desativar o fornecedor."
        )

    antes = forn.para_dict()
    forn.desativar()

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id,
        tabela="fornecedores",
        operacao="DELETE",
        registro_id=forn.id,
        dados_antes=antes,
        dados_depois=forn.para_dict(),
        usuario_id=usuario_atual.id,
    )

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao desativar fornecedor: %s", exc)
        return erro("Erro interno.", 500)

    logger.info("Fornecedor desativado: %s por %s", forn.nome, usuario_atual.email)
    return sucesso(message="Fornecedor desativado com sucesso.")


# ─── GET /api/fornecedores/categorias ────────────────────────────────────────

@bp_fornecedores.get("/categorias")
@login_obrigatorio
def categorias(usuario_atual):
    """Lista categorias disponíveis de fornecedores."""
    return sucesso(data={"categorias": list(CATEGORIAS_FORNECEDOR)})
