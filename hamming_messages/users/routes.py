from flask import (
    Flask,
    render_template,
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import current_user, login_required, login_user, logout_user
from hamming_messages import db
from hamming_messages.models import User
from hamming_messages.users.forms import (
    SigninForm,
    SignupForm,
    RequestResetForm,
    ResetPasswordForm,
)

users = Blueprint("users", __name__)


@users.route("/welcome")
def welcome():
    """Render welcome page."""
    if current_user.is_authenticated:
        redirect(url_for("main.home"))
    return render_template("welcome.pug")


@users.route("/signin", methods=["GET", "POST"])
def signin():
    """Render signin page."""
    if current_user.is_authenticated:
        redirect(url_for("main.home"))
    form = SigninForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            user.is_online = True
            login_user(user, remember=form.remember.data)
            db.session.commit()
            return redirect(url_for("main.home"))
    context = {
        "title": "Sign In",
        "form": form,
    }
    return render_template("signin.pug", **context)


@users.route("/signup", methods=["GET", "POST"])
def signup():
    """Render signup page."""
    if current_user.is_authenticated:
        redirect(url_for("main.home"))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("main.home"))
    context = {
        "title": "Sign Up",
        "form": form,
    }
    return render_template("signup.pug", **context)


@users.route("/signout")
@login_required
def logout():
    """Sign out current user and redirect to welcome."""
    user = User.query.get_or_404(current_user.id)
    user.is_online = False
    db.session.commit()
    logout_user()
    return redirect(url_for("users.welcome"))


@users.route("/update", methods=["PATCH"])
@login_required
def update_account():
    """Update user's account info and save to database."""
    username = request.json.get("username")
    email = request.json.get("email")
    if username and email:
        user = User.query.get_or_404(current_user.id)
        user.username = username
        user.email = email
        db.session.commit()
        return ({"username": user.username, "email": user.email}), 201
    return (""), 404


@users.route("/user", methods=["GET"])
@login_required
def get_user():
    """Get user info for current user."""
    user = User.query.get_or_404(current_user.id)
    return (
        {"id": user.id, "username": user.username, "email": user.email}
    ), 200


@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    """Show route for requesting user password reset."""
    if current_user.is_authenticated:
        redirect(url_for("main.home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        user.send_reset_email()
        flash("An email has been sent to reset your password.")
        return redirect(url_for("users.signin"))
    context = {"form": form}
    return render_template("reset_request.pug", **context)


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    """Show route for resetting user password."""
    if current_user.is_authenticated:
        redirect(url_for("main.home"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("The token is invalid or expired.")
        return redirect(url_for("users.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been updated! You are now able to sign in.")
        return redirect(url_for("users.signin"))
    context = {"form": form}
    return render_template("reset_token.pug", **context)
