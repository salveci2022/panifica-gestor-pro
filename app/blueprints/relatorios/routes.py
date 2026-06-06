"""
Relatórios PDF com gráficos — ReportLab (sem dependências de sistema).
"""
import logging
import io
from datetime import date
from flask import Blueprint, request, make_response

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

from app.extensions import db
from app.models.conta_pagar import ContaPagar
from app.models.faturamento import Faturamento
from app.utils.auth import login_obrigatorio
from app.utils.respostas import sucesso, erro

bp_relatorios = Blueprint("relatorios", __name__)
logger = logging.getLogger(__name__)

NAVY    = colors.HexColor("#0D1B2E")
AZUL    = colors.HexColor("#1D4ED8")
AZUL_CL = colors.HexColor("#EFF6FF")
VERDE   = colors.HexColor("#166534")
VERDE_CL= colors.HexColor("#F0FDF4")
VERM    = colors.HexColor("#991B1B")
VERM_CL = colors.HexColor("#FEF2F2")
CINZA1  = colors.HexColor("#1E293B")
CINZA2  = colors.HexColor("#64748B")
CINZA3  = colors.HexColor("#F1F5F9")
CINZA4  = colors.HexColor("#E2E8F0")
BRANCO  = colors.white
AMB     = colors.HexColor("#F59E0B")


def _brl(valor):
    v = float(valor or 0)
    s = f"{abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    return f"{'R$ ' if v >= 0 else 'R$ -'}{s}"


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo":    ParagraphStyle("t1",  parent=base["Normal"], fontSize=18,
                                    textColor=BRANCO, fontName="Helvetica-Bold",
                                    alignment=TA_CENTER, leading=24),
        "subtitulo": ParagraphStyle("t2",  parent=base["Normal"], fontSize=10,
                                    textColor=colors.HexColor("#93C5FD"),
                                    fontName="Helvetica", alignment=TA_CENTER, leading=14),
        "secao":     ParagraphStyle("s1",  parent=base["Normal"], fontSize=12,
                                    textColor=CINZA1, fontName="Helvetica-Bold", leading=16),
        "corpo":     ParagraphStyle("c1",  parent=base["Normal"], fontSize=10,
                                    textColor=CINZA1, fontName="Helvetica", leading=14),
        "label":     ParagraphStyle("l1",  parent=base["Normal"], fontSize=8,
                                    textColor=CINZA2, fontName="Helvetica", leading=12),
        "rodape":    ParagraphStyle("r1",  parent=base["Normal"], fontSize=8,
                                    textColor=CINZA2, fontName="Helvetica",
                                    alignment=TA_CENTER, leading=12),
        "kpi_label": ParagraphStyle("kl",  parent=base["Normal"], fontSize=9,
                                    textColor=CINZA2, fontName="Helvetica", leading=12),
        "kpi_valor": ParagraphStyle("kv",  parent=base["Normal"], fontSize=16,
                                    textColor=CINZA1, fontName="Helvetica-Bold", leading=20),
    }


def _grafico_barras_duplas(largura, altura, dados, cor_ent=AZUL, cor_sai=VERM):
    """
    Gera gráfico de barras duplas (entradas x saídas) como Drawing ReportLab.
    dados: lista de dict {label, entrada, saida}
    """
    d = Drawing(largura, altura)
    if not dados:
        return d

    margem_l, margem_r = 50, 10
    margem_t, margem_b = 10, 30
    area_w = largura - margem_l - margem_r
    area_h = altura - margem_t - margem_b

    max_val = max(
        max((float(i.get("entrada",0)) for i in dados), default=1),
        max((float(i.get("saida",0))   for i in dados), default=1),
    ) or 1

    n      = len(dados)
    grupo_w= area_w / n
    barra_w= max(4, grupo_w * 0.35)
    gap    = barra_w * 0.2

    # Linha de base
    d.add(Line(margem_l, margem_b, margem_l + area_w, margem_b,
               strokeColor=CINZA4, strokeWidth=0.5))
    # Eixo Y
    d.add(Line(margem_l, margem_b, margem_l, margem_b + area_h,
               strokeColor=CINZA4, strokeWidth=0.5))

    # Linhas horizontais de referência
    for frac in [0.25, 0.5, 0.75, 1.0]:
        y = margem_b + area_h * frac
        d.add(Line(margem_l, y, margem_l + area_w, y,
                   strokeColor=CINZA4, strokeWidth=0.3, strokeDashArray=[2,3]))
        val = max_val * frac
        label = f"R${val/1000:.0f}k" if val >= 1000 else f"R${val:.0f}"
        d.add(String(margem_l - 3, y - 3, label,
                     fontSize=6, fillColor=CINZA2, textAnchor="end"))

    # Barras
    for i, item in enumerate(dados):
        cx = margem_l + i * grupo_w + grupo_w / 2

        ent = float(item.get("entrada", 0))
        sai = float(item.get("saida",   0))

        # Barra entrada
        h_ent = area_h * (ent / max_val) if max_val > 0 else 0
        x_ent = cx - gap - barra_w
        if h_ent > 0:
            d.add(Rect(x_ent, margem_b, barra_w, h_ent,
                       fillColor=cor_ent, strokeColor=None))

        # Barra saída
        h_sai = area_h * (sai / max_val) if max_val > 0 else 0
        x_sai = cx + gap
        if h_sai > 0:
            d.add(Rect(x_sai, margem_b, barra_w, h_sai,
                       fillColor=cor_sai, strokeColor=None))

        # Label do eixo X
        label = str(item.get("label",""))[:5]
        d.add(String(cx, margem_b - 14, label,
                     fontSize=7, fillColor=CINZA2, textAnchor="middle"))

    return d


