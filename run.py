from app import create_app
from app.extensions import db
from app.models import Tenant, Usuario, Fornecedor, ContaPagar, Faturamento, AuditLog

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Disponibiliza modelos no flask shell para testes rápidos."""
    return {
        "db": db,
        "Tenant": Tenant,
        "Usuario": Usuario,
        "Fornecedor": Fornecedor,
        "ContaPagar": ContaPagar,
        "Faturamento": Faturamento,
        "AuditLog": AuditLog,
    }


@app.cli.command("seed")
def seed():
    """Cria dados de demonstração para desenvolvimento."""
    import click

    with app.app_context():
        # Tenant de demonstração
        tenant = Tenant(
            nome="Padaria São João",
            cnpj="12.345.678/0001-90",
            email_contato="joao@padariasaojoao.com.br",
            telefone="(61) 99900-1234",
            plano="pro",
        )
        db.session.add(tenant)
        db.session.flush()

        # Usuário proprietário
        prop = Usuario(
            tenant_id=tenant.id,
            nome="João Silva",
            email="joao@padariasaojoao.com.br",
            perfil="proprietario",
        )
        prop.definir_senha("Senha@1234")
        db.session.add(prop)

        # Usuário operador
        oper = Usuario(
            tenant_id=tenant.id,
            nome="Maria Caixa",
            email="maria@padariasaojoao.com.br",
            perfil="operador",
        )
        oper.definir_senha("Senha@1234")
        db.session.add(oper)

        # Fornecedores
        fornecedores = [
            Fornecedor(tenant_id=tenant.id, nome="Dist. Farinha Norte", categoria="insumos",
                       telefone="(61) 99901-1234", email="contato@farinha.com.br"),
            Fornecedor(tenant_id=tenant.id, nome="Laticínios Vale", categoria="laticinios",
                       whatsapp="(61) 98802-5566", email="vendas@laticiniosvale.com"),
            Fornecedor(tenant_id=tenant.id, nome="Neoenergia", categoria="concessionaria",
                       telefone="0800 722 1000"),
        ]
        for f in fornecedores:
            db.session.add(f)

        db.session.commit()
        click.echo("✅ Seed criado! Login: joao@padariasaojoao.com.br / Senha@1234")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


@app.cli.command("setup_producao")
def setup_producao():
    """Cria tenant e usuário inicial em produção."""
    from app.models.tenant import Tenant
    from app.models.usuario import Usuario
    from app.extensions import db

    with app.app_context():
        db.create_all()

        # Verificar se já existe
        existente = Usuario.query.filter_by(email="joao@padariasaojoao.com.br").first()
        if existente:
            print("Usuário já existe!")
            return

        t = Tenant.query.first()
        if not t:
            t = Tenant(
                nome="Padaria Sao Joao",
                cnpj="12.345.678/0001-90",
                email_contato="joao@padariasaojoao.com.br"
            )
            db.session.add(t)
            db.session.flush()

        u = Usuario(
            tenant_id=t.id,
            nome="Joao Silva",
            email="joao@padariasaojoao.com.br",
            perfil="proprietario"
        )
        u.definir_senha("Senha@1234")
        db.session.add(u)
        db.session.commit()
        print(f"Usuário criado: joao@padariasaojoao.com.br / Senha@1234")
