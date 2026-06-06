import logging
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.compra import Compra, CompraItem
from app.models.estoque import ItemEstoque, MovimentacaoEstoque
from app.schemas.compra_schema import CriarCompraSchema, FiltroCompraSchema
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import (
    sucesso, criado, erro, nao_encontrado, regra_negocio, paginado, validacao_erro
)
from app.services.audit_service import registrar_auditoria

bp_compras = Blueprint("compras", __name__)
logger = logging.getLogger(__name__)

_schema_criar  = CriarCompraSchema()
_schema_filtro = FiltroCompraSchema()


@bp_compras.get("")
@login_obrigatorio
def listar(usuario_atual):
    try:
        filtros = _schema_filtro.load(request.args.to_dict())
    except ValidationError as e:
        return validacao_erro(e.messages)

    pag = Compra.listar_por_tenant(
        tenant_id=usuario_atual.tenant_id,
        pagina=filtros["pagina"],
        por_pagina=filtros["por_pagina"],
        fornecedor_id=filtros.get("fornecedor_id"),
    )
    return paginado(pag.items, pag, lambda c: c.para_dict())


@bp_compras.post("")
@login_obrigatorio
def criar(usuario_atual):
    """
    Registra uma compra e atualiza automaticamente o estoque
    para cada item que tem item_estoque_id vinculado.
    """
    try:
        dados = _schema_criar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    tid = usuario_atual.tenant_id

    # Validar fornecedor se informado
    if dados.get("fornecedor_id"):
        from app.models.fornecedor import Fornecedor
        forn = Fornecedor.buscar_por_tenant_e_id(tid, dados["fornecedor_id"])
        if not forn:
            return nao_encontrado("Fornecedor")

    # Calcular valor total
    itens_dados = dados["itens"]
    valor_total = sum(
        float(i["quantidade"]) * float(i["valor_unitario"]) for i in itens_dados
    )

    try:
        # Criar compra
        compra = Compra(
            tenant_id=tid,
            fornecedor_id=dados.get("fornecedor_id"),
            criado_por_id=usuario_atual.id,
            data_compra=dados["data_compra"],
            numero_nota=dados.get("numero_nota"),
            valor_total=valor_total,
            forma_pagamento=dados.get("forma_pagamento"),
            status_pagamento=dados.get("status_pagamento", "pendente"),
            observacoes=dados.get("observacoes"),
        )
        db.session.add(compra)
        db.session.flush()  # garante compra.id

        # Criar itens e atualizar estoque
        for item_d in itens_dados:
            qtd          = float(item_d["quantidade"])
            vl_unit      = float(item_d["valor_unitario"])
            vl_total_item= round(qtd * vl_unit, 2)

            ci = CompraItem(
                compra_id=compra.id,
                item_estoque_id=item_d.get("item_estoque_id"),
                descricao=item_d["descricao"],
                unidade=item_d["unidade"],
                quantidade=qtd,
                valor_unitario=vl_unit,
                valor_total=vl_total_item,
            )
            db.session.add(ci)

            # Atualizar estoque se item vinculado
            if item_d.get("item_estoque_id"):
                item_est = ItemEstoque.query.filter_by(
                    id=item_d["item_estoque_id"], tenant_id=tid
                ).first()
                if item_est:
                    saldo_ant = float(item_est.quantidade_atual)
                    item_est.atualizar_custo_medio(qtd, vl_unit)
                    item_est.quantidade_atual = saldo_ant + qtd

                    mov = MovimentacaoEstoque(
                        tenant_id=tid,
                        item_id=item_est.id,
                        criado_por_id=usuario_atual.id,
                        tipo="entrada",
                        quantidade=qtd,
                        saldo_anterior=saldo_ant,
                        saldo_posterior=float(item_est.quantidade_atual),
                        custo_unitario=vl_unit,
                        origem="compra",
                        origem_id=compra.id,
                    )
                    db.session.add(mov)

        registrar_auditoria(
            tenant_id=tid, tabela="compras",
            operacao="INSERT", registro_id=compra.id,
            dados_depois=compra.para_dict(incluir_itens=False),
            usuario_id=usuario_atual.id,
        )
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar compra: %s", exc)
        return erro("Erro interno ao registrar compra.", 500)

    logger.info("Compra registrada: R$%s por %s", compra.valor_total, usuario_atual.email)
    return criado(data=compra.para_dict(), message="Compra registrada com sucesso.")


@bp_compras.get("/<string:compra_id>")
@login_obrigatorio
def obter(compra_id, usuario_atual):
    compra = Compra.query.filter_by(id=compra_id, tenant_id=usuario_atual.tenant_id).first()
    if not compra:
        return nao_encontrado("Compra")
    return sucesso(data=compra.para_dict())


@bp_compras.delete("/<string:compra_id>")
@proprietario_obrigatorio
def cancelar(compra_id, usuario_atual):
    """Cancela compra e estorna o estoque."""
    compra = Compra.query.filter_by(id=compra_id, tenant_id=usuario_atual.tenant_id).first()
    if not compra:
        return nao_encontrado("Compra")

    if compra.status_pagamento == "cancelado":
        return regra_negocio("Compra já está cancelada.")

    tid = usuario_atual.tenant_id
    try:
        # Estornar estoque de cada item vinculado
        for ci in compra.itens:
            if ci.item_estoque_id:
                item_est = ItemEstoque.query.filter_by(
                    id=ci.item_estoque_id, tenant_id=tid
                ).first()
                if item_est:
                    qtd       = float(ci.quantidade)
                    saldo_ant = float(item_est.quantidade_atual)
                    saldo_novo= max(0, saldo_ant - qtd)
                    item_est.quantidade_atual = saldo_novo

                    mov = MovimentacaoEstoque(
                        tenant_id=tid,
                        item_id=item_est.id,
                        criado_por_id=usuario_atual.id,
                        tipo="saida",
                        quantidade=qtd,
                        saldo_anterior=saldo_ant,
                        saldo_posterior=saldo_novo,
                        origem="compra",
                        origem_id=compra.id,
                        motivo=f"Estorno — cancelamento da compra {compra_id}",
                    )
                    db.session.add(mov)

        compra.status_pagamento = "cancelado"
        registrar_auditoria(
            tenant_id=tid, tabela="compras",
            operacao="DELETE", registro_id=compra.id,
            dados_antes=compra.para_dict(incluir_itens=False),
            usuario_id=usuario_atual.id,
        )
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao cancelar compra: %s", exc)
        return erro("Erro interno ao cancelar compra.", 500)

    return sucesso(message="Compra cancelada e estoque estornado.")


@bp_compras.get("/resumo/mes")
@login_obrigatorio
def resumo_mes(usuario_atual):
    """Total de compras do mês corrente."""
    from datetime import date
    hoje = date.today()
    total = Compra.total_no_mes(usuario_atual.tenant_id, hoje.year, hoje.month)
    return sucesso(data={"total_mes": total, "ano": hoje.year, "mes": hoje.month})
