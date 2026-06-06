from app.extensions import db
from app.models.base import ModeloBase, agora_utc
from datetime import date

STATUS_COMPRA    = ("pendente", "pago", "cancelado")
FORMAS_PAGAMENTO = ("pix", "boleto", "cartao_debito", "cartao_credito",
                    "dinheiro", "transferencia", "cheque")


class Compra(ModeloBase):
    """Registro de compra de insumos de um tenant."""
    __tablename__ = "compras"

    tenant_id         = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    fornecedor_id     = db.Column(db.String(36), db.ForeignKey("fornecedores.id"), nullable=True)
    criado_por_id     = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=True)

    data_compra       = db.Column(db.Date, nullable=False, default=date.today, index=True)
    numero_nota       = db.Column(db.String(40), nullable=True)
    valor_total       = db.Column(db.Numeric(12, 2), nullable=False)
    forma_pagamento   = db.Column(db.String(30), nullable=True)
    status_pagamento  = db.Column(db.String(20), default="pendente", nullable=False)
    observacoes       = db.Column(db.Text, nullable=True)

    # Relacionamentos
    tenant      = db.relationship("Tenant",      back_populates="compras")
    fornecedor  = db.relationship("Fornecedor",  back_populates="compras")
    criado_por  = db.relationship("Usuario",     foreign_keys=[criado_por_id])
    itens       = db.relationship("CompraItem",  back_populates="compra",
                                  cascade="all, delete-orphan", lazy="joined")

    def __repr__(self):
        return f"<Compra {self.data_compra} R${self.valor_total}>"

    def para_dict(self, incluir_itens: bool = True):
        base = super().para_dict()
        base.update({
            "tenant_id":        self.tenant_id,
            "fornecedor_id":    self.fornecedor_id,
            "fornecedor_nome":  self.fornecedor.nome if self.fornecedor else None,
            "criado_por_id":    self.criado_por_id,
            "data_compra":      self.data_compra.isoformat() if self.data_compra else None,
            "numero_nota":      self.numero_nota,
            "valor_total":      float(self.valor_total),
            "forma_pagamento":  self.forma_pagamento,
            "status_pagamento": self.status_pagamento,
            "observacoes":      self.observacoes,
        })
        if incluir_itens:
            base["itens"] = [i.para_dict() for i in (self.itens or [])]
        return base

    @classmethod
    def listar_por_tenant(cls, tenant_id: str, pagina: int = 1, por_pagina: int = 20,
                          fornecedor_id: str = None):
        q = cls.query.filter_by(tenant_id=tenant_id)
        if fornecedor_id:
            q = q.filter_by(fornecedor_id=fornecedor_id)
        return q.order_by(cls.data_compra.desc()).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )

    @classmethod
    def total_no_mes(cls, tenant_id: str, ano: int, mes: int) -> float:
        from sqlalchemy import func, extract
        from app.extensions import db as _db
        resultado = _db.session.query(func.sum(cls.valor_total)).filter(
            cls.tenant_id == tenant_id,
            extract("year",  cls.data_compra) == ano,
            extract("month", cls.data_compra) == mes,
        ).scalar()
        return float(resultado or 0)


class CompraItem(ModeloBase):
    """Item de uma compra."""
    __tablename__ = "compra_itens"

    compra_id       = db.Column(db.String(36), db.ForeignKey("compras.id"), nullable=False, index=True)
    item_estoque_id = db.Column(db.String(36), db.ForeignKey("itens_estoque.id"), nullable=True)

    descricao       = db.Column(db.String(200), nullable=False)
    unidade         = db.Column(db.String(20),  nullable=False, default="kg")
    quantidade      = db.Column(db.Numeric(12, 3), nullable=False)
    valor_unitario  = db.Column(db.Numeric(12, 4), nullable=False)
    valor_total     = db.Column(db.Numeric(12, 2), nullable=False)

    compra       = db.relationship("Compra",       back_populates="itens")
    item_estoque = db.relationship("ItemEstoque",  foreign_keys=[item_estoque_id])

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "compra_id":         self.compra_id,
            "item_estoque_id":   self.item_estoque_id,
            "item_estoque_nome": self.item_estoque.nome if self.item_estoque else None,
            "descricao":         self.descricao,
            "unidade":           self.unidade,
            "quantidade":        float(self.quantidade),
            "valor_unitario":    float(self.valor_unitario),
            "valor_total":       float(self.valor_total),
        })
        return base