def _grafico_pizza_simples(largura, altura, dados):
    """
    Gráfico de barras horizontais para categorias de despesa.
    dados: lista de dict {categoria, total, pct}
    """
    d = Drawing(largura, altura)
    if not dados:
        return d

    cores_cat = [AZUL, VERM, AMB, VERDE, colors.HexColor("#7C3AED"),
                 colors.HexColor("#0891B2"), colors.HexColor("#DB2777")]

    margem_l = 100
    barra_h  = 14
    gap      = 8
    area_w   = largura - margem_l - 60
    max_pct  = max((d.get("pct",0) for d in dados), default=1) or 1

    for idx, item in enumerate(dados[:8]):
        y = altura - 20 - idx * (barra_h + gap)
        pct  = float(item.get("pct", 0))
        bw   = area_w * (pct / 100)
        cor  = cores_cat[idx % len(cores_cat)]
        cat  = str(item.get("categoria","")).replace("_"," ").title()[:18]

        # Label categoria
        d.add(String(margem_l - 5, y + 3, cat,
                     fontSize=8, fillColor=CINZA1, textAnchor="end"))
        # Barra
        if bw > 0:
            d.add(Rect(margem_l, y, bw, barra_h, fillColor=cor, strokeColor=None))
        # Valor
        val_str = _brl(item.get("total", 0))
        d.add(String(margem_l + bw + 4, y + 3, f"{pct:.1f}%  {val_str}",
                     fontSize=7, fillColor=CINZA2))

    return d


