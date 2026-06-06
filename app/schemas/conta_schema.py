from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.conta_pagar import CATEGORIAS_VALIDAS, FORMAS_PAGAMENTO, STATUS_VALIDOS


class CriarContaSchema(Schema):
    descricao       = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    categoria       = fields.Str(required=True, validate=validate.OneOf(CATEGORIAS_VALIDAS))
    valor           = fields.Decimal(required=True, as_string=False)
    vencimento      = fields.Date(required=True)
    forma_pagamento = fields.Str(load_default=None, allow_none=True)
    fornecedor_id   = fields.Str(load_default=None, allow_none=True)
    loja_id         = fields.Str(load_default=None, allow_none=True)
    numero_pedido   = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=40))
    loja_id        = fields.Str(load_default=None, allow_none=True)
    numero_pedido  = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=40))
    observacoes     = fields.Str(load_default=None, allow_none=True,
                                  validate=validate.Length(max=1000))

    @validates("valor")
    def validar_valor(self, value, **kwargs):
        if float(value) <= 0:
            raise ValidationError("O valor deve ser maior que zero.")

    @validates("forma_pagamento")
    def validar_forma(self, value, **kwargs):
        if value is not None and value not in FORMAS_PAGAMENTO:
            raise ValidationError(f"Forma inválida. Use: {', '.join(FORMAS_PAGAMENTO)}")


class AtualizarContaSchema(Schema):
    descricao       = fields.Str(validate=validate.Length(min=2, max=200))
    categoria       = fields.Str(validate=validate.OneOf(CATEGORIAS_VALIDAS))
    valor           = fields.Decimal(as_string=False)
    vencimento      = fields.Date()
    forma_pagamento = fields.Str(allow_none=True)
    fornecedor_id   = fields.Str(allow_none=True)
    observacoes     = fields.Str(allow_none=True, validate=validate.Length(max=1000))

    @validates("valor")
    def validar_valor(self, value, **kwargs):
        if value is not None and float(value) <= 0:
            raise ValidationError("O valor deve ser maior que zero.")


class PagarContaSchema(Schema):
    valor_pago     = fields.Decimal(load_default=None, allow_none=True, as_string=False)
    data_pagamento = fields.Date(load_default=None, allow_none=True)

    @validates("valor_pago")
    def validar_valor_pago(self, value, **kwargs):
        if value is not None and float(value) <= 0:
            raise ValidationError("O valor pago deve ser maior que zero.")


class FiltroContaSchema(Schema):  # noqa
    status        = fields.Str(load_default=None, allow_none=True)
    pagina        = fields.Int(load_default=1, validate=validate.Range(min=1))
    por_pagina    = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    fornecedor_id = fields.Str(load_default=None, allow_none=True)
    categoria     = fields.Str(load_default=None, allow_none=True)

    @validates("status")
    def validar_status(self, value, **kwargs):
        if value is not None and value not in STATUS_VALIDOS:
            raise ValidationError(f"Status inválido. Opções: {', '.join(STATUS_VALIDOS)}")
