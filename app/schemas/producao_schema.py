from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.producao import CATEGORIAS_PRODUCAO, UNIDADES_PRODUCAO


class CriarProducaoSchema(Schema):
    data_producao  = fields.Date(required=True)
    produto        = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    categoria      = fields.Str(required=True, validate=validate.OneOf(CATEGORIAS_PRODUCAO))
    quantidade     = fields.Decimal(required=True, as_string=False)
    unidade        = fields.Str(required=True, validate=validate.OneOf(UNIDADES_PRODUCAO))
    custo_estimado = fields.Decimal(load_default=None, allow_none=True, as_string=False)
    observacoes    = fields.Str(load_default=None, allow_none=True)

    @validates("quantidade")
    def val_qtd(self, value, **kwargs):
        if float(value) <= 0:
            raise ValidationError("Quantidade deve ser maior que zero.")


class FiltroProducaoSchema(Schema):
    data       = fields.Date(load_default=None, allow_none=True)
    data_inicio= fields.Date(load_default=None, allow_none=True)
    data_fim   = fields.Date(load_default=None, allow_none=True)
    categoria  = fields.Str(load_default=None, allow_none=True,
                             validate=validate.OneOf(CATEGORIAS_PRODUCAO))
    pagina     = fields.Int(load_default=1, validate=validate.Range(min=1))
    por_pagina = fields.Int(load_default=30, validate=validate.Range(min=1, max=100))
