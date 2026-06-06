from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load
from app.models.compra import STATUS_COMPRA, FORMAS_PAGAMENTO


class CompraItemSchema(Schema):
    descricao       = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    unidade         = fields.Str(required=True)
    quantidade      = fields.Decimal(required=True, as_string=False)
    valor_unitario  = fields.Decimal(required=True, as_string=False)
    item_estoque_id = fields.Str(load_default=None, allow_none=True)

    @validates("quantidade")
    def val_qtd(self, value, **kwargs):
        if float(value) <= 0:
            raise ValidationError("Quantidade deve ser maior que zero.")

    @validates("valor_unitario")
    def val_vl(self, value, **kwargs):
        if float(value) <= 0:
            raise ValidationError("Valor unitário deve ser maior que zero.")


class CriarCompraSchema(Schema):
    data_compra      = fields.Date(required=True)
    fornecedor_id    = fields.Str(load_default=None, allow_none=True)
    numero_nota      = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=40))
    forma_pagamento  = fields.Str(load_default=None, allow_none=True)
    status_pagamento = fields.Str(load_default="pendente", validate=validate.OneOf(STATUS_COMPRA))
    observacoes      = fields.Str(load_default=None, allow_none=True)
    itens            = fields.List(fields.Nested(CompraItemSchema), required=True, validate=validate.Length(min=1))

    @validates("itens")
    def val_itens(self, value, **kwargs):
        if not value:
            raise ValidationError("A compra deve ter pelo menos um item.")


class FiltroCompraSchema(Schema):
    pagina         = fields.Int(load_default=1, validate=validate.Range(min=1))
    por_pagina     = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    fornecedor_id  = fields.Str(load_default=None, allow_none=True)
