from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.compromisso import Compromisso

from datetime import date, timedelta


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():

    hoje = date.today()
    limite_alertas = hoje + timedelta(days=3)

    inicio_mes = hoje.replace(day=1)

    if hoje.month == 12:
        fim_mes = hoje.replace(year=hoje.year + 1, month=1, day=1)
    else:
        fim_mes = hoje.replace(month=hoje.month + 1, day=1)

    fim_semana = hoje + timedelta(days=7)

    pagamentos_hoje = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.data_vencimento == hoje,
        Compromisso.status != "pago"
    ).all()

    pagamentos_semana = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.data_vencimento >= hoje,
        Compromisso.data_vencimento <= fim_semana,
        Compromisso.status != "pago"
    ).all()

    pagamentos_mes = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.data_vencimento >= inicio_mes,
        Compromisso.data_vencimento < fim_mes,
        Compromisso.status != "pago"
    ).all()

    vencidos = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.data_vencimento < hoje,
        Compromisso.status != "pago"
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    proximos = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.data_vencimento >= hoje,
        Compromisso.status != "pago"
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).limit(5).all()

    compromissos_alerta = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.status != "pago",
        Compromisso.data_vencimento <= limite_alertas
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    alertas = []

    for item in compromissos_alerta:

        dias = (item.data_vencimento - hoje).days

        if dias < 0:
            nivel = "vencido"
            icone = "❌"
            mensagem = "está vencido"

        elif dias == 0:
            nivel = "urgente"
            icone = "🔴"
            mensagem = "vence hoje"

        elif dias == 1:
            nivel = "alto"
            icone = "🟠"
            mensagem = "vence amanhã"

        elif dias == 2:
            nivel = "medio"
            icone = "🟡"
            mensagem = "vence em 2 dias"

        else:
            nivel = "medio"
            icone = "🟡"
            mensagem = "vence em 3 dias"

        alertas.append({
            "nivel": nivel,
            "icone": icone,
            "titulo": item.titulo,
            "mensagem": mensagem,
            "data": item.data_vencimento,
            "tipo": item.tipo,
            "valor": item.valor
        })

    total_hoje = sum(item.valor for item in pagamentos_hoje)
    total_semana = sum(item.valor for item in pagamentos_semana)
    total_mes = sum(item.valor for item in pagamentos_mes)

    return render_template(
        "dashboard/index.html",
        usuario=current_user,
        total_hoje=total_hoje,
        total_semana=total_semana,
        total_mes=total_mes,
        vencidos=vencidos,
        proximos=proximos,
        alertas=alertas
    )