from functools import wraps
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.compromisso import Compromisso


comprovantes_bp = Blueprint(
    "comprovantes",
    __name__,
    url_prefix="/comprovantes"
)


def requer_comprovantes(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not current_user.pode_acessar("comprovantes"):

            flash(
                "Você não possui acesso aos comprovantes.",
                "danger"
            )

            return redirect(url_for("dashboard.index"))

        return func(*args, **kwargs)

    return wrapper


@comprovantes_bp.route("/")
@login_required
@requer_comprovantes
def index():

    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")
    tipo_filtro = request.args.get("tipo") or ""

    query = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.comprovante.isnot(None)
    )

    if data_inicio_str:

        data_inicio = datetime.strptime(
            data_inicio_str,
            "%Y-%m-%d"
        ).date()

        query = query.filter(
            Compromisso.data_vencimento >= data_inicio
        )

    if data_fim_str:

        data_fim = datetime.strptime(
            data_fim_str,
            "%Y-%m-%d"
        ).date()

        query = query.filter(
            Compromisso.data_vencimento <= data_fim
        )

    if tipo_filtro:

        query = query.filter(
            Compromisso.tipo == tipo_filtro
        )

    comprovantes = query.order_by(
        Compromisso.data_vencimento.desc()
    ).all()

    return render_template(
        "comprovantes/index.html",
        comprovantes=comprovantes,
        tipo_filtro=tipo_filtro,
        data_inicio=data_inicio_str,
        data_fim=data_fim_str
    )