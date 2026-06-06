from datetime import date
from app.extensions import db
from app.models.base import ModeloBase, agora_utc

CATEGORIAS_VALIDAS = (
    "aluguel", "energia", "agua", "telefone", "internet",
    "folha_pagamento", "fornecedor", "imposto", "manutencao", "outro"
)

FORMAS_PAGAMENTO = (
    "pix", "boleto", "cartao_debito", "cartao_credito",
    "dinheiro", "transferencia", "cheque"
)

STATUS_VALIDOS = ("pendente", "paga", "vencida", "cancelada")


class ContaPagar(ModeloBase):
    __tablename__ = "contas_pagar"

    tenant_id      = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    fornecedor_id  = db.Column(db.String(36), db.ForeignKey("fornecedores.id"), nullable=True)
    loja_id        = db.Column(db.String(36), db.ForeignKey("lojas.id"), nullable=True, index=True)
    loja_id        = db.Column(db.String(36), db.ForeignKey("lojas.id"), nullable=True, index=True)
    numero_pedido  = db.Column(db.String(40), nullable=True)
    criado_por_id  = db.Column(db.String(36), db.ForeignKey("usuarios.id"), nullable=True)

    descricao      = db.Column(db.String(200), nullable=False)
    categoria      = db.Column(db.String(60), nullable=False, default="outro")
    valor          = db.Column(db.Numeric(12, 2), nullable=False)
    vencimento     = db.Column(db.Date, nullable=False, index=True)
    forma_pagamento= db.Column(db.String(30), nullable=True)
    status         = db.Column(db.String(20), default="pendente", nullable=False, index=True)
    data_pagamento = db.Column(db.Date, nullable=True)
    valor_pago     = db.Column(db.Numeric(12, 2), nullable=True)
    numero_pedido  = db.Column(db.String(40), nullable=True)
    observacoes    = db.Column(db.Text, nullable=True)

    tenant      = db.relationship("Tenant", back_populates="contas_pagar")
    fornecedor  = db.relationship("Fornecedor", back_populates="contas_pagar")
    loja        = db.relationship("Loja",       back_populates="contas_pagar")
    criado_por  = db.relationship("Usuario", foreign_keys=[criado_por_id])
    loja        = db.relationship("Loja", back_populates="contas_pagar", foreign_keys=[loja_id])

    def __repr__(self):
        return f"<ContaPagar {self.descricao} R${self.valor} [{self.status}]>"

    # ─── Lógica de negócio ─────────────────────────────────────────────────────

    def esta_vencida(self) -> bool:
        return self.status == "pendente" and self.vencimento < date.today()

    def marcar_como_paga(self, valor_pago=None, data_pgto=None) -> None:
        if self.status == "cancelada":
            raise ValueError("Não é possível pagar uma conta cancelada.")
        if self.status == "paga":
            raise ValueError("Esta conta já foi marcada como paga.")
        self.status = "paga"
        self.data_pagamento = data_pgto or date.today()
        self.valor_pago = valor_pago or self.valor
        self.atualizado_em = agora_utc()

    def cancelar(self) -> None:
        if self.status == "paga":
            raise ValueError("Não é possível cancelar uma conta já paga.")
        self.status = "cancelada"
        self.atualizado_em = agora_utc()

    def atualizar_status_vencimento(self) -> bool:
        """Atualiza status para 'vencida' se prazo expirou. NÃO comita."""
        if self.status == "pendente" and self.vencimento < date.today():
            self.status = "vencida"
            return True
        return False

    # ─── Serialização ──────────────────────────────────────────────────────────

    def para_dict(self):
        base = super().para_dict()
        base.update({
            "tenant_id":       self.tenant_id,
            "fornecedor_id":   self.fornecedor_id,
            "loja_id":         self.loja_id,
            "loja_nome":       self.loja.nome if self.loja else None,
            "loja_codigo":     self.loja.codigo if self.loja else None,
            "loja_id":         self.loja_id,
            "loja_nome":       self.loja.nome if self.loja else None,
            "loja_codigo":     self.loja.codigo if self.loja else None,
            "numero_pedido":   self.numero_pedido,
            "fornecedor_nome": self.fornecedor.nome if self.fornecedor else None,
            "criado_por_id":   self.criado_por_id,
            "descricao":       self.descricao,
            "categoria":       self.categoria,
            "valor":           float(self.valor),
            "vencimento":      self.vencimento.isoformat() if self.vencimento else None,
            "forma_pagamento": self.forma_pagamento,
            "status":          self.status,
            "data_pagamento":  self.data_pagamento.isoformat() if self.data_pagamento else None,
            "valor_pago":      float(self.valor_pago) if self.valor_pago else None,
            "numero_pedido":   self.numero_pedido,
            "observacoes":     self.observacoes,
            "esta_vencida":    self.esta_vencida(),
        })
        return base

    # ─── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def listar_por_tenant(cls, tenant_id: str, status=None, pagina=1, por_pagina=20):
        q = cls.query.filter_by(tenant_id=tenant_id)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(cls.vencimento.asc()).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )

    @classmethod
    def total_pendente(cls, tenant_id: str) -> float:
        from sqlalchemy import func
        resultado = db.session.query(func.sum(cls.valor)).filter(
            cls.tenant_id == tenant_id,
            cls.status.in_(["pendente", "vencida"])
        ).scalar()
        return float(resultado or 0)

    @classmethod
    def total_pago_no_mes(cls, tenant_id: str, ano: int, mes: int) -> float:
        from sqlalchemy import func, extract
        resultado = db.session.query(func.sum(cls.valor_pago)).filter(
            cls.tenant_id == tenant_id,
            cls.status == "paga",
            extract("year", cls.data_pagamento) == ano,
            extract("month", cls.data_pagamento) == mes,
        ).scalar()
        return float(resultado or 0)

    @classmethod
    def atualizar_vencidas(cls, tenant_id: str) -> int:
        """
        [FIX B2] Atualiza status de contas vencidas usando UPDATE direto.
        NÃO faz commit — deixa para a transação chamadora.
        Usa bulk update para performance.
        """
        resultado = db.session.query(cls).filter(
            cls.tenant_id == tenant_id,
            cls.status == "pendente",
            cls.vencimento < date.today(),
        ).update({"status": "vencida"}, synchronize_session="fetch")
        return resultado
