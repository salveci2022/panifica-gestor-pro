from app.extensions import db
from app.models.base import ModeloBase
from datetime import date

CATEGORIAS_PRODUCAO = ("paes", "bolos", "salgados", "doces", "bebidas", "outro")
UNIDADES_PRODUCAO   = ("un", "kg", "bandeja", "dz", "pct")


class ProducaoDiaria(ModeloBase):
    """Registro de produção diária de um tenant."""
    __tablename__ = "producao_diaria"

    tenant_id      = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    criado_por_id  = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=True)

    data_producao  = db.Column(db.Date, nullable=False, default=date.today, index=True)
    produto        = db.Column(db.String(120), nullable=False)
    categoria      = db.Column(db.String(60),  nullable=False, default="paes")
    quantidade     = db.Column(db.Numeric(10, 2), nullable=False)
    unidade        = db.Column(db.String(20),  nullable=False, default="un")
    custo_estimado = db.Column(db.Numeric(12, 2), nullable=True)
    observacoes    = db.Column(db.Text, nullable=True)

    tenant     = db.relationship("Tenant",  back_populates="producoes")
    criado_por = db.relationship("Usuario", foreign_keys=[criado_por_id])

    def __repr__(self):
        return f"<Producao {self.produto} {self.quantidade}{self.unidade}>"

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "tenant_id":      self.tenant_id,
            "criado_por_id":  self.criado_por_id,
            "data_producao":  self.data_producao.isoformat() if self.data_producao else None,
            "produto":        self.produto,
            "categoria":      self.categoria,
            "quantidade":     float(self.quantidade),
            "unidade":        self.unidade,
            "custo_estimado": float(self.custo_estimado) if self.custo_estimado else None,
            "observacoes":    self.observacoes,
        })
        return base

    @classmethod
    def listar_por_data(cls, tenant_id: str, data: date):
        return cls.query.filter_by(
            tenant_id=tenant_id, data_producao=data
        ).order_by(cls.categoria.asc(), cls.produto.asc()).all()

    @classmethod
    def resumo_periodo(cls, tenant_id: str, data_inicio: date, data_fim: date):
        """Retorna totais agrupados por produto no período."""
        from sqlalchemy import func
        from app.extensions import db as _db
        return _db.session.query(
            cls.produto,
            cls.categoria,
            cls.unidade,
            func.sum(cls.quantidade).label("total_quantidade"),
            func.sum(cls.custo_estimado).label("total_custo"),
        ).filter(
            cls.tenant_id == tenant_id,
            cls.data_producao >= data_inicio,
            cls.data_producao <= data_fim,
        ).group_by(cls.produto, cls.categoria, cls.unidade).all()
