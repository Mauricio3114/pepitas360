from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models.usuario import Usuario
    from app.models.empresa import Empresa
    from app.models.compromisso import Compromisso
    from app.models.movimentacao_financeira import MovimentacaoFinanceira

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.compromissos import compromissos_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.financeiro import financeiro_bp
    from app.routes.comprovantes import comprovantes_bp
    from app.routes.relatorios import relatorios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(compromissos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(financeiro_bp)
    app.register_blueprint(comprovantes_bp)
    app.register_blueprint(relatorios_bp)

    from datetime import date, timedelta
    from app.models.compromisso import Compromisso
    from flask_login import current_user

    @app.context_processor
    def alertas_globais():

        total_alertas = 0

        try:

            if current_user.is_authenticated:

                hoje = date.today()
                limite = hoje + timedelta(days=3)

                total_alertas = Compromisso.query.filter(
                    Compromisso.empresa_id == current_user.empresa_id,
                    Compromisso.status != "pago",
                    Compromisso.data_vencimento <= limite
                ).count()

        except:
            total_alertas = 0

        return dict(
            alertas_menu=total_alertas
        )

    return app