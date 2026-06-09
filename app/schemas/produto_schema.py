from marshmallow import Schema, fields, validate, pre_load

CATEGORIAS_PRODUTO = (
    "paes",
    "bolos",
    "doces",
    "salgados",
    "bebidas",
    "insumos",
    "outros"
)

UNIDADES_PRODUTO = (
    "un",
    "kg",
    "g",
    "l",
    "ml",
    "cx",
    "pct",
    "dz"
)


class CriarProdutoSchema(Schema):
    nome = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120)
    )

    categoria = fields.Str(
        required=True,
        validate=validate.OneOf(CATEGORIAS_PRODUTO)
    )

    codigo_barras = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=50)
    )

    unidade = fields.Str(
        required=True,
        validate=validate.OneOf(UNIDADES_PRODUTO)
    )

    preco_custo = fields.Decimal(
        required=True,
        as_string=False
    )

    preco_venda = fields.Decimal(
        required=True,
        as_string=False
    )

    estoque_atual = fields.Decimal(
        load_default=0,
        as_string=False
    )

    estoque_minimo = fields.Decimal(
        load_default=0,
        as_string=False
    )

    observacoes = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=1000)
    )

    @pre_load
    def normalizar(self, data, **kwargs):
        if "nome" in data and isinstance(data["nome"], str):
            data["nome"] = data["nome"].strip()

        if data.get("codigo_barras") == "":
            data["codigo_barras"] = None

        return data


class AtualizarProdutoSchema(Schema):
    nome = fields.Str(
        validate=validate.Length(min=2, max=120)
    )

    categoria = fields.Str(
        validate=validate.OneOf(CATEGORIAS_PRODUTO)
    )

    codigo_barras = fields.Str(
        allow_none=True,
        validate=validate.Length(max=50)
    )

    unidade = fields.Str(
        validate=validate.OneOf(UNIDADES_PRODUTO)
    )

    preco_custo = fields.Decimal(
        as_string=False
    )

    preco_venda = fields.Decimal(
        as_string=False
    )

    estoque_atual = fields.Decimal(
        as_string=False
    )

    estoque_minimo = fields.Decimal(
        as_string=False
    )

    observacoes = fields.Str(
        allow_none=True,
        validate=validate.Length(max=1000)
    )

    ativo = fields.Bool()