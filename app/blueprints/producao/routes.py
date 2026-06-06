import logging
from datetime import date
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.producao import ProducaoDiaria, CATEGORIAS_PRODUCAO, UNIDADES_PRODUCAO
from app.schemas.producao_schema import CriarProducaoSchema, FiltroProducaoSchema
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import (
    sucesso, criado, erro, nao_encontrado, regra_negocio, paginado, validacao_erro
)
from app.services.audit_service import registrar_auditoria

bp_producao = Blueprint("producao", __name__)
logger = logging.getLogger(__name__)

_schema_criar  = CriarProducaoSchema()
_schema_filtro = FiltroProducaoSchema()


@bp_producao.get("/categorias")
@login_obrigatorio
def listar_categorias(usuario_atual):
    return sucesso(data={
        "categorias": list(CATEGORIAS_PRODUCAO),
        "unidades":   list(UNIDADES_PRODUCAO),
    })


@bp_producao.get("/hoje")
@login_obrigatorio
def producao_hoje(usuario_atual):
    """Retorna todos os registros de produção do dia atual."""
    itens = ProducaoDiaria.listar_por_data(usuario_atual.tenant_id, date.today())
    return sucesso(data={
        "data":  date.today().isoformat(),
        "itens": [i.para_dict() for i in itens],
        "total": len(itens),
    })


@bp_producao.get("")
@login_obrigatorio
def listar(usuario_atual):
    try:
        filtros = _schema_filtro.load(request.args.to_dict())
    except ValidationError as e:
        return validacao_erro(e.messages)

    tid = usuario_atual.tenant_id
    q   = ProducaoDiaria.query.filter_by(tenant_id=tid)

    if filtros.get("data"):
        q = q.filter_by(data_producao=filtros["data"])
    elif filtros.get("data_inicio") and filtros.get("data_fim"):
        q = q.filter(
            ProducaoDiaria.data_producao >= filtros["data_inicio"],
            ProducaoDiaria.data_producao <= filtros["data_fim"],
        )
    if filtros.get("categoria"):
        q = q.filter_by(categoria=filtros["categoria"])

    q   = q.order_by(ProducaoDiaria.data_producao.desc(), ProducaoDiaria.produto.asc())
    pag = q.paginate(page=filtros["pagina"], per_page=filtros["por_pagina"], error_out=False)
    return paginado(pag.items, pag, lambda p: p.para_dict())


@bp_producao.post("")
@login_obrigatorio
def criar(usuario_atual):
    try:
        dados = _schema_criar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    try:
        prod = ProducaoDiaria(
            tenant_id=usuario_atual.tenant_id,
            criado_por_id=usuario_atual.id,
            data_producao=dados["data_producao"],
            produto=dados["produto"],
            categoria=dados["categoria"],
            quantidade=dados["quantidade"],
            unidade=dados["unidade"],
            custo_estimado=dados.get("custo_estimado"),
            observacoes=dados.get("observacoes"),
        )
        db.session.add(prod)
        db.session.flush()
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="producao_diaria",
            operacao="INSERT", registro_id=prod.id,
            dados_depois=prod.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar produção: %s", exc)
        return erro("Erro interno ao registrar produção.", 500)

    logger.info("Produção: %s %s%s por %s", prod.produto, prod.quantidade, prod.unidade, usuario_atual.email)
    return criado(data=prod.para_dict(), message="Produção registrada.")


@bp_producao.get("/<string:prod_id>")
@login_obrigatorio
def obter(prod_id, usuario_atual):
    prod = ProducaoDiaria.query.filter_by(id=prod_id, tenant_id=usuario_atual.tenant_id).first()
    if not prod:
        return nao_encontrado("Registro de produção")
    return sucesso(data=prod.para_dict())


@bp_producao.delete("/<string:prod_id>")
@proprietario_obrigatorio
def deletar(prod_id, usuario_atual):
    prod = ProducaoDiaria.query.filter_by(id=prod_id, tenant_id=usuario_atual.tenant_id).first()
    if not prod:
        return nao_encontrado("Registro de produção")

    hoje = date.today()
    if prod.data_producao < hoje:
        return regra_negocio("Só é possível excluir registros do dia atual.")

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="producao_diaria",
        operacao="DELETE", registro_id=prod.id,
        dados_antes=prod.para_dict(), usuario_id=usuario_atual.id,
    )
    try:
        db.session.delete(prod)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return erro("Erro interno.", 500)

    return sucesso(message="Registro removido.")


@bp_producao.get("/resumo/periodo")
@login_obrigatorio
def resumo_periodo(usuario_atual):
    """Resumo de produção agrupado por produto em um período."""
    from datetime import timedelta
    hoje       = date.today()
    data_inicio= date.fromisoformat(request.args.get("data_inicio", str(hoje - timedelta(days=6))))
    data_fim   = date.fromisoformat(request.args.get("data_fim",   str(hoje)))

    resultados = ProducaoDiaria.resumo_periodo(usuario_atual.tenant_id, data_inicio, data_fim)
    return sucesso(data={
        "data_inicio": data_inicio.isoformat(),
        "data_fim":    data_fim.isoformat(),
        "resumo": [
            {
                "produto":            r.produto,
                "categoria":          r.categoria,
                "unidade":            r.unidade,
                "total_quantidade":   float(r.total_quantidade),
                "total_custo":        float(r.total_custo or 0),
            }
            for r in resultados
        ],
    })
