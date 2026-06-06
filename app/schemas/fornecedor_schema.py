from marshmallow import Schema, fields, validate, pre_load
from app.models.fornecedor import CATEGORIAS_FORNECEDOR


class CriarFornecedorSchema(Schema):
    nome         = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    cnpj_cpf     = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=18))
    categoria    = fields.Str(required=True, validate=validate.OneOf(CATEGORIAS_FORNECEDOR))
    telefone     = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=20))
    whatsapp     = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=20))
    email        = fields.Email(load_default=None, allow_none=True)
    contato_nome = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=80))
    endereco     = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=500))
    observacoes  = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=1000))

    @pre_load
    def normalizar(self, data, **kwargs):
        if "nome" in data and isinstance(data["nome"], str):
            data["nome"] = data["nome"].strip()
        if data.get("email") == "":
            data["email"] = None
        return data


class AtualizarFornecedorSchema(Schema):
    nome         = fields.Str(validate=validate.Length(min=2, max=120))
    cnpj_cpf     = fields.Str(validate=validate.Length(max=18), allow_none=True)
    categoria    = fields.Str(validate=validate.OneOf(CATEGORIAS_FORNECEDOR))
    telefone     = fields.Str(validate=validate.Length(max=20), allow_none=True)
    whatsapp     = fields.Str(validate=validate.Length(max=20), allow_none=True)
    email        = fields.Email(allow_none=True)
    contato_nome = fields.Str(validate=validate.Length(max=80), allow_none=True)
    endereco     = fields.Str(validate=validate.Length(max=500), allow_none=True)
    observacoes  = fields.Str(validate=validate.Length(max=1000), allow_none=True)
    ativo        = fields.Bool()
