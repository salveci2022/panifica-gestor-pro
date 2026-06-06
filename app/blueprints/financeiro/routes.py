import logging
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.conta_pagar import ContaPagar, CATEGORIAS_VALIDAS, FORMAS_PAGAMENTO
from app.models.faturamento import Faturamento
from app.schemas.conta_schema import (
    CriarContaSchema, AtualizarContaSchema,
    PagarContaSchema, FiltroContaSchema,
)
from app.schemas.faturamento_schema import CriarFaturamentoSchema, FiltroFluxoSchema
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import (
    sucesso, criado, erro, nao_encontrado,
    regra_negocio, paginado, validacao_erro
)
from app.services.audit_service import registrar_auditoria

bp_financeiro = Blueprint("financeiro", __name__)
logger = logging.getLogger(__name__)

_schema_criar    = CriarContaSchema()
_schema_atualizar= AtualizarContaSchema()
_schema_pagar    = PagarContaSchema()
_schema_filtro   = FiltroContaSchema()
_schema_fat      = CriarFaturamentoSchema()
_schema_fluxo    = FiltroFluxoSchema()


# ═══════════════════════════════════════════════════════════════════════════════
#  [FIX B6] Rotas ESTÁTICAS registradas ANTES das dinâmicas para evitar conflito
# ═══════════════════════════════════════════════════════════════════════════════

@bp_financeiro.get("/categorias")
@login_obrigatorio
def listar_categorias(usuario_atual):
    return sucesso(data={
        "categorias": list(CATEGORIAS_VALIDAS),
        "formas_pagamento": list(FORMAS_PAGAMENTO),
    })


@bp_financeiro.get("/historico")
@login_obrigatorio
def historico(usuario_atual):
    tid = usuario_atual.tenant_id
    pagina    = int(request.args.get("pagina", 1))
    por_pagina= min(int(request.args.get("por_pagina", 20)), 100)

    pag = ContaPagar.query.filter_by(
        tenant_id=tid, status="paga"
    ).order_by(ContaPagar.data_pagamento.desc()).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )
    return paginado(pag.items, pag, lambda c: c.para_dict())


# ─── Faturamento (rotas estáticas antes de /<fat_id>) ────────────────────────

@bp_financeiro.get("/faturamento")
@login_obrigatorio
def listar_faturamentos(usuario_atual):
    tid = usuario_atual.tenant_id
    pagina    = int(request.args.get("pagina", 1))
    por_pagina= min(int(request.args.get("por_pagina", 20)), 100)
    pag = Faturamento.query.filter_by(tenant_id=tid).order_by(
        Faturamento.data.desc()
    ).paginate(page=pagina, per_page=por_pagina, error_out=False)
    return paginado(pag.items, pag, lambda f: f.para_dict())


@bp_financeiro.post("/faturamento")
@login_obrigatorio
def criar_faturamento(usuario_atual):
    try:
        dados = _schema_fat.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    try:
        fat = Faturamento(
            tenant_id=usuario_atual.tenant_id,
            criado_por_id=usuario_atual.id,
            data=dados["data"],
            valor=dados["valor"],
            descricao=dados.get("descricao"),
        )
        db.session.add(fat)
        db.session.flush()  # garante fat.id antes de registrar auditoria
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="faturamentos",
            operacao="INSERT", registro_id=fat.id,
            dados_depois=fat.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar faturamento: %s", exc)
        return erro("Erro interno ao registrar receita.", 500)

    logger.info("Faturamento: R$%s em %s por %s", fat.valor, fat.data, usuario_atual.email)
    return criado(data=fat.para_dict(), message="Receita registrada.")


