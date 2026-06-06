import uuid
from datetime import datetime, timezone
from app.extensions import db


def gerar_uuid():
    return str(uuid.uuid4())


def agora_utc():
    return datetime.now(timezone.utc)


class ModeloBase(db.Model):
    """Classe base abstrata com id UUID e timestamps."""
    __abstract__ = True

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=gerar_uuid,
        nullable=False,
    )
    criado_em = db.Column(
        db.DateTime(timezone=True),
        default=agora_utc,
        nullable=False,
    )
    atualizado_em = db.Column(
        db.DateTime(timezone=True),
        default=agora_utc,
        onupdate=agora_utc,
        nullable=False,
    )

    def para_dict(self):
        """Converte o modelo para dicionário. Sobrescrever nas subclasses."""
        return {
            "id": self.id,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }

    def salvar(self):
        db.session.add(self)
        db.session.commit()
        return self

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, id_):
        return cls.query.filter_by(id=id_).first()
