import pytest
from datetime import date, timedelta
from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models import Tenant, Usuario, ContaPagar


@pytest.fixture(scope="module")
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="module")
def client_auth(app):
    client = app.test_client()
    with app.app_context():
        tenant = Tenant(nome="Padaria Fin", cnpj="11.111.111/0001-11", email_contato="fin@test.com")
        _db.session.add(tenant)
        _db.session.flush()
        usuario = Usuario(tenant_id=tenant.id, nome="Fin User", email="fin@test.com", perfil="proprietario")
        usuario.definir_senha("Senha@1234")
        _db.session.add(usuario)
        _db.session.commit()

    resp = client.post("/api/auth/login", json={"email": "fin@test.com", "senha": "Senha@1234"})
    token = resp.get_json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers


class TestContasPagar:
    def test_criar_conta(self, client_auth):
        client, headers = client_auth
        resp = client.post("/api/contas", json={
            "descricao": "Aluguel junho",
            "categoria": "aluguel",
            "valor": 2500.00,
            "vencimento": str(date.today() + timedelta(days=10)),
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["ok"] is True
        assert data["data"]["descricao"] == "Aluguel junho"
        assert data["data"]["status"] == "pendente"

    def test_criar_conta_valor_zero(self, client_auth):
        client, headers = client_auth
        resp = client.post("/api/contas", json={
            "descricao": "Conta inválida",
            "categoria": "outro",
            "valor": 0,
            "vencimento": str(date.today()),
        }, headers=headers)
        assert resp.status_code == 400

    def test_listar_contas(self, client_auth):
        client, headers = client_auth
        resp = client.get("/api/contas", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_conta_vencida_automaticamente(self, client_auth):
        client, headers = client_auth
        resp = client.post("/api/contas", json={
            "descricao": "Conta vencida",
            "categoria": "outro",
            "valor": 100.00,
            "vencimento": str(date.today() - timedelta(days=1)),
        }, headers=headers)
        assert resp.status_code == 201
        assert resp.get_json()["data"]["status"] == "vencida"

    def test_marcar_conta_como_paga(self, client_auth):
        client, headers = client_auth
        # Criar conta
        resp = client.post("/api/contas", json={
            "descricao": "Para pagar",
            "categoria": "outro",
            "valor": 150.00,
            "vencimento": str(date.today() + timedelta(days=5)),
        }, headers=headers)
        conta_id = resp.get_json()["data"]["id"]

        # Pagar
        resp2 = client.patch(f"/api/contas/{conta_id}/pagar", json={}, headers=headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["status"] == "paga"

    def test_pagar_conta_ja_paga(self, client_auth):
        client, headers = client_auth
        resp = client.post("/api/contas", json={
            "descricao": "Pagar duas vezes",
            "categoria": "outro",
            "valor": 50.00,
            "vencimento": str(date.today() + timedelta(days=1)),
        }, headers=headers)
        conta_id = resp.get_json()["data"]["id"]
        client.patch(f"/api/contas/{conta_id}/pagar", json={}, headers=headers)
        resp2 = client.patch(f"/api/contas/{conta_id}/pagar", json={}, headers=headers)
        assert resp2.status_code == 422

    def test_conta_nao_encontrada(self, client_auth):
        client, headers = client_auth
        resp = client.get("/api/contas/id-inexistente-00000", headers=headers)
        assert resp.status_code == 404