def _gerar_pdf_relatorio(tenant_nome, periodo, dados, fluxo_semanal=None):
    buf = io.BytesIO()
    W, H = A4
    M    = 15 * mm
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              leftMargin=M, rightMargin=M,
                              topMargin=14*mm, bottomMargin=14*mm)
    s  = _estilos()
    st = []

    MESES = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    mes_nome = MESES[periodo["mes"]] if 1 <= periodo["mes"] <= 12 else str(periodo["mes"])

    fat_total  = dados.get("faturamento_total",  0)
    desp_total = dados.get("despesas_total",      0)
    lucro      = dados.get("lucro_estimado",      0)
    margem     = dados.get("margem_percentual",   0)
    saidas_cat = dados.get("saidas_por_categoria",[])
    contas_pgs = dados.get("contas_pagas",        [])
    cor_lucro  = VERDE if float(lucro) >= 0 else VERM

    # ── Cabeçalho ──
    cab = Table(
        [[Paragraph("PANIFICA GESTOR PRO", s["titulo"]),
          Paragraph(f"Relatório Financeiro — {mes_nome} de {periodo['ano']}", s["subtitulo"]),
          Paragraph(f"{tenant_nome}  ·  Gerado em {date.today().strftime('%d/%m/%Y')}", s["label"])]],
        colWidths=[W - 2*M]
    )
    cab.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 16),
        ("ROUNDEDCORNERS",(0,0),(-1,-1), 6),
    ]))
    st.append(cab)
    st.append(Spacer(1, 14))

    # ── KPIs ──
    def kpi_cell(lbl, val, cor=CINZA1):
        return [
            Paragraph(lbl, s["kpi_label"]),
            Paragraph(val, ParagraphStyle("kv2", parent=s["kpi_valor"], textColor=cor)),
        ]

    kpi_t = Table(
        [[kpi_cell("Faturamento total", _brl(fat_total), VERDE),
          kpi_cell("Total de despesas", _brl(desp_total), VERM),
          kpi_cell("Lucro estimado",    _brl(lucro),      cor_lucro),
          kpi_cell("Margem líquida",    f"{float(margem):.1f}%", cor_lucro)]],
        colWidths=[(W - 2*M) / 4] * 4
    )
    kpi_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CINZA3),
        ("INNERGRID",     (0,0),(-1,-1), 1, CINZA4),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    st.append(kpi_t)
    st.append(Spacer(1, 16))

    # ── GRÁFICO: Entradas x Saídas (fluxo semanal) ──
    if fluxo_semanal and len(fluxo_semanal) > 0:
        st.append(Paragraph("Entradas × Saídas — Últimos 14 dias", s["secao"]))
        st.append(Spacer(1, 6))

        # Legenda
        leg = Table(
            [[Rect(0, 2, 10, 10, fillColor=AZUL, strokeColor=None),
              Paragraph("Entradas", s["label"]),
              Rect(0, 2, 10, 10, fillColor=VERM, strokeColor=None),
              Paragraph("Saídas",   s["label"])]],
            colWidths=[12, 55, 12, 55]
        )
        leg.setStyle(TableStyle([
            ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0),(-1,-1), 0),
        ]))
        st.append(leg)
        st.append(Spacer(1, 4))

        dados_graf = [
            {
                "label":   d["data"][-5:],
                "entrada": float(d.get("entradas", 0)),
                "saida":   float(d.get("saidas",   0)),
            }
            for d in fluxo_semanal
        ]
        graf_barras = _grafico_barras_duplas(W - 2*M, 120, dados_graf)
        st.append(graf_barras)
        st.append(Spacer(1, 16))

    # ── GRÁFICO: Despesas por categoria ──
    if saidas_cat:
        desp_t = float(desp_total) or 1
        dados_cat = sorted([
            {
                "categoria": r["categoria"],
                "total":     r["total"],
                "pct":       round(r["total"] / desp_t * 100, 1),
            }
            for r in saidas_cat
        ], key=lambda x: -x["pct"])

        col_w = (W - 2*M) / 2 - 5*mm

        # Tabela de categorias
        cat_rows = [
            [Paragraph(h, ParagraphStyle("th", parent=s["label"],
                        textColor=colors.HexColor("#93C5FD")))
             for h in ["Categoria", "Total", "%"]]
        ]
        for item in dados_cat:
            cat_rows.append([
                Paragraph(item["categoria"].replace("_"," ").title(), s["corpo"]),
                Paragraph(_brl(item["total"]),
                          ParagraphStyle("rv", parent=s["corpo"], alignment=TA_RIGHT)),
                Paragraph(f"{item['pct']:.1f}%",
                          ParagraphStyle("rv", parent=s["corpo"], alignment=TA_RIGHT)),
            ])
        cat_t = Table(cat_rows, colWidths=[col_w*0.5, col_w*0.3, col_w*0.2])
        cat_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), NAVY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BRANCO, CINZA3]),
            ("LINEBELOW",     (0,0),(-1,-1), 0.5, CINZA4),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ]))

        # Gráfico de barras horizontais
        graf_cat = _grafico_pizza_simples(col_w, len(dados_cat[:8]) * 22 + 25, dados_cat)

        st.append(Paragraph("Despesas por categoria", s["secao"]))
        st.append(Spacer(1, 6))
        layout = Table([[cat_t, graf_cat]], colWidths=[col_w + 5*mm, col_w + 5*mm])
        layout.setStyle(TableStyle([
            ("VALIGN",      (0,0),(-1,-1), "TOP"),
            ("LEFTPADDING", (0,0),(-1,-1), 0),
            ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ]))
        st.append(layout)
        st.append(Spacer(1, 16))

    # ── Contas pagas ──
    st.append(Paragraph("Contas pagas no período", s["secao"]))
    st.append(Spacer(1, 6))

    if contas_pgs:
        cp_rows = [
            [Paragraph(h, ParagraphStyle("th", parent=s["label"],
                        textColor=colors.HexColor("#93C5FD")))
             for h in ["Descrição", "Categoria", "Valor pago", "Data"]]
        ]
        for c in contas_pgs:
            cp_rows.append([
                Paragraph(c.get("descricao","")[:45], s["corpo"]),
                Paragraph(c.get("categoria","").replace("_"," ").title(), s["corpo"]),
                Paragraph(_brl(c.get("valor_pago") or c.get("valor")),
                          ParagraphStyle("rv", parent=s["corpo"], alignment=TA_RIGHT)),
                Paragraph(c.get("data_pagamento","—") or "—", s["corpo"]),
            ])
        cp_t = Table(cp_rows, colWidths=[
            (W-2*M)*0.38, (W-2*M)*0.2, (W-2*M)*0.22, (W-2*M)*0.2
        ])
        cp_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), NAVY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BRANCO, CINZA3]),
            ("LINEBELOW",     (0,0),(-1,-1), 0.5, CINZA4),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ]))
        st.append(cp_t)
    else:
        st.append(Paragraph("Nenhuma conta paga no período.", s["corpo"]))

    st.append(Spacer(1, 20))
    st.append(HRFlowable(width="100%", thickness=0.5, color=CINZA4, spaceBefore=4))
    st.append(Paragraph(
        "PANIFICA GESTOR PRO  ·  SPYNET Tecnologia Forense &amp; Soluções Digitais Ltda.  "
        "·  CNPJ 64.000.808/0001-51  ·  Documento gerado automaticamente",
        s["rodape"]
    ))

    doc.build(st)
    buf.seek(0)
    return buf.read()


