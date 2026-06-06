from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.estoque import UNIDADES_VALIDAS


class CriarItemEstoqueSchema(Schema):
    nome              = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    unidade           = fields.Str(required=True, validate=validate.OneOf(UNIDADES_VALIDAS))
    quantidade_atual  = fields.Decimal(load_default=0, as_string=False)
    quantidade_minima = fields.Decimal(load_default=0, as_string=False)
    custo_medio       = fields.Decimal(load_default=None, allow_none=True, as_string=False)

    @validates("quantidade_atual")
    def val_qtd(self, value, **kwargs):
        if float(value) < 0:
            raise ValidationError("Quantidade não pode ser negativa.")


class AtualizarItemEstoqueSchema(Schema):
    nome              = fields.Str(validate=validate.Length(min=2, max=120))
    unidade           = fields.Str(validate=validate.OneOf(UNIDADES_VALIDAS))
    quantidade_minima = fields.Decimal(as_string=False)
    ativo             = fields.Bool()


class AjusteEstoqueSchema(Schema):
    tipo       = fields.Str(required=True, validate=validate.OneOf(("entrada","saida","ajuste","perda")))
    quantidade = fields.Decimal(required=True, as_string=False)
    motivo     = fields.Str(load_default=None, allow_none=True)
    custo_unitario = fields.Decimal(load_default=None, allow_none=True, as_string=False)

    @validates("quantidade")
    def val_qtd(self, value, **kwargs):
        if float(value) <= 0:
            raise ValidationError("Quantidade deve ser maior que zero.")
