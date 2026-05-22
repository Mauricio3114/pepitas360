import os
import calendar
from uuid import uuid4
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.compromisso import Compromisso

from datetime import datetime, date


compromissos_bp = Blueprint(
    "compromissos",
    __name__,
    url_prefix="/compromissos"
)


TIPOS_PAGAMENTO = [
    "pagamento",
    "boleto",
    "transferencia",
    "dinheiro"
]

TIPOS_AGENDA = [
    "reuniao",
    "evento"
]

EXTENSOES_PERMITIDAS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp"
}


def requer_permissao(modulo):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if not current_user.pode_acessar(modulo):

                flash(
                    "Você não possui permissão para acessar este módulo.",
                    "danger"
                )

                return redirect(url_for("dashboard.index"))

            return func(*args, **kwargs)

        return wrapper

    return decorator


def buscar_compromisso_da_empresa(compromisso_id):
    return Compromisso.query.filter_by(
        id=compromisso_id,
        empresa_id=current_user.empresa_id
    ).first_or_404()


def destino_por_tipo(tipo):

    if tipo in TIPOS_AGENDA:
        return "compromissos.agenda"

    return "compromissos.pagamentos"


def modulo_por_tipo(tipo):

    if tipo in TIPOS_AGENDA:
        return "agenda"

    return "pagamentos"


def extensao_permitida(nome_arquivo):

    return (
        "." in nome_arquivo
        and nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS
    )


def salvar_comprovante(arquivo):

    if not arquivo or arquivo.filename == "":
        return None

    if not extensao_permitida(arquivo.filename):

        flash(
            "Formato de comprovante inválido. Use PDF, PNG, JPG, JPEG ou WEBP.",
            "warning"
        )

        return None

    pasta_upload = os.path.join(
        os.getcwd(),
        "static",
        "uploads",
        "comprovantes"
    )

    os.makedirs(pasta_upload, exist_ok=True)

    nome_original = secure_filename(arquivo.filename)
    extensao = nome_original.rsplit(".", 1)[1].lower()
    nome_final = f"{uuid4().hex}.{extensao}"

    caminho_final = os.path.join(
        pasta_upload,
        nome_final
    )

    arquivo.save(caminho_final)

    return f"uploads/comprovantes/{nome_final}"


@compromissos_bp.route("/")
@login_required
def listar():

    compromissos = Compromisso.query.filter_by(
        empresa_id=current_user.empresa_id
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    return render_template(
        "compromissos/listar.html",
        compromissos=compromissos
    )


@compromissos_bp.route("/agenda")
@login_required
@requer_permissao("agenda")
def agenda():

    compromissos = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.tipo.in_(TIPOS_AGENDA)
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    return render_template(
        "compromissos/agenda.html",
        compromissos=compromissos
    )


@compromissos_bp.route("/pagamentos")
@login_required
@requer_permissao("pagamentos")
def pagamentos():

    compromissos = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.tipo.in_(TIPOS_PAGAMENTO)
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    return render_template(
        "compromissos/pagamentos.html",
        compromissos=compromissos
    )


@compromissos_bp.route("/calendario")
@login_required
def calendario():

    if not (
        current_user.pode_acessar("agenda")
        or current_user.pode_acessar("pagamentos")
    ):

        flash(
            "Você não possui permissão para acessar o calendário.",
            "danger"
        )

        return redirect(url_for("dashboard.index"))

    hoje = date.today()

    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year

    if mes < 1:
        mes = 12
        ano -= 1

    if mes > 12:
        mes = 1
        ano += 1

    primeiro_dia = date(ano, mes, 1)

    ultimo_dia_numero = calendar.monthrange(ano, mes)[1]
    ultimo_dia = date(ano, mes, ultimo_dia_numero)

    compromissos = Compromisso.query.filter(
        Compromisso.empresa_id == current_user.empresa_id,
        Compromisso.data_vencimento >= primeiro_dia,
        Compromisso.data_vencimento <= ultimo_dia
    ).order_by(
        Compromisso.data_vencimento.asc()
    ).all()

    compromissos_por_dia = {}

    for item in compromissos:
        dia = item.data_vencimento.day

        if dia not in compromissos_por_dia:
            compromissos_por_dia[dia] = []

        compromissos_por_dia[dia].append(item)

    calendario_mes = calendar.monthcalendar(ano, mes)

    nomes_meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro"
    }

    return render_template(
        "compromissos/calendario.html",
        calendario_mes=calendario_mes,
        compromissos_por_dia=compromissos_por_dia,
        mes=mes,
        ano=ano,
        nome_mes=nomes_meses[mes],
        hoje=hoje
    )


