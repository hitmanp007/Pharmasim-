import logging, os, secrets
from flask import Flask, render_template, request, session, abort
from . import models


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    env = os.environ.get("PHARMASIM_ENV", "production")
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE=os.environ.get("DATABASE_PATH") or os.path.join(app.instance_path, "pharmasim.db"),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(env == "production"),
    )
    if config:
        app.config.update(config)
    if not app.config["SECRET_KEY"]:
        if env == "development":
            app.config["SECRET_KEY"] = secrets.token_hex(16)
        else:
            raise RuntimeError("SECRET_KEY environment variable must be set in production.")
    logging.basicConfig(level=logging.INFO)
    models.init_db(app.config["DATABASE"])
    app.teardown_appcontext(models.close_db)

    @app.before_request
    def _guard():
        session.setdefault("sid", secrets.token_hex(16))
        session.setdefault("csrf", secrets.token_hex(16))
        if request.method == "POST" and not secrets.compare_digest(
                request.form.get("csrf_token", ""), session["csrf"]):
            abort(400)

    @app.context_processor
    def _ctx():
        return {"csrf_token": session.get("csrf", "")}

    for code, msg in ((400, "The request was invalid or expired. Go back and try again."),
                      (404, "That page or scenario does not exist."),
                      (500, "Something went wrong on our side.")):
        app.register_error_handler(code, lambda e, c=code, m=msg: (render_template("errors/error.html", code=c, message=m), c))

    from .routes import bp
    app.register_blueprint(bp)
    return app