@bp_financeiro.get("/faturamento/<string:fat_id>")
@login_obrigatorio
def obter_faturamento(fat_id, usuario_atual):
    fat = Faturamento.query.filter_by(
        id=fat_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not fat:
        return nao_encontrado("Faturamento")
    return sucesso(data=fat.para_dict())


@bp_financeiro.put("/faturamento/<string:fat_id>")
@login_obrigatorio
def atualizar_faturamento(fat_id, usuario_atual):
    fat = Faturamento.query.filter_by(
        id=fat_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not fat:
        return nao_encontrado("Faturamento")

    try:
        dados = _schema_fat.load(request.get_json() or {}, partial=True)
    except ValidationError as e:
        return validacao_erro(e.messages)

    antes = fat.para_dict()
    for campo, valor in dados.items():
        setattr(fat, campo, valor)

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="faturamentos",
        operacao="UPDATE", registro_id=fat.id,
        dados_antes=antes, dados_depois=fat.para_dict(), usuario_id=usuario_atual.id,
    )
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao atualizar faturamento: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(data=fat.para_dict(), message="Receita atualizada.")


@bp_financeiro.delete("/faturamento/<string:fat_id>")
@proprietario_obrigatorio
def deletar_faturamento(fat_id, usuario_atual):
    fat = Faturamento.query.filter_by(
        id=fat_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not fat:
        return nao_encontrado("Faturamento")

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="faturamentos",
        operacao="DELETE", registro_id=fat.id,
        dados_antes=fat.para_dict(), usuario_id=usuario_atual.id,
    )
    try:
        db.session.delete(fat)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao deletar faturamento: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(message="Receita removida.")


@bp_financeiro.get("/fluxo-caixa/relatorio")
@login_obrigatorio
def relatorio_fluxo(usuario_atual):
    tid = usuario_atual.tenant_id
    from datetime import date as _date
    hoje = _date.today()

    try:
        params = _schema_fluxo.load(request.args.to_dict())
    except ValidationError as e:
        return validacao_erro(e.messages)

    ano = params.get("ano") or hoje.year
    mes = params.get("mes") or hoje.month

    fat_mes      = Faturamento.total_do_mes(tid, ano, mes)
    despesas_mes = ContaPagar.total_pago_no_mes(tid, ano, mes)
    lucro        = fat_mes - despesas_mes
    margem       = round((lucro / fat_mes * 100), 2) if fat_mes > 0 else 0.0

    from sqlalchemy import func, extract
    saidas_cat = db.session.query(
        ContaPagar.categoria,
        func.sum(ContaPagar.valor_pago).label("total")
    ).filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "paga",
        extract("year",  ContaPagar.data_pagamento) == ano,
        extract("month", ContaPagar.data_pagamento) == mes,
    ).group_by(ContaPagar.categoria).all()

    return sucesso(data={
        "periodo":           {"ano": ano, "mes": mes},
        "faturamento_total": fat_mes,
        "despesas_total":    despesas_mes,
        "lucro_estimado":    round(lucro, 2),
        "margem_percentual": margem,
        "saidas_por_categoria": [
            {"categoria": r.categoria, "total": float(r.total)}
            for r in saidas_cat
        ],
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTAS A PAGAR — rotas dinâmicas registradas depois das estáticas
# ═══════════════════════════════════════════════════════════════════════════════

@bp_financeiro.get("")
@login_obrigatorio
def listar_contas(usuario_atual):
    tid = usuario_atual.tenant_id
    # [FIX B2] atualizar_vencidas não faz mais commit próprio
    ContaPagar.atualizar_vencidas(tid)

    try:
        filtros = _schema_filtro.load(request.args.to_dict())
    except ValidationError as e:
        return validacao_erro(e.messages)

    q = ContaPagar.query.filter_by(tenant_id=tid)
    if filtros.get("status"):
        q = q.filter_by(status=filtros["status"])
    if filtros.get("fornecedor_id"):
        q = q.filter_by(fornecedor_id=filtros["fornecedor_id"])
    if filtros.get("categoria"):
        q = q.filter_by(categoria=filtros["categoria"])
    if filtros.get("loja_id"):
        q = q.filter_by(loja_id=filtros["loja_id"])

    q   = q.order_by(ContaPagar.vencimento.asc())
    pag = q.paginate(page=filtros["pagina"], per_page=filtros["por_pagina"], error_out=False)
    # Comita o bulk update de vencidas
    db.session.commit()
    return paginado(pag.items, pag, lambda c: c.para_dict())


@bp_financeiro.post("")
@login_obrigatorio
def criar_conta(usuario_atual):
    try:
        dados = _schema_criar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    if dados.get("fornecedor_id"):
        from app.models.fornecedor import Fornecedor
        forn = Fornecedor.buscar_por_tenant_e_id(usuario_atual.tenant_id, dados["fornecedor_id"])
        if not forn:
            return nao_encontrado("Fornecedor")

    try:
        conta = ContaPagar(
            tenant_id=usuario_atual.tenant_id,
            criado_por_id=usuario_atual.id,
            descricao=dados["descricao"],
            categoria=dados["categoria"],
            valor=dados["valor"],
            vencimento=dados["vencimento"],
            forma_pagamento=dados.get("forma_pagamento"),
            fornecedor_id=dados.get("fornecedor_id"),
            observacoes=dados.get("observacoes"),
            loja_id=dados.get("loja_id"),
            numero_pedido=dados.get("numero_pedido"),
        )
        conta.atualizar_status_vencimento()
        db.session.add(conta)
        db.session.flush()  # garante conta.id antes de registrar auditoria
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="contas_pagar",
            operacao="INSERT", registro_id=conta.id,
            dados_depois=conta.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar conta: %s", exc)
        return erro("Erro interno ao criar conta.", 500)

    logger.info("Conta criada: %s R$%s", conta.descricao, conta.valor)
    return criado(data=conta.para_dict(), message="Conta registrada.")


@bp_financeiro.get("/<string:conta_id>")
@login_obrigatorio
def obter_conta(conta_id, usuario_atual):
    conta = ContaPagar.query.filter_by(
        id=conta_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not conta:
        return nao_encontrado("Conta")
    conta.atualizar_status_vencimento()
    return sucesso(data=conta.para_dict())


@bp_financeiro.put("/<string:conta_id>")
@login_obrigatorio
def atualizar_conta(conta_id, usuario_atual):
    conta = ContaPagar.query.filter_by(
        id=conta_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not conta:
        return nao_encontrado("Conta")
    if conta.status == "cancelada":
        return regra_negocio("Não é possível editar uma conta cancelada.")

    try:
        dados = _schema_atualizar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    if conta.status == "paga":
        bloqueados = set(dados.keys()) - {"observacoes"}
        if bloqueados:
            return regra_negocio(
                f"Conta já paga. Somente 'observacoes' pode ser alterado. "
                f"Campos bloqueados: {', '.join(bloqueados)}"
            )

    if "fornecedor_id" in dados and dados["fornecedor_id"]:
        from app.models.fornecedor import Fornecedor
        if not Fornecedor.buscar_por_tenant_e_id(usuario_atual.tenant_id, dados["fornecedor_id"]):
            return nao_encontrado("Fornecedor")

    antes = conta.para_dict()
    for campo, valor in dados.items():
        setattr(conta, campo, valor)
    conta.atualizar_status_vencimento()

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="contas_pagar",
        operacao="UPDATE", registro_id=conta.id,
        dados_antes=antes, dados_depois=conta.para_dict(), usuario_id=usuario_atual.id,
    )
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao atualizar conta: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(data=conta.para_dict(), message="Conta atualizada.")


@bp_financeiro.patch("/<string:conta_id>/pagar")
@login_obrigatorio
def marcar_paga(conta_id, usuario_atual):
    conta = ContaPagar.query.filter_by(
        id=conta_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not conta:
        return nao_encontrado("Conta")

    try:
        dados = _schema_pagar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    antes = conta.para_dict()
    try:
        conta.marcar_como_paga(
            valor_pago=dados.get("valor_pago"),
            data_pgto=dados.get("data_pagamento"),
        )
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="contas_pagar",
            operacao="UPDATE", registro_id=conta.id,
            dados_antes=antes, dados_depois=conta.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except ValueError as e:
        return regra_negocio(str(e))
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao pagar conta: %s", exc)
        return erro("Erro interno.", 500)

    logger.info("Conta paga: %s R$%s", conta.descricao, conta.valor_pago)
    return sucesso(data=conta.para_dict(), message="Conta marcada como paga.")


@bp_financeiro.patch("/<string:conta_id>/cancelar")
@proprietario_obrigatorio
def cancelar_conta(conta_id, usuario_atual):
    conta = ContaPagar.query.filter_by(
        id=conta_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not conta:
        return nao_encontrado("Conta")

    antes = conta.para_dict()
    try:
        conta.cancelar()
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="contas_pagar",
            operacao="UPDATE", registro_id=conta.id,
            dados_antes=antes, dados_depois=conta.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except ValueError as e:
        return regra_negocio(str(e))
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao cancelar conta: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(data=conta.para_dict(), message="Conta cancelada.")


@bp_financeiro.delete("/<string:conta_id>")
@proprietario_obrigatorio
def deletar_conta(conta_id, usuario_atual):
    conta = ContaPagar.query.filter_by(
        id=conta_id, tenant_id=usuario_atual.tenant_id
    ).first()
    if not conta:
        return nao_encontrado("Conta")
    if conta.status == "paga":
        return regra_negocio("Não é possível excluir uma conta paga. Use cancelar.")

    antes = conta.para_dict()
    try:
        conta.cancelar()
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="contas_pagar",
            operacao="DELETE", registro_id=conta.id,
            dados_antes=antes, usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except ValueError as e:
        return regra_negocio(str(e))
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao deletar conta: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(message="Conta removida.")
