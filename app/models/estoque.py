from app.extensions import db
from app.models.base import ModeloBase, agora_utc

UNIDADES_VALIDAS = ("kg", "g", "l", "ml", "un", "cx", "sc", "dz", "pct")


class ItemEstoque(ModeloBase):
    """Item de estoque de um tenant."""
    __tablename__ = "itens_estoque"

    tenant_id          = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    nome               = db.Column(db.String(120), nullable=False)
    unidade            = db.Column(db.String(10),  nullable=False, default="kg")
    quantidade_atual   = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    quantidade_minima  = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    custo_medio        = db.Column(db.Numeric(12, 4), nullable=True)
    ativo              = db.Column(db.Boolean, default=True, nullable=False)

    tenant         = db.relationship("Tenant", back_populates="itens_estoque")
    movimentacoes  = db.relationship("MovimentacaoEstoque", back_populates="item",
                                     lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ItemEstoque {self.nome} {self.quantidade_atual}{self.unidade}>"

    @property
    def em_alerta(self) -> bool:
        return float(self.quantidade_atual) <= float(self.quantidade_minima)

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "tenant_id":         self.tenant_id,
            "nome":              self.nome,
            "unidade":           self.unidade,
            "quantidade_atual":  float(self.quantidade_atual),
            "quantidade_minima": float(self.quantidade_minima),
            "custo_medio":       float(self.custo_medio) if self.custo_medio else None,
            "ativo":             self.ativo,
            "em_alerta":         self.em_alerta,
        })
        return base

    def atualizar_custo_medio(self, qtd_entrada: float, custo_unitario: float) -> None:
        """Recalcula custo médio ponderado ao receber nova entrada."""
        qtd_atual   = float(self.quantidade_atual or 0)
        custo_atual = float(self.custo_medio or custo_unitario)
        total_qtd   = qtd_atual + qtd_entrada
        if total_qtd > 0:
            self.custo_medio = ((qtd_atual * custo_atual) + (qtd_entrada * custo_unitario)) / total_qtd

    @classmethod
    def listar_por_tenant(cls, tenant_id: str, apenas_ativos: bool = True, em_alerta: bool = False):
        q = cls.query.filter_by(tenant_id=tenant_id)
        if apenas_ativos:
            q = q.filter_by(ativo=True)
        if em_alerta:
            q = q.filter(cls.quantidade_atual <= cls.quantidade_minima)
        return q.order_by(cls.nome.asc()).all()

    @classmethod
    def contar_alertas(cls, tenant_id: str) -> int:
        return cls.query.filter(
            cls.tenant_id == tenant_id,
            cls.ativo == True,
            cls.quantidade_atual <= cls.quantidade_minima,
        ).count()


class MovimentacaoEstoque(ModeloBase):
    """Histórico de movimentações de um item de estoque."""
    __tablename__ = "movimentacoes_estoque"

    tenant_id        = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    item_id          = db.Column(db.String(36), db.ForeignKey("itens_estoque.id"), nullable=False, index=True)
    criado_por_id    = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=True)

    tipo             = db.Column(db.String(20), nullable=False)   # entrada | saida | ajuste | perda
    quantidade       = db.Column(db.Numeric(12, 3), nullable=False)
    saldo_anterior   = db.Column(db.Numeric(12, 3), nullable=False)
    saldo_posterior  = db.Column(db.Numeric(12, 3), nullable=False)
    custo_unitario   = db.Column(db.Numeric(12, 4), nullable=True)
    origem           = db.Column(db.String(30), nullable=True)   # compra | producao | manual
    origem_id        = db.Column(db.String(36), nullable=True)
    motivo           = db.Column(db.Text, nullable=True)

    item       = db.relationship("ItemEstoque", back_populates="movimentacoes")
    criado_por = db.relationship("Usuario", foreign_keys=[criado_por_id])

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "tenant_id":       self.tenant_id,
            "item_id":         self.item_id,
            "item_nome":       self.item.nome if self.item else None,
            "tipo":            self.tipo,
            "quantidade":      float(self.quantidade),
            "saldo_anterior":  float(self.saldo_anterior),
            "saldo_posterior": float(self.saldo_posterior),
            "custo_unitario":  float(self.custo_unitario) if self.custo_unitario else None,
            "origem":          self.origem,
            "origem_id":       self.origem_id,
            "motivo":          self.motivo,
        })
        return base
