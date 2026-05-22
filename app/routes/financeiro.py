from functools import wraps
from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.movimentacao_financeira import MovimentacaoFinanceira


financeiro_bp = Blueprint(
    "financeiro",
    __name__,
    url_prefix="/financeiro"
)


def requer_financeiro(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.pode_acessar("financeiro"):
            flash("Você não possui permissão para acessar o financeiro.", "danger")
            return redirect(url_for("dashboard.index"))

        return func(*args, **kwargs)

    return wrapper


def buscar_movimentacao_da_empresa(movimentacao_id):
    return MovimentacaoFinanceira.query.filter_by(
        id=movimentacao_id,
        empresa_id=current_user.empresa_id
    ).first_or_404()


def calcular_resumo(movimentacoes):
    total_entradas = sum(
        item.valor for item in movimentacoes
        if item.tipo == "entrada"
    )

    total_saidas = sum(
        item.valor for item in movimentacoes
        if item.tipo == "saida"
    )

    saldo = total_entradas - total_saidas

    return total_entradas, total_saidas, saldo


@financeiro_bp.route("/")
@login_required
@requer_financeiro
def index():

    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")
    tipo_filtro = request.args.get("tipo") or ""
    categoria_filtro = request.args.get("categoria") or ""

    if data_inicio_str:
        data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
    else:
        data_inicio = inicio_mes

    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
    else:
        data_fim = hoje

    query = MovimentacaoFinanceira.query.filter(
        MovimentacaoFinanceira.empresa_id == current_user.empresa_id,
        MovimentacaoFinanceira.data_movimentacao >= data_inicio,
        MovimentacaoFinanceira.data_movimentacao <= data_fim
    )

    if tipo_filtro:
        query = query.filter(
            MovimentacaoFinanceira.tipo == tipo_filtro
        )

    if categoria_filtro:
        query = query.filter(
            MovimentacaoFinanceira.categoria == categoria_filtro
        )

    movimentacoes = query.order_by(
        MovimentacaoFinanceira.data_movimentacao.desc()
    ).all()

    total_entradas, total_saidas, saldo_mes = calcular_resumo(
        movimentacoes
    )

    categorias = [
        "vendas",
        "servicos",
        "fornecedor",
        "salario",
        "aluguel",
        "energia",
        "internet",
        "impostos",
        "outros"
    ]

    return render_template(
        "financeiro/index.html",
        movimentacoes=movimentacoes,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo_mes=saldo_mes,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo_filtro=tipo_filtro,
        categoria_filtro=categoria_filtro,
        categorias=categorias
    )


@financeiro_bp.route("/novo", methods=["GET", "POST"])
@login_required
@requer_financeiro
def novo():

    if request.method == "POST":

        movimentacao = MovimentacaoFinanceira(
            empresa_id=current_user.empresa_id,
            usuario_id=current_user.id,
            tipo=request.form.get("tipo"),
            descricao=request.form.get("descricao"),
            categoria=request.form.get("categoria"),
            valor=float(request.form.get("valor") or 0),
            data_movimentacao=datetime.strptime(
                request.form.get("data_movimentacao"),
                "%Y-%m-%d"
            ).date(),
            observacao=request.form.get("observacao")
        )

        db.session.add(movimentacao)
        db.session.commit()

        flash("Movimentação cadastrada com sucesso!", "success")

        return redirect(url_for("financeiro.index"))

    return render_template("financeiro/form.html")


@financeiro_bp.route("/editar/<int:movimentacao_id>", methods=["GET", "POST"])
@login_required
@requer_financeiro
def editar(movimentacao_id):

    movimentacao = buscar_movimentacao_da_empresa(movimentacao_id)

    if request.method == "POST":

        movimentacao.tipo = request.form.get("tipo")
        movimentacao.descricao = request.form.get("descricao")
        movimentacao.categoria = request.form.get("categoria")
        movimentacao.valor = float(request.form.get("valor") or 0)
        movimentacao.data_movimentacao = datetime.strptime(
            request.form.get("data_movimentacao"),
            "%Y-%m-%d"
        ).date()
        movimentacao.observacao = request.form.get("observacao")

        db.session.commit()

        flash("Movimentação atualizada com sucesso!", "success")

        return redirect(url_for("financeiro.index"))

    return render_template(
        "financeiro/form.html",
        movimentacao=movimentacao
    )


@financeiro_bp.route("/excluir/<int:movimentacao_id>")
@login_required
@requer_financeiro
def excluir(movimentacao_id):

    movimentacao = buscar_movimentacao_da_empresa(movimentacao_id)

    db.session.delete(movimentacao)
    db.session.commit()

    flash("Movimentação excluída com sucesso!", "success")

    return redirect(url_for("financeiro.index"))