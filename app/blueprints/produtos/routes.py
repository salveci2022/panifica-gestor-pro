import logging
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.produto import Produto, CATEGORIAS_PRODUTO
from app.schemas.produto_schema import (
    CriarProdutoSchema,
    AtualizarProdutoSchema
)

from app.utils.auth import (
    login_obrigatorio,
    proprietario_obrigatorio
)

from app.utils.respostas import (
    sucesso,
    criado,
    erro,
    nao_encontrado,
    conflito,
    validacao_erro
)

from app.services.audit_service import registrar_auditoria

bp_produtos = Blueprint("produtos", __name__)
logger = logging.getLogger(__name__)

_schema_criar = CriarProdutoSchema()
_schema_atualizar = AtualizarProdutoSchema()


# LISTAR PRODUTOS

@bp_produtos.get("")
@login_obrigatorio
def listar(usuario_atual):

    tid = usuario_atual.tenant_id

    busca = request.args.get("busca")
    categoria = request.args.get("categoria")
    incluir_inativos = (
        request.args.get("inativos", "false").lower() == "true"
    )

    q = Produto.query.filter_by(
        tenant_id=tid
    )

    if not incluir_inativos:
        q = q.filter_by(ativo=True)

    if busca:
        q = q.filter(
            Produto.nome.ilike(f"%{busca}%")
        )

    if categoria:
        q = q.filter_by(
            categoria=categoria
        )

    produtos = q.order_by(
        Produto.nome.asc()
    ).all()

    return sucesso(
        data=[p.para_dict() for p in produtos]
    )


# CRIAR PRODUTO

@bp_produtos.post("")
@login_obrigatorio
def criar(usuario_atual):

    try:
        dados = _schema_criar.load(
            request.get_json() or {}
        )

    except ValidationError as e:
        return validacao_erro(e.messages)

    existente = Produto.query.filter_by(
        tenant_id=usuario_atual.tenant_id,
        nome=dados["nome"]
    ).first()

    if existente:
        return conflito(
            f"Já existe um produto chamado '{dados['nome']}'."
        )

    try:

        produto = Produto(
            tenant_id=usuario_atual.tenant_id,
            nome=dados["nome"],
            categoria=dados["categoria"],
            codigo_barras=dados.get("codigo_barras"),
            unidade=dados["unidade"],
            preco_custo=dados["preco_custo"],
            preco_venda=dados["preco_venda"],
            estoque_atual=dados.get("estoque_atual", 0),
            estoque_minimo=dados.get("estoque_minimo", 0),
            observacoes=dados.get("observacoes")
        )

        db.session.add(produto)
        db.session.flush()

        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id,
            tabela="produtos",
            operacao="INSERT",
            registro_id=produto.id,
            dados_depois=produto.para_dict(),
            usuario_id=usuario_atual.id
        )

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        logger.exception(
            "Erro ao criar produto: %s",
            exc
        )

        return erro(
            "Erro interno ao criar produto.",
            500
        )

    return criado(
        data=produto.para_dict(),
        message="Produto cadastrado com sucesso."
    )


# OBTER PRODUTO

@bp_produtos.get("/<string:produto_id>")
@login_obrigatorio
def obter(produto_id, usuario_atual):

    produto = Produto.buscar_por_tenant_e_id(
        usuario_atual.tenant_id,
        produto_id
    )

    if not produto:
        return nao_encontrado("Produto")

    return sucesso(
        data=produto.para_dict()
    )


# ATUALIZAR PRODUTO

@bp_produtos.put("/<string:produto_id>")
@login_obrigatorio
def atualizar(produto_id, usuario_atual):

    produto = Produto.buscar_por_tenant_e_id(
        usuario_atual.tenant_id,
        produto_id
    )

    if not produto:
        return nao_encontrado("Produto")

    try:

        dados = _schema_atualizar.load(
            request.get_json() or {}
        )

    except ValidationError as e:

        return validacao_erro(
            e.messages
        )

    antes = produto.para_dict()

    for campo, valor in dados.items():
        setattr(produto, campo, valor)

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id,
        tabela="produtos",
        operacao="UPDATE",
        registro_id=produto.id,
        dados_antes=antes,
        dados_depois=produto.para_dict(),
        usuario_id=usuario_atual.id
    )

    try:

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        logger.exception(
            "Erro ao atualizar produto: %s",
            exc
        )

        return erro(
            "Erro interno ao atualizar produto.",
            500
        )

    return sucesso(
        data=produto.para_dict(),
        message="Produto atualizado."
    )


# DESATIVAR PRODUTO

@bp_produtos.delete("/<string:produto_id>")
@proprietario_obrigatorio
def deletar(produto_id, usuario_atual):

    produto = Produto.buscar_por_tenant_e_id(
        usuario_atual.tenant_id,
        produto_id
    )

    if not produto:
        return nao_encontrado(
            "Produto"
        )

    antes = produto.para_dict()

    produto.desativar()

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id,
        tabela="produtos",
        operacao="DELETE",
        registro_id=produto.id,
        dados_antes=antes,
        dados_depois=produto.para_dict(),
        usuario_id=usuario_atual.id
    )

    try:

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        logger.exception(
            "Erro ao desativar produto: %s",
            exc
        )

        return erro(
            "Erro interno.",
            500
        )

    return sucesso(
        message="Produto desativado com sucesso."
    )


# CATEGORIAS

@bp_produtos.get("/categorias")
@login_obrigatorio
def categorias(usuario_atual):

    return sucesso(
        data={
            "categorias": list(
                CATEGORIAS_PRODUTO
            )
        }
    )