from app.extensions import db
from app.models.base import ModeloBase


class Faturamento(ModeloBase):
    """Receita diária lançada manualmente pelo operador."""
    __tablename__ = "faturamentos"

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    criado_por_id = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=True)

    data = db.Column(db.Date, nullable=False, index=True)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    descricao = db.Column(db.String(200), nullable=True)

    # Relacionamentos
    tenant = db.relationship("Tenant", back_populates="faturamentos")
    criado_por = db.relationship("Usuario", foreign_keys=[criado_por_id])

    def __repr__(self):
        return f"<Faturamento {self.data} R${self.valor}>"

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "tenant_id": self.tenant_id,
            "criado_por_id": self.criado_por_id,
            "data": self.data.isoformat() if self.data else None,
            "valor": float(self.valor),
            "descricao": self.descricao,
        })
        return base

    @classmethod
    def total_do_dia(cls, tenant_id: str, data) -> float:
        from sqlalchemy import func
        resultado = db.session.query(func.sum(cls.valor)).filter(
            cls.tenant_id == tenant_id,
            cls.data == data,
        ).scalar()
        return float(resultado or 0)

    @classmethod
    def total_do_mes(cls, tenant_id: str, ano: int, mes: int) -> float:
        from sqlalchemy import func, extract
        resultado = db.session.query(func.sum(cls.valor)).filter(
            cls.tenant_id == tenant_id,
            extract("year", cls.data) == ano,
            extract("month", cls.data) == mes,
        ).scalar()
        return float(resultado or 0)

    @classmethod
    def fluxo_ultimos_dias(cls, tenant_id: str, dias: int = 7):
        """Retorna lista de {data, total_entradas} dos últimos N dias."""
        from sqlalchemy import func
        from datetime import date, timedelta
        hoje = date.today()
        inicio = hoje - timedelta(days=dias - 1)
        resultados = db.session.query(
            cls.data,
            func.sum(cls.valor).label("total")
        ).filter(
            cls.tenant_id == tenant_id,
            cls.data >= inicio,
            cls.data <= hoje,
        ).group_by(cls.data).order_by(cls.data.asc()).all()

        # Preenche dias sem lançamento com zero
        mapa = {str(r.data): float(r.total) for r in resultados}
        saida = []
        for i in range(dias):
            d = inicio + timedelta(days=i)
            saida.append({"data": str(d), "entradas": mapa.get(str(d), 0.0)})
        return saida
