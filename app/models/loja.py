from app.extensions import db
from app.models.base import ModeloBase


class Loja(ModeloBase):
    """Unidade / loja de um tenant."""
    __tablename__ = "lojas"

    tenant_id  = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    nome       = db.Column(db.String(80),  nullable=False)
    codigo     = db.Column(db.String(20),  nullable=True)
    endereco   = db.Column(db.String(200), nullable=True)
    ativo      = db.Column(db.Boolean, default=True, nullable=False)

    tenant       = db.relationship("Tenant",     back_populates="lojas")
    contas_pagar = db.relationship("ContaPagar", back_populates="loja", lazy="dynamic")

    def __repr__(self):
        return f"<Loja {self.codigo or self.nome}>"

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "tenant_id": self.tenant_id,
            "nome":      self.nome,
            "codigo":    self.codigo,
            "endereco":  self.endereco,
            "ativo":     self.ativo,
        })
        return base

    @classmethod
    def listar_por_tenant(cls, tenant_id: str, apenas_ativas: bool = True):
        q = cls.query.filter_by(tenant_id=tenant_id)
        if apenas_ativas:
            q = q.filter_by(ativo=True)
        return q.order_by(cls.nome.asc()).all()
