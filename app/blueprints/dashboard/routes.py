import logging
from datetime import date, timedelta
from flask import Blueprint, request

from app.extensions import db
from app.models.conta_pagar import ContaPagar
from app.models.faturamento import Faturamento
from app.utils.auth import login_obrigatorio
from app.utils.respostas import sucesso

bp_dashboard = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)


@bp_dashboard.get("/resumo")
@login_obrigatorio
def resumo(usuario_atual):
    """KPIs do dia e do mês. [FIX B8] atualizar_vencidas sem commit próprio."""
    tid  = usuario_atual.tenant_id
    hoje = date.today()
    ano, mes = hoje.year, hoje.month

    # [FIX B8] Bulk update sem commit — commitamos explicitamente aqui
    ContaPagar.atualizar_vencidas(tid)
    db.session.commit()

    fat_dia      = Faturamento.total_do_dia(tid, hoje)
    fat_mes      = Faturamento.total_do_mes(tid, ano, mes)
    despesas_mes = ContaPagar.total_pago_no_mes(tid, ano, mes)
    total_pend   = ContaPagar.total_pendente(tid)
    lucro        = fat_mes - despesas_mes
    margem       = round((lucro / fat_mes * 100), 2) if fat_mes > 0 else 0.0

    contas_vencidas  = ContaPagar.query.filter_by(tenant_id=tid, status="vencida").count()
    proximas_vencer  = ContaPagar.query.filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "pendente",
        ContaPagar.vencimento > hoje,
        ContaPagar.vencimento <= hoje + timedelta(days=3),
    ).count()

    return sucesso(data={
        "faturamento_dia":      fat_dia,
        "faturamento_mes":      fat_mes,
        "despesas_mes":         despesas_mes,
        "lucro_estimado":       round(lucro, 2),
        "margem_percentual":    margem,
        "total_pendente":       total_pend,
        "contas_vencidas":      contas_vencidas,
        "proximas_vencer":      proximas_vencer,
        "data_referencia":      hoje.isoformat(),
        "mes_referencia":       f"{ano}-{mes:02d}",
    })


@bp_dashboard.get("/fluxo-caixa")
@login_obrigatorio
def fluxo_caixa(usuario_atual):
    """Entradas e saídas por dia para o gráfico."""
    tid  = usuario_atual.tenant_id
    dias = min(int(request.args.get("dias", 7)), 30)

    entradas = Faturamento.fluxo_ultimos_dias(tid, dias)

    from sqlalchemy import func
    hoje   = date.today()
    inicio = hoje - timedelta(days=dias - 1)

    saidas_raw = db.session.query(
        ContaPagar.data_pagamento,
        func.sum(ContaPagar.valor_pago).label("total")
    ).filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "paga",
        ContaPagar.data_pagamento >= inicio,
        ContaPagar.data_pagamento <= hoje,
    ).group_by(ContaPagar.data_pagamento).all()

    mapa_saidas = {str(r.data_pagamento): float(r.total) for r in saidas_raw}

    fluxo = []
    acumulado = 0.0
    for item in entradas:
        d      = item["data"]
        entrada= item["entradas"]
        saida  = mapa_saidas.get(d, 0.0)
        saldo  = round(entrada - saida, 2)
        acumulado += saldo
        fluxo.append({
            "data":           d,
            "entradas":       entrada,
            "saidas":         saida,
            "saldo_dia":      saldo,
            "saldo_acumulado":round(acumulado, 2),
        })

    return sucesso(data={"dias": dias, "fluxo": fluxo})


@bp_dashboard.get("/alertas")
@login_obrigatorio
def alertas(usuario_atual):
    """Contas vencidas e próximas a vencer."""
    tid  = usuario_atual.tenant_id
    hoje = date.today()

    # [FIX B8] Commit explícito após bulk update
    ContaPagar.atualizar_vencidas(tid)
    db.session.commit()

    vencidas = ContaPagar.query.filter_by(
        tenant_id=tid, status="vencida"
    ).order_by(ContaPagar.vencimento.asc()).limit(10).all()

    proximas = ContaPagar.query.filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "pendente",
        ContaPagar.vencimento > hoje,
        ContaPagar.vencimento <= hoje + timedelta(days=3),
    ).order_by(ContaPagar.vencimento.asc()).limit(10).all()

    # Estoque crítico
    from app.models.estoque import ItemEstoque
    itens_criticos = ItemEstoque.listar_por_tenant(tid, em_alerta=True)

    return sucesso(data={
        "contas_vencidas":  [c.para_dict() for c in vencidas],
        "proximas_vencer":  [c.para_dict() for c in proximas],
        "total_vencidas":   len(vencidas),
        "total_proximas":   len(proximas),
        "estoque_critico":  [i.para_dict() for i in itens_criticos[:5]],
        "total_estoque_critico": len(itens_criticos),
    })
