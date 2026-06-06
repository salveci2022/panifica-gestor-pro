from app.extensions import db
from app.models.base import ModeloBase


class Tenant(ModeloBase):
    """Representa uma padaria cliente do sistema."""
    __tablename__ = "tenants"

    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    email_contato = db.Column(db.String(180), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    logo_url = db.Column(db.Text, nullable=True)
    plano = db.Column(db.String(20), default="basico", nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    # Relacionamentos
    usuarios = db.relationship("Usuario", back_populates="tenant", lazy="dynamic", cascade="all, delete-orphan")
    contas_pagar = db.relationship("ContaPagar", back_populates="tenant", lazy="dynamic")
    fornecedores = db.relationship("Fornecedor", back_populates="tenant", lazy="dynamic")
    faturamentos  = db.relationship("Faturamento",    back_populates="tenant", lazy="dynamic")
    lojas         = db.relationship("Loja",           back_populates="tenant", lazy="dynamic", cascade="all, delete-orphan")
    itens_estoque = db.relationship("ItemEstoque",   back_populates="tenant", lazy="dynamic")
    lojas         = db.relationship("Loja",            back_populates="tenant", lazy="dynamic")
    compras       = db.relationship("Compra",         back_populates="tenant", lazy="dynamic")
    producoes     = db.relationship("ProducaoDiaria", back_populates="tenant", lazy="dynamic")

    def __repr__(self):
        return f"<Tenant {self.nome}>"

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "nome": self.nome,
            "cnpj": self.cnpj,
            "email_contato": self.email_contato,
            "telefone": self.telefone,
            "logo_url": self.logo_url,
            "plano": self.plano,
            "ativo": self.ativo,
        })
        return base
