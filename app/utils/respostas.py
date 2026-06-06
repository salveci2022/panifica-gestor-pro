from flask import jsonify


def sucesso(data=None, message: str = "OK", code: int = 200, meta: dict = None):
    """Resposta de sucesso padronizada."""
    body = {"ok": True, "message": message}
    if data is not None:
        body["data"] = data
    if meta:
        body["meta"] = meta
    return jsonify(body), code


def criado(data=None, message: str = "Criado com sucesso."):
    return sucesso(data=data, message=message, code=201)


def sem_conteudo():
    return "", 204


def erro(message: str, code: int = 400, detalhes=None):
    """Resposta de erro padronizada."""
    body = {"ok": False, "error": message, "code": code}
    if detalhes:
        body["detalhes"] = detalhes
    return jsonify(body), code


def nao_encontrado(recurso: str = "Recurso"):
    return erro(f"{recurso} não encontrado.", 404)


def nao_autorizado(message: str = "Não autenticado."):
    return erro(message, 401)


def proibido(message: str = "Acesso negado."):
    return erro(message, 403)


def conflito(message: str):
    return erro(message, 409)


def regra_negocio(message: str):
    """Erro de regra de negócio — HTTP 422."""
    return erro(message, 422)


def paginado(itens, paginacao, serializar_fn):
    """Resposta paginada com metadados."""
    return sucesso(
        data=[serializar_fn(i) for i in itens],
        meta={
            "total": paginacao.total,
            "pagina": paginacao.page,
            "por_pagina": paginacao.per_page,
            "total_paginas": paginacao.pages,
            "tem_proxima": paginacao.has_next,
            "tem_anterior": paginacao.has_prev,
        }
    )


def validacao_erro(erros: dict):
    """Erros de validação do Marshmallow."""
    return erro("Dados inválidos. Verifique os campos.", 400, detalhes=erros)