# ─── Endpoints ───────────────────────────────────────────────────────────────

@bp_relatorios.get("/financeiro")
@login_obrigatorio
def relatorio_financeiro_json(usuario_atual):
    tid  = usuario_atual.tenant_id
    hoje = date.today()
    ano  = int(request.args.get("ano",  hoje.year))
    mes  = int(request.args.get("mes",  hoje.month))

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

    contas_pagas = ContaPagar.query.filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "paga",
        extract("year",  ContaPagar.data_pagamento) == ano,
        extract("month", ContaPagar.data_pagamento) == mes,
    ).order_by(ContaPagar.data_pagamento.desc()).all()

    return sucesso(data={
        "periodo":              {"ano": ano, "mes": mes},
        "faturamento_total":    fat_mes,
        "despesas_total":       despesas_mes,
        "lucro_estimado":       round(lucro, 2),
        "margem_percentual":    margem,
        "saidas_por_categoria": [{"categoria": r.categoria, "total": float(r.total)} for r in saidas_cat],
        "contas_pagas":         [c.para_dict() for c in contas_pagas],
    })


@bp_relatorios.get("/financeiro/pdf")
@login_obrigatorio
def relatorio_financeiro_pdf(usuario_atual):
    tid  = usuario_atual.tenant_id
    hoje = date.today()
    ano  = int(request.args.get("ano",  hoje.year))
    mes  = int(request.args.get("mes",  hoje.month))

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

    contas_pagas = ContaPagar.query.filter(
        ContaPagar.tenant_id == tid,
        ContaPagar.status == "paga",
        extract("year",  ContaPagar.data_pagamento) == ano,
        extract("month", ContaPagar.data_pagamento) == mes,
    ).order_by(ContaPagar.data_pagamento.desc()).all()

    # Buscar fluxo das últimas 2 semanas para o gráfico
    from app.models.faturamento import Faturamento as Fat
    fluxo_semanal = Fat.fluxo_ultimos_dias(tid, 14)
    # Adicionar saídas ao fluxo
    from datetime import timedelta
    inicio = hoje - timedelta(days=13)
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
    for item in fluxo_semanal:
        item["saidas"] = mapa_saidas.get(item["data"], 0.0)

    tenant_nome = usuario_atual.tenant.nome if usuario_atual.tenant else "Padaria"
    periodo = {"ano": ano, "mes": mes}
    dados = {
        "faturamento_total":    fat_mes,
        "despesas_total":       despesas_mes,
        "lucro_estimado":       round(lucro, 2),
        "margem_percentual":    margem,
        "saidas_por_categoria": [{"categoria": r.categoria, "total": float(r.total)} for r in saidas_cat],
        "contas_pagas":         [c.para_dict() for c in contas_pagas],
    }

    try:
        pdf_bytes = _gerar_pdf_relatorio(tenant_nome, periodo, dados, fluxo_semanal)
        resp = make_response(pdf_bytes)
        resp.headers["Content-Type"]        = "application/pdf"
        resp.headers["Content-Disposition"] = (
            f'attachment; filename="relatorio_{tenant_nome.replace(" ","_")}_{ano}_{mes:02d}.pdf"'
        )
        logger.info("PDF gerado: %s %d/%d", tenant_nome, mes, ano)
        return resp
    except Exception as exc:
        logger.exception("Erro ao gerar PDF: %s", exc)
        return erro("Erro ao gerar o relatório PDF.", 500)


@bp_relatorios.get("/estoque")
@login_obrigatorio
def relatorio_estoque(usuario_atual):
    from app.models.estoque import ItemEstoque
    tid   = usuario_atual.tenant_id
    itens = ItemEstoque.listar_por_tenant(tid)
    return sucesso(data={
        "itens":         [i.para_dict() for i in itens],
        "total":         len(itens),
        "em_alerta":     sum(1 for i in itens if i.em_alerta),
    })


@bp_relatorios.get("/compras")
@login_obrigatorio
def relatorio_compras(usuario_atual):
    from app.models.compra import Compra
    tid  = usuario_atual.tenant_id
    hoje = date.today()
    ano  = int(request.args.get("ano",  hoje.year))
    mes  = int(request.args.get("mes",  hoje.month))
    total_mes = Compra.total_no_mes(tid, ano, mes)
    return sucesso(data={
        "periodo":    {"ano": ano, "mes": mes},
        "total_mes":  total_mes,
    })
