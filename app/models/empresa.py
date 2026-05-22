from app import db


class Empresa(db.Model):
    __tablename__ = "empresas"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(150), nullable=False)

    ativa = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, server_default=db.func.now())

    usuarios = db.relationship("Usuario", backref="empresa", lazy=True)