@compromissos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():

    if request.method == "POST":

        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")
        tipo = request.form.get("tipo")
        forma_pagamento = request.form.get("forma_pagamento")
        valor = request.form.get("valor") or 0
        data_vencimento = request.form.get("data_vencimento")
        observacao = request.form.get("observacao")

        modulo = modulo_por_tipo(tipo)

        if not current_user.pode_acessar(modulo):

            flash(
                "Você não possui permissão para cadastrar neste módulo.",
                "danger"
            )

            return redirect(url_for("dashboard.index"))

        arquivo_comprovante = request.files.get("comprovante")

        comprovante_salvo = salvar_comprovante(
            arquivo_comprovante
        )

        compromisso = Compromisso(
            empresa_id=current_user.empresa_id,
            usuario_id=current_user.id,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            forma_pagamento=forma_pagamento,
            valor=float(valor),
            data_vencimento=datetime.strptime(
                data_vencimento,
                "%Y-%m-%d"
            ).date(),
            observacao=observacao,
            comprovante=comprovante_salvo,
            status="pendente"
        )

        db.session.add(compromisso)
        db.session.commit()

        flash(
            "Compromisso cadastrado com sucesso!",
            "success"
        )

        return redirect(
            url_for(destino_por_tipo(tipo))
        )

    return render_template(
        "compromissos/novo.html"
    )


@compromissos_bp.route("/editar/<int:compromisso_id>", methods=["GET", "POST"])
@login_required
def editar(compromisso_id):

    compromisso = buscar_compromisso_da_empresa(
        compromisso_id
    )

    modulo = modulo_por_tipo(
        compromisso.tipo
    )

    if not current_user.pode_acessar(modulo):

        flash(
            "Você não possui permissão para editar este módulo.",
            "danger"
        )

        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        compromisso.titulo = request.form.get("titulo")
        compromisso.descricao = request.form.get("descricao")
        compromisso.tipo = request.form.get("tipo")
        compromisso.forma_pagamento = request.form.get("forma_pagamento")
        compromisso.valor = float(
            request.form.get("valor") or 0
        )

        compromisso.data_vencimento = datetime.strptime(
            request.form.get("data_vencimento"),
            "%Y-%m-%d"
        ).date()

        compromisso.status = request.form.get("status")
        compromisso.observacao = request.form.get("observacao")

        arquivo_comprovante = request.files.get(
            "comprovante"
        )

        novo_comprovante = salvar_comprovante(
            arquivo_comprovante
        )

        if novo_comprovante:
            compromisso.comprovante = novo_comprovante

        db.session.commit()

        flash(
            "Compromisso atualizado com sucesso!",
            "success"
        )

        return redirect(
            url_for(destino_por_tipo(compromisso.tipo))
        )

    return render_template(
        "compromissos/novo.html",
        compromisso=compromisso
    )


@compromissos_bp.route("/pagar/<int:compromisso_id>")
@login_required
@requer_permissao("pagamentos")
def pagar(compromisso_id):

    compromisso = buscar_compromisso_da_empresa(
        compromisso_id
    )

    compromisso.status = "pago"

    db.session.commit()

    flash(
        "Compromisso marcado como pago!",
        "success"
    )

    return redirect(
        url_for(destino_por_tipo(compromisso.tipo))
    )


@compromissos_bp.route("/pendente/<int:compromisso_id>")
@login_required
@requer_permissao("pagamentos")
def pendente(compromisso_id):

    compromisso = buscar_compromisso_da_empresa(
        compromisso_id
    )

    compromisso.status = "pendente"

    db.session.commit()

    flash(
        "Compromisso marcado como pendente!",
        "warning"
    )

    return redirect(
        url_for(destino_por_tipo(compromisso.tipo))
    )


@compromissos_bp.route("/excluir/<int:compromisso_id>")
@login_required
def excluir(compromisso_id):

    compromisso = buscar_compromisso_da_empresa(
        compromisso_id
    )

    modulo = modulo_por_tipo(
        compromisso.tipo
    )

    if not current_user.pode_acessar(modulo):

        flash(
            "Você não possui permissão para excluir neste módulo.",
            "danger"
        )

        return redirect(
            url_for("dashboard.index")
        )

    destino = destino_por_tipo(
        compromisso.tipo
    )

    db.session.delete(compromisso)
    db.session.commit()

    flash(
        "Compromisso excluído com sucesso!",
        "success"
    )

    return redirect(
        url_for(destino)
    )