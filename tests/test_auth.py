import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models import Tenant, Usuario


@pytest.fixture(scope="session")
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def tenant_e_usuario(app):
    with app.app_context():
        tenant = Tenant(
            nome="Padaria Teste",
            cnpj="00.000.000/0001-00",
            email_contato="teste@padaria.com",
        )
        _db.session.add(tenant)
        _db.session.flush()

        usuario = Usuario(
            tenant_id=tenant.id,
            nome="Teste Proprietário",
            email="proprietario@padaria.com",
            perfil="proprietario",
        )
        usuario.definir_senha("SenhaForte@123")
        _db.session.add(usuario)
        _db.session.commit()

        yield {"tenant": tenant, "usuario": usuario}

        _db.session.query(Usuario).delete()
        _db.session.query(Tenant).delete()
        _db.session.commit()


class TestLogin:
    def test_login_sucesso(self, client, tenant_e_usuario):
        resp = client.post("/api/auth/login", json={
            "email": "proprietario@padaria.com",
            "senha": "SenhaForte@123"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_login_senha_errada(self, client, tenant_e_usuario):
        resp = client.post("/api/auth/login", json={
            "email": "proprietario@padaria.com",
            "senha": "senhaerrada"
        })
        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_login_email_inexistente(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "naoexiste@email.com",
            "senha": "qualquercoisa"
        })
        assert resp.status_code == 401

    def test_login_dados_ausentes(self, client):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 400

    def test_login_email_invalido(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "naoemail",
            "senha": "qualquer"
        })
        assert resp.status_code == 400


class TestMe:
    def _obter_token(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "proprietario@padaria.com",
            "senha": "SenhaForte@123"
        })
        return resp.get_json()["data"]["access_token"]

    def test_me_autenticado(self, client, tenant_e_usuario):
        token = self._obter_token(client)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["data"]["usuario"]["email"] == "proprietario@padaria.com"

    def test_me_sem_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
