import logging
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.estoque import ItemEstoque, MovimentacaoEstoque, UNIDADES_VALIDAS
from app.schemas.estoque_schema import CriarItemEstoqueSchema, AtualizarItemEstoqueSchema, AjusteEstoqueSchema
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import sucesso, criado, erro, nao_encontrado, regra_negocio, validacao_erro
from app.services.audit_service import registrar_auditoria

bp_estoque = Blueprint("estoque", __name__)
logger = logging.getLogger(__name__)

_schema_criar    = CriarItemEstoqueSchema()
_schema_atualizar= AtualizarItemEstoqueSchema()
_schema_ajuste   = AjusteEstoqueSchema()


@bp_estoque.get("/unidades")
@login_obrigatorio
def listar_unidades(usuario_atual):
    return sucesso(data={"unidades": list(UNIDADES_VALIDAS)})


@bp_estoque.get("/alertas")
@login_obrigatorio
def listar_alertas(usuario_atual):
    itens = ItemEstoque.listar_por_tenant(usuario_atual.tenant_id, em_alerta=True)
    return sucesso(data={
        "itens":  [i.para_dict() for i in itens],
        "total":  len(itens),
    })


@bp_estoque.get("")
@login_obrigatorio
def listar(usuario_atual):
    tid = usuario_atual.tenant_id
    inativos = request.args.get("inativos", "false").lower() == "true"
    alerta   = request.args.get("alerta",   "false").lower() == "true"
    busca    = request.args.get("busca")

    q = ItemEstoque.query.filter_by(tenant_id=tid)
    if not inativos:
        q = q.filter_by(ativo=True)
    if alerta:
        q = q.filter(ItemEstoque.quantidade_atual <= ItemEstoque.quantidade_minima)
    if busca:
        q = q.filter(ItemEstoque.nome.ilike(f"%{busca}%"))

    itens = q.order_by(ItemEstoque.nome.asc()).all()
    return sucesso(data={
        "itens":           [i.para_dict() for i in itens],
        "total":           len(itens),
        "total_alertas":   ItemEstoque.contar_alertas(tid),
    })


@bp_estoque.post("")
@login_obrigatorio
def criar(usuario_atual):
    try:
        dados = _schema_criar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    # Verificar duplicidade de nome
    existente = ItemEstoque.query.filter_by(
        tenant_id=usuario_atual.tenant_id, nome=dados["nome"]
    ).first()
    if existente:
        if not existente.ativo:
            existente.ativo = True
            db.session.commit()
            return sucesso(data=existente.para_dict(), message="Item reativado.")
        return erro("Já existe um item com este nome.", 409)

    try:
        item = ItemEstoque(
            tenant_id=usuario_atual.tenant_id,
            nome=dados["nome"],
            unidade=dados["unidade"],
            quantidade_atual=dados.get("quantidade_atual", 0),
            quantidade_minima=dados.get("quantidade_minima", 0),
            custo_medio=dados.get("custo_medio"),
        )
        db.session.add(item)
        db.session.flush()
        registrar_auditoria(
            tenant_id=usuario_atual.tenant_id, tabela="itens_estoque",
            operacao="INSERT", registro_id=item.id,
            dados_depois=item.para_dict(), usuario_id=usuario_atual.id,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar item: %s", exc)
        return erro("Erro interno ao criar item.", 500)

    logger.info("Item criado: %s por %s", item.nome, usuario_atual.email)
    return criado(data=item.para_dict(), message="Item cadastrado.")


@bp_estoque.get("/<string:item_id>")
@login_obrigatorio
def obter(item_id, usuario_atual):
    item = ItemEstoque.query.filter_by(id=item_id, tenant_id=usuario_atual.tenant_id).first()
    if not item:
        return nao_encontrado("Item de estoque")

    movs = MovimentacaoEstoque.query.filter_by(
        item_id=item_id, tenant_id=usuario_atual.tenant_id
    ).order_by(MovimentacaoEstoque.criado_em.desc()).limit(20).all()

    dados = item.para_dict()
    dados["movimentacoes_recentes"] = [m.para_dict() for m in movs]
    return sucesso(data=dados)


@bp_estoque.put("/<string:item_id>")
@login_obrigatorio
def atualizar(item_id, usuario_atual):
    item = ItemEstoque.query.filter_by(id=item_id, tenant_id=usuario_atual.tenant_id).first()
    if not item:
        return nao_encontrado("Item de estoque")

    try:
        dados = _schema_atualizar.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    antes = item.para_dict()
    for campo, valor in dados.items():
        setattr(item, campo, valor)

    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="itens_estoque",
        operacao="UPDATE", registro_id=item.id,
        dados_antes=antes, dados_depois=item.para_dict(), usuario_id=usuario_atual.id,
    )
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao atualizar item: %s", exc)
        return erro("Erro interno.", 500)

    return sucesso(data=item.para_dict(), message="Item atualizado.")


