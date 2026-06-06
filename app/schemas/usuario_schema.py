from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load
from app.models.usuario import PERFIS_VALIDOS


class LoginSchema(Schema):
    email = fields.Email(required=True)
    senha = fields.Str(required=True, load_only=True)

    @pre_load
    def normalizar(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].strip().lower()
        return data


class CriarUsuarioSchema(Schema):
    nome   = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    email  = fields.Email(required=True)
    senha  = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=72))
    perfil = fields.Str(load_default="operador", validate=validate.OneOf(PERFIS_VALIDOS))

    @pre_load
    def normalizar(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].strip().lower()
        if "nome" in data and isinstance(data["nome"], str):
            data["nome"] = data["nome"].strip()
        return data


class AtualizarUsuarioSchema(Schema):
    nome   = fields.Str(validate=validate.Length(min=2, max=120))
    perfil = fields.Str(validate=validate.OneOf(PERFIS_VALIDOS))
    ativo  = fields.Bool()


class AlterarSenhaSchema(Schema):
    senha_atual    = fields.Str(required=True, load_only=True)
    nova_senha     = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=72))
    confirmar_senha= fields.Str(required=True, load_only=True)


class RecuperarSenhaSchema(Schema):
    email = fields.Email(required=True)

    @pre_load
    def normalizar(self, data, **kwargs):
        if "email" in data:
            data["email"] = data["email"].strip().lower()
        return data


class RedefinirSenhaSchema(Schema):
    token          = fields.Str(required=True)
    nova_senha     = fields.Str(required=True, validate=validate.Length(min=8, max=72))
    confirmar_senha= fields.Str(required=True)
