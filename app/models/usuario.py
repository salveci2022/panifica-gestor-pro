import secrets
from datetime import datetime, timezone, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.extensions import db
from app.models.base import ModeloBase, agora_utc

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

PERFIS_VALIDOS = ("proprietario", "operador", "visualizador")


class Usuario(ModeloBase):
    """Usuário de um tenant com controle de perfil (RBAC)."""
    __tablename__ = "usuarios"

    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.Text, nullable=False)
    perfil = db.Column(db.String(20), default="operador", nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    ultimo_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Campos para recuperação de senha
    token_reset = db.Column(db.Text, nullable=True)
    token_expira = db.Column(db.DateTime(timezone=True), nullable=True)

    # Campos para controle de tentativas de login
    tentativas_login = db.Column(db.Integer, default=0, nullable=False)
    bloqueado_ate = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relacionamentos
    tenant = db.relationship("Tenant", back_populates="usuarios")

    def __repr__(self):
        return f"<Usuario {self.email} [{self.perfil}]>"

    # ─── Senha ───────────────────────────────────────────────────────────────

    def definir_senha(self, senha_plana: str) -> None:
        """Gera hash Argon2id e armazena."""
        if len(senha_plana) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        self.senha_hash = _ph.hash(senha_plana)

    def verificar_senha(self, senha_plana: str) -> bool:
        """Retorna True se a senha for válida."""
        try:
            return _ph.verify(self.senha_hash, senha_plana)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def senha_precisa_rehash(self) -> bool:
        return _ph.check_needs_rehash(self.senha_hash)

    # ─── Bloqueio por tentativas ──────────────────────────────────────────────

    def esta_bloqueado(self) -> bool:
        if self.bloqueado_ate and self.bloqueado_ate > agora_utc():
            return True
        return False

    def registrar_tentativa_falha(self, max_tentativas: int = 5, minutos_bloqueio: int = 15) -> None:
        self.tentativas_login = (self.tentativas_login or 0) + 1
        if self.tentativas_login >= max_tentativas:
            self.bloqueado_ate = agora_utc() + timedelta(minutes=minutos_bloqueio)
            self.tentativas_login = 0

    def resetar_tentativas(self) -> None:
        self.tentativas_login = 0
        self.bloqueado_ate = None

    def registrar_login(self) -> None:
        self.ultimo_login = agora_utc()
        self.resetar_tentativas()

    # ─── Token de recuperação de senha ───────────────────────────────────────

    def gerar_token_reset(self, horas_expiracao: int = 2) -> str:
        token = secrets.token_urlsafe(48)
        self.token_reset = token
        self.token_expira = agora_utc() + timedelta(hours=horas_expiracao)
        return token

    def token_reset_valido(self) -> bool:
        if not self.token_reset or not self.token_expira:
            return False
        return self.token_expira > agora_utc()

    def limpar_token_reset(self) -> None:
        self.token_reset = None
        self.token_expira = None

    # ─── Serialização ─────────────────────────────────────────────────────────

    def para_dict(self, incluir_sensiveis: bool = False):
        base = super().para_dict()
        base.update({
            "tenant_id": self.tenant_id,
            "nome": self.nome,
            "email": self.email,
            "perfil": self.perfil,
            "ativo": self.ativo,
            "ultimo_login": self.ultimo_login.isoformat() if self.ultimo_login else None,
        })
        if incluir_sensiveis:
            base["esta_bloqueado"] = self.esta_bloqueado()
            base["tentativas_login"] = self.tentativas_login
        return base

    # ─── Queries ──────────────────────────────────────────────────────────────

    @classmethod
    def buscar_por_email(cls, email: str):
        return cls.query.filter_by(email=email.lower().strip()).first()

    @classmethod
    def buscar_por_tenant(cls, tenant_id: str):
        return cls.query.filter_by(tenant_id=tenant_id, ativo=True).all()
