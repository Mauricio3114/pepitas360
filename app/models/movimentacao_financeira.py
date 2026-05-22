from app import db
from datetime import datetime


class MovimentacaoFinanceira(db.Model):
    __tablename__ = "movimentacoes_financeiras"

    id = db.Column(db.Integer, primary_key=True)

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    tipo = db.Column(db.String(20), nullable=False)  # entrada ou saida
    descricao = db.Column(db.String(180), nullable=False)
    categoria = db.Column(db.String(80), nullable=True)

    valor = db.Column(db.Float, nullable=False, default=0.0)
    data_movimentacao = db.Column(db.Date, nullable=False)

    observacao = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", backref="movimentacoes_financeiras")
    empresa = db.relationship("Empresa", backref="movimentacoes_financeiras")