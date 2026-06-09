from app.extensions import db
from app.models.base import ModeloBase

CATEGORIAS_PRODUTO = (
    "paes",
    "bolos",
    "doces",
    "salgados",
    "bebidas",
    "insumos",
    "outros"
)


class Produto(ModeloBase):
    __tablename__ = "produtos"

    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    categoria = db.Column(
        db.String(50),
        nullable=False,
        default="outros"
    )

    codigo_barras = db.Column(
        db.String(50),
        nullable=True
    )

    unidade = db.Column(
        db.String(10),
        nullable=False,
        default="un"
    )

    preco_custo = db.Column(
        db.Numeric(12, 4),
        nullable=False,
        default=0
    )

    preco_venda = db.Column(
        db.Numeric(12, 4),
        nullable=False,
        default=0
    )

    estoque_atual = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    estoque_minimo = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    observacoes = db.Column(
        db.Text,
        nullable=True
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    tenant = db.relationship(
        "Tenant",
        back_populates="produtos"
    )

    @classmethod
    def buscar_por_tenant_e_id(cls, tenant_id, produto_id):
        return cls.query.filter_by(
            tenant_id=tenant_id,
            id=produto_id
        ).first()

    def desativar(self):
        self.ativo = False

    def para_dict(self):
        base = super().para_dict()

        base.update({
            "tenant_id": self.tenant_id,
            "nome": self.nome,
            "categoria": self.categoria,
            "codigo_barras": self.codigo_barras,
            "unidade": self.unidade,
            "preco_custo": float(self.preco_custo),
            "preco_venda": float(self.preco_venda),
            "estoque_atual": float(self.estoque_atual),
            "estoque_minimo": float(self.estoque_minimo),
            "observacoes": self.observacoes,
            "ativo": self.ativo
        })

        return base