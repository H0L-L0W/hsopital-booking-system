import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # Basic config - can be overridden by environment variables
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///hospital_saas.db"
    )
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
        # Render uses postgres://; SQLAlchemy expects postgresql://
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config[
            "SQLALCHEMY_DATABASE_URI"
        ].replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Email / notification config placeholders
    app.config["MAIL_SENDER"] = os.environ.get("MAIL_SENDER", "no-reply@example.com")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    from . import models  # noqa: F401
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .patient.routes import patient_bp
    from .doctor.routes import doctor_bp
    from .staff.routes import staff_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(patient_bp, url_prefix="/patient")
    app.register_blueprint(doctor_bp, url_prefix="/doctor")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app

