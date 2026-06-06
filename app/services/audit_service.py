import logging
from flask import request
from app.models.audit_log import AuditLog
from app.utils.auth import obter_ip_requisicao, obter_user_agent

logger = logging.getLogger(__name__)


def registrar_auditoria(
    tenant_id: str,
    tabela: str,
    operacao: str,
    registro_id: str,
    dados_antes=None,
    dados_depois=None,
    usuario_id: str = None,
):
    """Grava entrada de auditoria. Não comita — a transação pai comita."""
    try:
        AuditLog.registrar(
            tenant_id=tenant_id,
            tabela=tabela,
            operacao=operacao,
            registro_id=registro_id,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            usuario_id=usuario_id,
            ip_origem=obter_ip_requisicao(),
            user_agent=obter_user_agent(),
        )
    except Exception as exc:
        # Não deixar falha de auditoria quebrar a operação principal
        logger.error("Falha ao registrar auditoria: %s", exc)
