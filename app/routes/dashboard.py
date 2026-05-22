from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.models.compromisso import Compromisso
from app.models.empresa import Empresa

from datetime import date, timedelta


dashboard_bp = Blueprint("dashboard", __name__)


def aplicar_filtro_empresa(query, empresa_id=None):

    if current_user.perfil == "master":

        if empresa_id:
            return query.filter(
                Compromisso.empresa_id == empresa_id
            )

        return query

    return query.filter(
        Compromisso.empresa_id == current_user.empresa_id
    )


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

    empresa_id = request.args.get("empresa_id", type=int)

    empresas = []

    if current_user.perfil == "master":
        empresas = Empresa.query.filter_by(
            ativa=True
        ).order_by(
            Empresa.nome.asc()
        ).all()

    pagamentos_hoje_query = Compromisso.query.filter(
        Compromisso.data_vencimento == hoje,
        Compromisso.status != "pago"
    )

    pagamentos_semana_query = Compromisso.query.filter(
        Compromisso.data_vencimento >= hoje,
        Compromisso.data_vencimento <= fim_semana,
        Compromisso.status != "pago"
    )

    pagamentos_mes_query = Compromisso.query.filter(
        Compromisso.data_vencimento >= inicio_mes,
        Compromisso.data_vencimento < fim_mes,
        Compromisso.status != "pago"
    )

    vencidos_query = Compromisso.query.filter(
        Compromisso.data_vencimento < hoje,
        Compromisso.status != "pago"
    )

    proximos_query = Compromisso.query.filter(
        Compromisso.data_vencimento >= hoje,
        Compromisso.status != "pago"
    )

    alertas_query = Compromisso.query.filter(
        Compromisso.status != "pago",
        Compromisso.data_vencimento <= limite_alertas
    )

    pagamentos_hoje = aplicar_filtro_empresa(
        pagamentos_hoje_query,
        empresa_id
    ).all()

    pagamentos_semana = aplicar_filtro_empresa(
        pagamentos_semana_query,
        empresa_id
    ).all()

    pagamentos_mes = aplicar_filtro_empresa(
        pagamentos_mes_query,
        empresa_id
    ).all()

    vencidos = aplicar_filtro_empresa(
        vencidos_query,
        empresa_id
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    proximos = aplicar_filtro_empresa(
        proximos_query,
        empresa_id
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).limit(5).all()

    compromissos_alerta = aplicar_filtro_empresa(
        alertas_query,
        empresa_id
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
        alertas=alertas,
        empresas=empresas,
        empresa_id=empresa_id
    )