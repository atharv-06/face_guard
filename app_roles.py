# app_roles.py
import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from models import db, User, RecognitionLog, Blacklist
from auth import login_manager, UserLogin
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime, timedelta
from functools import wraps
import sqlite3

# optional email config
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

basedir = os.path.abspath(os.path.dirname(__file__))

def create_app(config_obj=None):
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")

    # Ensure database folder exists
    db_folder = os.path.join(basedir, "database")
    os.makedirs(db_folder, exist_ok=True)

    # SQLite DB path
    db_path = os.path.join(db_folder, "app_roles.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"  # correct endpoint for login
    login_manager.login_message_category = "info"

    # Create tables and default admin
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username="admin").first() is None:
            admin = User(username="admin", role="admin")
            admin.set_password("admin123")  # change after first login
            db.session.add(admin)
            db.session.commit()

    # ------------------ Routes ------------------

    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        total = RecognitionLog.query.count()
        recent = RecognitionLog.query.order_by(RecognitionLog.timestamp.desc()).limit(10).all()
        bl_count = Blacklist.query.filter_by(active=True).count()
        return render_template("rb_dashboard.html", total=total, recent=recent, bl_count=bl_count)

    # ---- AUTH ----
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(UserLogin(user))
                flash("Logged in successfully.", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("rb_login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out", "info")
        return redirect(url_for("login"))

    # ---- Admin required decorator ----
    def admin_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("login"))
            u = User.query.get(int(current_user.id))
            if not u or u.role != "admin":
                flash("Admin access required", "warning")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)
        return wrapper

    # ---- User management ----
    @app.route("/admin/users")
    @login_required
    @admin_required
    def users():
        all_users = User.query.order_by(User.created_at.desc()).all()
        return render_template("rb_users.html", users=all_users)

    @app.route("/admin/users/create", methods=["POST"])
    @login_required
    @admin_required
    def create_user():
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "user")
        if not username or not password:
            flash("Username and password required", "danger")
            return redirect(url_for("users"))
        if User.query.filter_by(username=username).first():
            flash("User already exists", "warning")
            return redirect(url_for("users"))
        u = User(username=username, role=role)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash("User created", "success")
        return redirect(url_for("users"))

    @app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
    @login_required
    @admin_required
    def delete_user(user_id):
        if user_id == int(current_user.id):
            flash("You cannot delete yourself", "danger")
            return redirect(url_for("users"))
        u = User.query.get(user_id)
        if u:
            db.session.delete(u)
            db.session.commit()
            flash("User deleted", "success")
        return redirect(url_for("users"))

    # ---- Blacklist ----
    @app.route("/admin/blacklist")
    @login_required
    @admin_required
    def blacklist():
        items = Blacklist.query.order_by(Blacklist.created_at.desc()).all()
        return render_template("rb_blacklist.html", items=items)

    @app.route("/admin/blacklist/add", methods=["POST"])
    @login_required
    @admin_required
    def add_blacklist():
        name = request.form.get("name")
        notes = request.form.get("notes")
        if name:
            b = Blacklist(name=name, notes=notes)
            db.session.add(b)
            db.session.commit()
            flash("Added to blacklist", "success")
        return redirect(url_for("blacklist"))

    @app.route("/admin/blacklist/toggle/<int:id>", methods=["POST"])
    @login_required
    @admin_required
    def toggle_blacklist(id):
        b = Blacklist.query.get(id)
        if b:
            b.active = not b.active
            db.session.commit()
            flash("Updated", "success")
        return redirect(url_for("blacklist"))

    # ---- Logs & Analytics ----
    @app.route("/logs")
    @login_required
    def logs():
        rows = RecognitionLog.query.order_by(RecognitionLog.timestamp.desc()).limit(500).all()
        return render_template("rb_logs.html", logs=rows)

    @app.route("/analytics_data")
    @login_required
    def analytics_data():
        cutoff = datetime.utcnow() - timedelta(days=14)
        rows = db.session.query(RecognitionLog).filter(RecognitionLog.timestamp >= cutoff).all()
        from collections import Counter
        counts = Counter([r.timestamp.date().isoformat() for r in rows])
        labels = sorted(list(counts.keys()))
        values = [counts[d] for d in labels]
        name_counts = Counter([r.name or "Unknown" for r in rows])
        top = name_counts.most_common(10)
        return jsonify({
            "timeline": {"labels": labels, "values": values},
            "top_names": [{"name": n, "count": c} for n,c in top]
        })

    # ---- Alert endpoint ----
    @app.route("/api/alert", methods=["POST"])
    def api_alert():
        data = request.get_json() or {}
        name = data.get("name", "Unknown")
        conf = data.get("confidence", None)
        notes = data.get("notes", "")

        r = RecognitionLog(name=name, confidence=conf or 0.0)
        db.session.add(r)
        db.session.commit()

        b = Blacklist.query.filter(Blacklist.name==name, Blacklist.active==True).first()
        if b or name == "Unknown":
            try:
                send_alert_email(name, conf, notes)
            except Exception as e:
                app.logger.error("Alert email failed: %s", e)

        return jsonify({"ok": True}), 201

    # ---- Email helper ----
    def send_alert_email(name, confidence, notes=""):
        import smtplib
        from email.message import EmailMessage
        if not SMTP_HOST or not ALERT_EMAIL_TO:
            return False
        msg = EmailMessage()
        msg['Subject'] = f"[ALERT] Face detected: {name}"
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_EMAIL_TO
        body = f"Detected: {name}\nConfidence: {confidence}\nNotes: {notes}\nTime: {datetime.utcnow().isoformat()}"
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True

    return app

# ---- Run the app ----
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5010)
