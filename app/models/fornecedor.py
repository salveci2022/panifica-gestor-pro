from app.extensions import db
from app.models.base import ModeloBase

CATEGORIAS_FORNECEDOR = (
    "insumos", "laticinios", "embalagem", "servicos",
    "concessionaria", "manutencao", "outro"
)


class Fornecedor(ModeloBase):
    __tablename__ = "fornecedores"

    tenant_id    = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    nome         = db.Column(db.String(120), nullable=False)
    cnpj_cpf     = db.Column(db.String(18), nullable=True)
    categoria    = db.Column(db.String(60), nullable=False, default="outro")
    telefone     = db.Column(db.String(20), nullable=True)
    whatsapp     = db.Column(db.String(20), nullable=True)
    email        = db.Column(db.String(180), nullable=True)
    contato_nome = db.Column(db.String(80), nullable=True)
    endereco     = db.Column(db.Text, nullable=True)
    observacoes  = db.Column(db.Text, nullable=True)
    ativo        = db.Column(db.Boolean, default=True, nullable=False)

    tenant      = db.relationship("Tenant", back_populates="fornecedores")
    contas_pagar= db.relationship("ContaPagar", back_populates="fornecedor", lazy="dynamic")
    compras     = db.relationship("Compra",     back_populates="fornecedor", lazy="dynamic")

    def __repr__(self):
        return f"<Fornecedor {self.nome}>"

    def desativar(self) -> None:
        self.ativo = False

    def para_dict(self, incluir_totais: bool = False):
        base = super().para_dict()
        base.update({
            "tenant_id":    self.tenant_id,
            "nome":         self.nome,
            "cnpj_cpf":     self.cnpj_cpf,
            "categoria":    self.categoria,
            "telefone":     self.telefone,
            "whatsapp":     self.whatsapp,
            "email":        self.email,
            "contato_nome": self.contato_nome,
            "endereco":     self.endereco,
            "observacoes":  self.observacoes,
            "ativo":        self.ativo,
        })
        if incluir_totais:
            # [FIX B1] Import direto em vez de __import__ frágil
            base["total_contas_abertas"] = self._total_contas_abertas()
        return base

    def _total_contas_abertas(self) -> float:
        """[FIX B1] Import correto dentro do método para evitar circular import."""
        from app.models.conta_pagar import ContaPagar
        from sqlalchemy import func
        resultado = db.session.query(func.sum(ContaPagar.valor)).filter(
            ContaPagar.fornecedor_id == self.id,
            ContaPagar.status.in_(["pendente", "vencida"])
        ).scalar()
        return float(resultado or 0)

    @classmethod
    def listar_por_tenant(cls, tenant_id: str, apenas_ativos: bool = True, busca: str = None):
        q = cls.query.filter_by(tenant_id=tenant_id)
        if apenas_ativos:
            q = q.filter_by(ativo=True)
        if busca:
            q = q.filter(cls.nome.ilike(f"%{busca}%"))
        return q.order_by(cls.nome.asc()).all()

    @classmethod
    def buscar_por_tenant_e_id(cls, tenant_id: str, fornecedor_id: str):
        return cls.query.filter_by(tenant_id=tenant_id, id=fornecedor_id).first()
