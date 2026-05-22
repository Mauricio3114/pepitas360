from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.usuario import Usuario


usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios"
)


def somente_admin(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not current_user.pode_acessar("usuarios"):
            flash("Você não possui permissão para acessar usuários.", "danger")
            return redirect(url_for("dashboard.index"))

        return func(*args, **kwargs)

    return wrapper


def buscar_usuario_da_empresa(usuario_id):

    return Usuario.query.filter_by(
        id=usuario_id,
        empresa_id=current_user.empresa_id
    ).first_or_404()


@usuarios_bp.route("/")
@login_required
@somente_admin
def listar():

    usuarios = Usuario.query.filter_by(
        empresa_id=current_user.empresa_id
    ).order_by(
        Usuario.nome.asc()
    ).all()

    return render_template(
        "usuarios/listar.html",
        usuarios=usuarios
    )


@usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@somente_admin
def novo():

    if request.method == "POST":

        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        perfil = request.form.get("perfil")
        ativo = True if request.form.get("ativo") == "on" else False

        usuario_existente = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario_existente:
            flash("Já existe um usuário com este e-mail.", "warning")
            return redirect(url_for("usuarios.novo"))

        usuario = Usuario(
            empresa_id=current_user.empresa_id,
            nome=nome,
            email=email,
            perfil=perfil,
            ativo=ativo
        )

        usuario.set_senha(senha)

        db.session.add(usuario)
        db.session.commit()

        flash("Usuário cadastrado com sucesso!", "success")

        return redirect(url_for("usuarios.listar"))

    return render_template("usuarios/form.html")


@usuarios_bp.route("/editar/<int:usuario_id>", methods=["GET", "POST"])
@login_required
@somente_admin
def editar(usuario_id):

    usuario = buscar_usuario_da_empresa(usuario_id)

    if request.method == "POST":

        usuario.nome = request.form.get("nome")
        usuario.email = request.form.get("email")
        usuario.perfil = request.form.get("perfil")
        usuario.ativo = True if request.form.get("ativo") == "on" else False

        nova_senha = request.form.get("senha")

        if nova_senha:
            usuario.set_senha(nova_senha)

        db.session.commit()

        flash("Usuário atualizado com sucesso!", "success")

        return redirect(url_for("usuarios.listar"))

    return render_template(
        "usuarios/form.html",
        usuario=usuario
    )


@usuarios_bp.route("/alternar-status/<int:usuario_id>")
@login_required
@somente_admin
def alternar_status(usuario_id):

    usuario = buscar_usuario_da_empresa(usuario_id)

    if usuario.id == current_user.id:
        flash("Você não pode desativar seu próprio usuário.", "warning")
        return redirect(url_for("usuarios.listar"))

    usuario.ativo = not usuario.ativo

    db.session.commit()

    flash("Status do usuário alterado com sucesso!", "success")

    return redirect(url_for("usuarios.listar"))