from app import db
from datetime import datetime


class Compromisso(db.Model):
    __tablename__ = "compromissos"

    id = db.Column(db.Integer, primary_key=True)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    tipo = db.Column(db.String(50), nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=True)

    valor = db.Column(db.Float, default=0.0)

    data_vencimento = db.Column(db.Date, nullable=False)
    hora_evento = db.Column(db.Time, nullable=True)

    status = db.Column(db.String(30), default="pendente")

    comprovante = db.Column(db.String(255), nullable=True)
    observacao = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    usuario = db.relationship("Usuario", backref="compromissos")
    empresa = db.relationship("Empresa", backref="compromissos")