import os
import time
from functools import wraps

import psycopg
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "lab07-cambie-esta-clave"),
    DATABASE_URL=os.environ.get(
        "DATABASE_URL", "postgresql://lab07:lab07-db-password@localhost:5432/lab07"
    ),
    BACKEND_ID=os.environ.get("BACKEND_ID", "backend-local"),
)


def get_db():
    if "db" not in g:
        g.db = psycopg.connect(app.config["DATABASE_URL"], row_factory=dict_row)
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    last_error = None
    for _ in range(30):
        try:
            with psycopg.connect(app.config["DATABASE_URL"], autocommit=True) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGSERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS tasks (
                        id BIGSERIAL PRIMARY KEY,
                        title VARCHAR(160) NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        completed BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO NOTHING
                    """,
                    ("admin", generate_password_hash("admin123")),
                )
            return
        except psycopg.OperationalError as error:
            last_error = error
            time.sleep(1)
    raise RuntimeError("No fue posible inicializar PostgreSQL") from last_error


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


@app.before_request
def load_user():
    g.user = session.get("username")


@app.after_request
def identify_backend(response):
    response.headers["X-Backend-Server"] = app.config["BACKEND_ID"]
    return response


@app.context_processor
def template_context():
    return {"backend_id": app.config["BACKEND_ID"]}


@app.get("/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone()
    except psycopg.Error:
        return jsonify(status="unhealthy", backend=app.config["BACKEND_ID"]), 503
    return jsonify(status="healthy", backend=app.config["BACKEND_ID"])


@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Usuario o contrasena incorrectos.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            target = request.args.get("next")
            return redirect(target if target and target.startswith("/") else url_for("tasks"))

    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def tasks():
    rows = get_db().execute(
        """
        SELECT id, title, description, completed, created_at, updated_at
        FROM tasks
        ORDER BY id DESC
        """
    ).fetchall()
    completed_count = sum(1 for task in rows if task["completed"])
    stats = {
        "total": len(rows),
        "completed": completed_count,
        "pending": len(rows) - completed_count,
        "progress": round((completed_count / len(rows)) * 100) if rows else 0,
    }
    return render_template("tasks.html", tasks=rows, stats=stats)


@app.route("/tasks/new", methods=("GET", "POST"))
@login_required
def create_task():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("El titulo es obligatorio.", "error")
        else:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO tasks (title, description) VALUES (%s, %s)",
                    (title, description),
                )
            flash("Tarea creada correctamente.", "success")
            return redirect(url_for("tasks"))
    return render_template("task_form.html", task=None)


def find_task(task_id):
    task = get_db().execute(
        "SELECT id, title, description, completed FROM tasks WHERE id = %s",
        (task_id,),
    ).fetchone()
    if task is None:
        abort(404)
    return task


@app.route("/tasks/<int:task_id>/edit", methods=("GET", "POST"))
@login_required
def edit_task(task_id):
    task = find_task(task_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        completed = request.form.get("completed") == "on"
        if not title:
            flash("El titulo es obligatorio.", "error")
        else:
            with get_db() as conn:
                conn.execute(
                    """
                    UPDATE tasks
                    SET title = %s, description = %s, completed = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (title, description, completed, task_id),
                )
            flash("Tarea actualizada correctamente.", "success")
            return redirect(url_for("tasks"))
    return render_template("task_form.html", task=task)


@app.post("/tasks/<int:task_id>/delete")
@login_required
def delete_task(task_id):
    find_task(task_id)
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    flash("Tarea eliminada correctamente.", "success")
    return redirect(url_for("tasks"))


if os.environ.get("SKIP_DB_INIT") != "1":
    init_db()