@bp_estoque.post("/<string:item_id>/ajuste")
@login_obrigatorio
def ajuste_manual(item_id, usuario_atual):
    """Ajuste manual de estoque (entrada, saída, ajuste ou perda)."""
    item = ItemEstoque.query.filter_by(id=item_id, tenant_id=usuario_atual.tenant_id).first()
    if not item:
        return nao_encontrado("Item de estoque")

    try:
        dados = _schema_ajuste.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    tipo = dados["tipo"]
    qtd  = float(dados["quantidade"])

    if tipo in ("ajuste", "perda") and not dados.get("motivo"):
        return regra_negocio("Ajustes e perdas exigem um motivo (mínimo 5 caracteres).")
    if dados.get("motivo") and len(dados["motivo"]) < 5:
        return regra_negocio("Motivo muito curto — mínimo 5 caracteres.")

    saldo_ant = float(item.quantidade_atual)

    if tipo in ("saida", "perda"):
        if saldo_ant < qtd:
            return regra_negocio(
                f"Estoque insuficiente. Disponível: {saldo_ant} {item.unidade}."
            )
        saldo_novo = saldo_ant - qtd
    else:  # entrada ou ajuste
        saldo_novo = saldo_ant + qtd if tipo == "entrada" else qtd

    try:
        item.quantidade_atual = saldo_novo
        if tipo == "entrada" and dados.get("custo_unitario"):
            item.atualizar_custo_medio(qtd, float(dados["custo_unitario"]))

        mov = MovimentacaoEstoque(
            tenant_id=usuario_atual.tenant_id,
            item_id=item.id,
            criado_por_id=usuario_atual.id,
            tipo=tipo,
            quantidade=qtd,
            saldo_anterior=saldo_ant,
            saldo_posterior=saldo_novo,
            custo_unitario=dados.get("custo_unitario"),
            origem="manual",
            motivo=dados.get("motivo"),
        )
        db.session.add(mov)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro no ajuste de estoque: %s", exc)
        return erro("Erro interno.", 500)

    logger.info("Ajuste %s: %s %s%s por %s", tipo, item.nome, qtd, item.unidade, usuario_atual.email)
    return sucesso(data=item.para_dict(), message=f"Ajuste de {tipo} registrado.")


@bp_estoque.delete("/<string:item_id>")
@proprietario_obrigatorio
def desativar(item_id, usuario_atual):
    item = ItemEstoque.query.filter_by(id=item_id, tenant_id=usuario_atual.tenant_id).first()
    if not item:
        return nao_encontrado("Item de estoque")

    antes = item.para_dict()
    item.ativo = False
    registrar_auditoria(
        tenant_id=usuario_atual.tenant_id, tabela="itens_estoque",
        operacao="DELETE", registro_id=item.id,
        dados_antes=antes, usuario_id=usuario_atual.id,
    )
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return erro("Erro interno.", 500)

    return sucesso(message="Item desativado.")
