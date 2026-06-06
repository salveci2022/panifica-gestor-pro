from marshmallow import Schema, fields, validate, validates, ValidationError


class CriarFaturamentoSchema(Schema):
    data      = fields.Date(required=True)
    valor     = fields.Decimal(required=True, as_string=False)
    descricao = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=200))

    @validates("valor")
    def validar_valor(self, value, **kwargs):
        if float(value) <= 0:
            raise ValidationError("O valor do faturamento deve ser maior que zero.")


class FiltroFluxoSchema(Schema):
    dias = fields.Int(load_default=30, validate=validate.Range(min=1, max=365))
    ano  = fields.Int(load_default=None, allow_none=True)
    mes  = fields.Int(load_default=None, allow_none=True, validate=validate.Range(min=1, max=12))
