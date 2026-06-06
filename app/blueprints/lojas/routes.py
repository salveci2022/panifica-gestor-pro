import logging
from flask import Blueprint, request
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import db
from app.models.loja import Loja
from app.utils.auth import login_obrigatorio, proprietario_obrigatorio
from app.utils.respostas import sucesso, criado, erro, nao_encontrado, validacao_erro
from app.services.audit_service import registrar_auditoria

bp_lojas = Blueprint("lojas_bp", __name__)
logger   = logging.getLogger(__name__)


class CriarLojaSchema(Schema):
    nome     = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    codigo   = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=20))
    endereco = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=200))

class AtualizarLojaSchema(Schema):
    nome     = fields.Str(validate=validate.Length(min=2, max=80))
    codigo   = fields.Str(allow_none=True)
    endereco = fields.Str(allow_none=True)
    ativo    = fields.Bool()

_sc = CriarLojaSchema()
_sa = AtualizarLojaSchema()


@bp_lojas.get("")
@login_obrigatorio
def listar(usuario_atual):
    inativos = request.args.get("inativos","false").lower() == "true"
    lojas = Loja.listar_por_tenant(usuario_atual.tenant_id, apenas_ativas=not inativos)
    return sucesso(data=[l.para_dict() for l in lojas])


@bp_lojas.post("")
@proprietario_obrigatorio
def criar(usuario_atual):
    try:
        dados = _sc.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)

    if dados.get("codigo"):
        existente = Loja.query.filter_by(tenant_id=usuario_atual.tenant_id, codigo=dados["codigo"]).first()
        if existente:
            return erro(f"Já existe uma loja com o código '{dados['codigo']}'.", 409)

    try:
        loja = Loja(tenant_id=usuario_atual.tenant_id, nome=dados["nome"],
                    codigo=dados.get("codigo"), endereco=dados.get("endereco"))
        db.session.add(loja)
        db.session.flush()
        registrar_auditoria(tenant_id=usuario_atual.tenant_id, tabela="lojas",
                            operacao="INSERT", registro_id=loja.id,
                            dados_depois=loja.para_dict(), usuario_id=usuario_atual.id)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro ao criar loja: %s", exc)
        return erro("Erro interno.", 500)

    return criado(data=loja.para_dict(), message="Loja cadastrada.")


@bp_lojas.get("/resumo/contas")
@login_obrigatorio
def resumo_por_loja(usuario_atual):
    from app.models.conta_pagar import ContaPagar
    from sqlalchemy import func
    tid = usuario_atual.tenant_id
    lojas = Loja.listar_por_tenant(tid)
    resultado = []
    for loja in lojas:
        pend = db.session.query(func.sum(ContaPagar.valor)).filter(
            ContaPagar.tenant_id==tid, ContaPagar.loja_id==loja.id,
            ContaPagar.status.in_(["pendente","vencida"])).scalar()
        pago = db.session.query(func.sum(ContaPagar.valor_pago)).filter(
            ContaPagar.tenant_id==tid, ContaPagar.loja_id==loja.id,
            ContaPagar.status=="paga").scalar()
        venc = ContaPagar.query.filter_by(tenant_id=tid, loja_id=loja.id, status="vencida").count()
        resultado.append({
            "loja_id": loja.id, "loja_nome": loja.nome, "loja_codigo": loja.codigo,
            "total_pendente": float(pend or 0), "total_pago": float(pago or 0),
            "contas_vencidas": venc,
        })
    return sucesso(data=resultado)


@bp_lojas.get("/<string:loja_id>")
@login_obrigatorio
def obter(loja_id, usuario_atual):
    loja = Loja.query.filter_by(id=loja_id, tenant_id=usuario_atual.tenant_id).first()
    if not loja: return nao_encontrado("Loja")
    return sucesso(data=loja.para_dict())


@bp_lojas.put("/<string:loja_id>")
@proprietario_obrigatorio
def atualizar(loja_id, usuario_atual):
    loja = Loja.query.filter_by(id=loja_id, tenant_id=usuario_atual.tenant_id).first()
    if not loja: return nao_encontrado("Loja")
    try:
        dados = _sa.load(request.get_json() or {})
    except ValidationError as e:
        return validacao_erro(e.messages)
    antes = loja.para_dict()
    for k, v in dados.items(): setattr(loja, k, v)
    registrar_auditoria(tenant_id=usuario_atual.tenant_id, tabela="lojas",
                        operacao="UPDATE", registro_id=loja.id,
                        dados_antes=antes, dados_depois=loja.para_dict(), usuario_id=usuario_atual.id)
    try: db.session.commit()
    except: db.session.rollback(); return erro("Erro interno.", 500)
    return sucesso(data=loja.para_dict(), message="Loja atualizada.")


@bp_lojas.delete("/<string:loja_id>")
@proprietario_obrigatorio
def desativar(loja_id, usuario_atual):
    loja = Loja.query.filter_by(id=loja_id, tenant_id=usuario_atual.tenant_id).first()
    if not loja: return nao_encontrado("Loja")
    from app.models.conta_pagar import ContaPagar
    abertas = ContaPagar.query.filter_by(loja_id=loja_id, status="pendente").count()
    if abertas > 0:
        return erro(f"Esta loja tem {abertas} conta(s) pendente(s).", 422)
    loja.ativo = False
    registrar_auditoria(tenant_id=usuario_atual.tenant_id, tabela="lojas",
                        operacao="DELETE", registro_id=loja.id,
                        dados_antes=loja.para_dict(), usuario_id=usuario_atual.id)
    try: db.session.commit()
    except: db.session.rollback(); return erro("Erro interno.", 500)
    return sucesso(message="Loja desativada.")
