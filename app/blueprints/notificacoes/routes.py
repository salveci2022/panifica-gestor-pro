"""
Módulo de notificações via WhatsApp usando Z-API.
Configuração no .env:
  ZAPI_INSTANCE_ID=sua-instancia
  ZAPI_TOKEN=seu-token
  ZAPI_CLIENT_TOKEN=seu-client-token
  WHATSAPP_NUMERO_PADARIA=5561999001234  (com DDI+DDD, sem + e sem espaço)
"""
import logging
import os
import requests
from flask import Blueprint, request

from app.models.conta_pagar import ContaPagar
from app.models.estoque import ItemEstoque
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import sucesso, erro

bp_notificacoes = Blueprint("notificacoes", __name__)
logger = logging.getLogger(__name__)


def _zapi_url(endpoint: str) -> str:
    instance = os.environ.get("ZAPI_INSTANCE_ID", "")
    token    = os.environ.get("ZAPI_TOKEN", "")
    return f"https://api.z-api.io/instances/{instance}/token/{token}/{endpoint}"


def _zapi_headers() -> dict:
    client_token = os.environ.get("ZAPI_CLIENT_TOKEN", "")
    return {
        "Content-Type": "application/json",
        "client-token": client_token,
    }


def _enviar_mensagem(numero: str, mensagem: str) -> dict:
    """Envia mensagem de texto via Z-API."""
    if not os.environ.get("ZAPI_INSTANCE_ID"):
        return {"ok": False, "erro": "Z-API não configurada. Defina ZAPI_INSTANCE_ID no .env"}

    try:
        resp = requests.post(
            _zapi_url("send-text"),
            json={"phone": numero, "message": mensagem},
            headers=_zapi_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return {"ok": True, "resposta": resp.json()}
        return {"ok": False, "erro": f"Z-API retornou {resp.status_code}: {resp.text}"}
    except Exception as exc:
        logger.exception("Erro ao enviar WhatsApp: %s", exc)
        return {"ok": False, "erro": str(exc)}


def _formatar_brl(valor) -> str:
    v = float(valor or 0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ─── GET /api/notificacoes/status ────────────────────────────────────────────

@bp_notificacoes.get("/status")
@login_obrigatorio
def status_zapi(usuario_atual):
    """Verifica se Z-API está configurada e conectada."""
    if not os.environ.get("ZAPI_INSTANCE_ID"):
        return sucesso(data={
            "configurada": False,
            "mensagem": "ZAPI_INSTANCE_ID não definida no .env"
        })

    try:
        resp = requests.get(_zapi_url("status"), headers=_zapi_headers(), timeout=8)
        dados = resp.json()
        return sucesso(data={
            "configurada": True,
            "conectada":   dados.get("connected", False),
            "status":      dados,
        })
    except Exception as exc:
        return sucesso(data={"configurada": True, "conectada": False, "erro": str(exc)})


# ─── POST /api/notificacoes/alerta-vencimentos ────────────────────────────────

@bp_notificacoes.post("/alerta-vencimentos")
@login_obrigatorio
def alerta_vencimentos(usuario_atual):
    """Envia WhatsApp com contas vencidas e próximas a vencer."""
    from datetime import date, timedelta
    tid  = usuario_atual.tenant_id
    hoje = date.today()

    # Atualizar vencidas
    ContaPagar.atualizar_vencidas(tid)

    vencidas = ContaPagar.query.filter_by(
        tenant_id=tid, status="vencida"
    ).order_by(ContaPagar.vencimento.asc()).limit(5).all()

    proximas = ContaPagar.query.filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "pendente",
        ContaPagar.vencimento > hoje,
        ContaPagar.vencimento <= hoje + timedelta(days=3),
    ).order_by(ContaPagar.vencimento.asc()).limit(5).all()

    if not vencidas and not proximas:
        return sucesso(message="Nenhum alerta para enviar.")

    tenant_nome = usuario_atual.tenant.nome if usuario_atual.tenant else "Padaria"
    numero = request.json.get("numero") or os.environ.get("WHATSAPP_NUMERO_PADARIA", "")

    if not numero:
        return erro("Número de WhatsApp não informado. Passe no body ou defina WHATSAPP_NUMERO_PADARIA no .env", 400)

    linhas = [f"⚠️ *{tenant_nome} — Alertas Financeiros*", f"📅 {hoje.strftime('%d/%m/%Y')}", ""]

    if vencidas:
        linhas.append("🔴 *CONTAS VENCIDAS:*")
        for c in vencidas:
            linhas.append(f"  • {c.descricao} — {_formatar_brl(c.valor)} (venceu {c.vencimento.strftime('%d/%m')})")
        linhas.append("")

    if proximas:
        linhas.append("🟡 *VENCENDO EM 3 DIAS:*")
        for c in proximas:
            linhas.append(f"  • {c.descricao} — {_formatar_brl(c.valor)} (vence {c.vencimento.strftime('%d/%m')})")
        linhas.append("")

    total_vencido = sum(float(c.valor) for c in vencidas)
    linhas.append(f"💰 Total vencido: *{_formatar_brl(total_vencido)}*")
    linhas.append("")
    linhas.append("_Enviado pelo PANIFICA GESTOR PRO_")

    mensagem = "\n".join(linhas)
    resultado = _enviar_mensagem(numero, mensagem)

    return sucesso(
        data={"enviado": resultado["ok"], "numero": numero, "detalhe": resultado},
        message="Alerta enviado." if resultado["ok"] else "Falha ao enviar."
    )


# ─── POST /api/notificacoes/alerta-estoque ───────────────────────────────────

@bp_notificacoes.post("/alerta-estoque")
@login_obrigatorio
def alerta_estoque(usuario_atual):
    """Envia WhatsApp com itens de estoque em nível crítico."""
    tid    = usuario_atual.tenant_id
    itens  = ItemEstoque.listar_por_tenant(tid, em_alerta=True)
    numero = request.json.get("numero") or os.environ.get("WHATSAPP_NUMERO_PADARIA", "")

    if not itens:
        return sucesso(message="Estoque em níveis normais. Nenhum alerta necessário.")

    if not numero:
        return erro("Número não informado.", 400)

    tenant_nome = usuario_atual.tenant.nome if usuario_atual.tenant else "Padaria"
    from datetime import date
    linhas = [
        f"📦 *{tenant_nome} — Estoque Crítico*",
        f"📅 {date.today().strftime('%d/%m/%Y')}",
        f"",
        f"🔴 *{len(itens)} item(ns) abaixo do mínimo:*",
        "",
    ]
    for item in itens:
        linhas.append(
            f"  • {item.nome}: {float(item.quantidade_atual)}{item.unidade} "
            f"(mínimo: {float(item.quantidade_minima)}{item.unidade})"
        )

    linhas += ["", "_Enviado pelo PANIFICA GESTOR PRO_"]
    mensagem = "\n".join(linhas)
    resultado = _enviar_mensagem(numero, mensagem)

    return sucesso(
        data={"enviado": resultado["ok"], "itens_alertados": len(itens)},
        message="Alerta de estoque enviado." if resultado["ok"] else "Falha ao enviar."
    )


# ─── POST /api/notificacoes/resumo-diario ─────────────────────────────────────

@bp_notificacoes.post("/resumo-diario")
@login_obrigatorio
def resumo_diario(usuario_atual):
    """Envia resumo financeiro do dia via WhatsApp."""
    from datetime import date
    from app.models.faturamento import Faturamento
    from app.extensions import db

    tid    = usuario_atual.tenant_id
    hoje   = date.today()
    numero = request.json.get("numero") or os.environ.get("WHATSAPP_NUMERO_PADARIA", "")

    if not numero:
        return erro("Número não informado.", 400)

    fat_dia = Faturamento.total_do_dia(tid, hoje)
    fat_mes = Faturamento.total_do_mes(tid, hoje.year, hoje.month)

    ContaPagar.atualizar_vencidas(tid)
    db.session.commit()
    total_pend = ContaPagar.total_pendente(tid)
    qtd_venc   = ContaPagar.query.filter_by(tenant_id=tid, status="vencida").count()

    tenant_nome = usuario_atual.tenant.nome if usuario_atual.tenant else "Padaria"
    linhas = [
        f"📊 *{tenant_nome} — Resumo do Dia*",
        f"📅 {hoje.strftime('%d/%m/%Y')}",
        "",
        f"💵 Faturamento hoje: *{_formatar_brl(fat_dia)}*",
        f"📈 Faturamento no mês: *{_formatar_brl(fat_mes)}*",
        f"💳 Contas a pagar: *{_formatar_brl(total_pend)}*",
    ]
    if qtd_venc > 0:
        linhas.append(f"🔴 Contas vencidas: *{qtd_venc}*")

    linhas += ["", "_Enviado pelo PANIFICA GESTOR PRO_"]
    mensagem = "\n".join(linhas)
    resultado = _enviar_mensagem(numero, mensagem)

    return sucesso(
        data={"enviado": resultado["ok"]},
        message="Resumo enviado." if resultado["ok"] else "Falha ao enviar."
    )
