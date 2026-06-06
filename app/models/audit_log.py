import json
import uuid
from datetime import datetime, timezone
from app.extensions import db


def _gerar_uuid():
    return str(uuid.uuid4())


def _agora_utc():
    return datetime.now(timezone.utc)


class AuditLog(db.Model):
    """
    Log de auditoria imutável.
    [FIX BUG-001] Usa UUID string como PK (consistente com outros modelos)
    para garantir que o id seja gerado ANTES do INSERT, sem depender de
    autoincrement do banco — funciona em SQLite e PostgreSQL.
    """
    __tablename__ = "audit_logs"

    id          = db.Column(db.String(36), primary_key=True, default=_gerar_uuid, nullable=False)
    tenant_id   = db.Column(db.String(36), nullable=False, index=True)
    usuario_id  = db.Column(db.String(36), nullable=True)
    tabela      = db.Column(db.String(60), nullable=False)
    operacao    = db.Column(db.String(10), nullable=False)   # INSERT | UPDATE | DELETE
    registro_id = db.Column(db.String(36), nullable=True)    # nullable para casos onde id ainda não existe
    dados_antes = db.Column(db.Text, nullable=True)
    dados_depois= db.Column(db.Text, nullable=True)
    ip_origem   = db.Column(db.String(45), nullable=True)
    user_agent  = db.Column(db.Text, nullable=True)
    criado_em   = db.Column(db.DateTime(timezone=True), default=_agora_utc, nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.operacao} {self.tabela}:{self.registro_id}>"

    @classmethod
    def registrar(
        cls,
        tenant_id: str,
        tabela: str,
        operacao: str,
        registro_id: str,
        dados_antes=None,
        dados_depois=None,
        usuario_id: str = None,
        ip_origem: str = None,
        user_agent: str = None,
    ):
        """
        Cria registro de auditoria.
        O UUID do log é gerado pelo Python (default=_gerar_uuid),
        garantindo id não-nulo antes do INSERT.
        """
        log = cls(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            tabela=tabela,
            operacao=operacao,
            registro_id=registro_id,
            dados_antes=json.dumps(dados_antes, default=str) if dados_antes else None,
            dados_depois=json.dumps(dados_depois, default=str) if dados_depois else None,
            ip_origem=ip_origem,
            user_agent=user_agent,
        )
        db.session.add(log)
        # Não comitar aqui — a transação pai cuida do commit
        return log
