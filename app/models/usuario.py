from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    perfil = db.Column(db.String(50), default="visualizador")
    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, server_default=db.func.now())

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def is_master(self):
        return self.perfil == "master"

    def is_admin(self):
        return self.perfil == "admin"

    def pode_acessar(self, modulo):
        if self.perfil in ["master", "admin"]:
            return True

        permissoes = {
            "financeiro": ["financeiro"],
            "pagamentos": ["financeiro"],
            "relatorios": ["financeiro"],
            "agenda": ["agenda"],
            "usuarios": [],
            "comprovantes": ["financeiro"],
            "visualizar": ["visualizador", "financeiro", "agenda"],
        }

        return self.perfil in permissoes.get(modulo, [])