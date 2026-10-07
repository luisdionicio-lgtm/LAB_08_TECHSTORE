import os
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg
import jwt
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "techstore-cambie-esta-clave"),
    DATABASE_URL=os.environ.get("DATABASE_URL", "postgresql://lab07:lab07-db-password@localhost:5432/lab07"),
    BACKEND_ID=os.environ.get("BACKEND_ID", "backend-local"),
    JWT_SECRET=os.environ.get("JWT_SECRET", "techstore-jwt-cambie-esta-clave-de-32-caracteres"),
    GITHUB_CLIENT_ID=os.environ.get("GITHUB_CLIENT_ID", ""),
    GITHUB_CLIENT_SECRET=os.environ.get("GITHUB_CLIENT_SECRET", ""),
    GITHUB_REDIRECT_URI=os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:8080/auth/github/callback"),
    GITHUB_DEFAULT_STORE=os.environ.get("GITHUB_DEFAULT_STORE", "TechStore Lima Centro"),
    GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID", ""),
    GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    GOOGLE_REDIRECT_URI=os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/google/callback"),
    GOOGLE_DEFAULT_STORE=os.environ.get("GOOGLE_DEFAULT_STORE", "TechStore Lima Centro"),
)

LOCKOUT_MINUTES = 1
MAX_LOGIN_ATTEMPTS = 3

DEMO_PRODUCTS = (
    ("TS-GAM-407", "PC Gamer Nebula RTX 4070", "Computadoras", "TechStore Build", 4, 3, "6299.00", "Equipo gamer con Ryzen 7, GeForce RTX 4070, 32 GB DDR5 y SSD NVMe de 1 TB."),
    ("TS-NBK-001", "Laptop Lenovo IdeaPad Slim 3", "Computadoras", "Lenovo", 18, 6, "2499.90", "Ryzen 5, 16 GB RAM y SSD de 512 GB para productividad diaria."),
    ("TS-MON-014", "Monitor LG UltraGear 27", "Monitores", "LG", 7, 8, "1299.00", "Panel IPS QHD de 165 Hz orientado a diseño, gaming y contenido."),
    ("TS-RED-008", "Router TP-Link Archer AX55", "Redes", "TP-Link", 24, 7, "389.90", "Router Wi-Fi 6 de doble banda para hogares y oficinas pequeñas."),
    ("TS-ACC-021", "Teclado Logitech MX Keys S", "Accesorios", "Logitech", 5, 5, "449.00", "Teclado inalámbrico multidispositivo con iluminación inteligente."),
    ("TS-ALM-033", "SSD Kingston NV2 1 TB", "Almacenamiento", "Kingston", 0, 10, "259.90", "Unidad NVMe PCIe 4.0 para ampliación de equipos compatibles."),
    ("TS-MOV-005", "Samsung Galaxy A55 5G", "Móviles", "Samsung", 13, 4, "1499.00", "Smartphone 5G con pantalla Super AMOLED y cámara estabilizada."),
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
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGSERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        full_name VARCHAR(160),
                        email VARCHAR(180),
                        store_name VARCHAR(120) NOT NULL DEFAULT 'TechStore Lima Centro',
                        role VARCHAR(40) NOT NULL DEFAULT 'EMPLEADO',
                        github_id VARCHAR(80),
                        google_id VARCHAR(255),
                        failed_attempts INTEGER NOT NULL DEFAULT 0,
                        locked_until TIMESTAMPTZ
                    );
                    CREATE TABLE IF NOT EXISTS products (
                        id BIGSERIAL PRIMARY KEY,
                        sku VARCHAR(40) UNIQUE NOT NULL,
                        name VARCHAR(160) NOT NULL,
                        category VARCHAR(80) NOT NULL,
                        brand VARCHAR(80) NOT NULL,
                        stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                        min_stock INTEGER NOT NULL DEFAULT 0 CHECK (min_stock >= 0),
                        price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
                        description TEXT NOT NULL DEFAULT '',
                        active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(160)")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(180)")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS store_name VARCHAR(120) NOT NULL DEFAULT 'TechStore Lima Centro'")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(40) NOT NULL DEFAULT 'EMPLEADO'")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS github_id VARCHAR(80)")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts INTEGER NOT NULL DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ")
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_github_id_unique ON users (github_id) WHERE github_id IS NOT NULL")
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_google_id_unique ON users (google_id) WHERE google_id IS NOT NULL")
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, full_name, email, store_name, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        store_name = EXCLUDED.store_name,
                        role = EXCLUDED.role
                    """,
                    ("admin", generate_password_hash("admin123"), "Administrador TechStore", "admin@techstore.local", "TechStore Lima Centro", "ADMINISTRADOR"),
                )
                with conn.cursor() as cursor:
                    cursor.executemany("""
                        INSERT INTO products
                            (sku, name, category, brand, stock, min_stock, price, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (sku) DO NOTHING
                    """, DEMO_PRODUCTS)
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
        token = request.cookies.get("techstore_access_token")
        try:
            payload = jwt.decode(
                token or "",
                app.config["JWT_SECRET"],
                algorithms=["HS256"],
                audience="techstore-web",
                issuer="techstore-local",
            )
            if int(payload["sub"]) != session["user_id"]:
                raise jwt.InvalidTokenError("El usuario del token no coincide")
        except (jwt.InvalidTokenError, KeyError, ValueError):
            session.clear()
            flash("Tu token JWT venció o no es válido. Inicia sesión nuevamente.", "error")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view

@app.before_request
def load_user():
    g.user = session.get("username")
    g.store_name = session.get("store_name")
    g.auth_provider = session.get("auth_provider")

@app.after_request
def identify_backend(response):
    response.headers["X-Backend-Server"] = app.config["BACKEND_ID"]
    return response

@app.context_processor
def template_context():
    return {
        "backend_id": app.config["BACKEND_ID"],
        "github_enabled": bool(app.config["GITHUB_CLIENT_ID"] and app.config["GITHUB_CLIENT_SECRET"]),
        "google_enabled": bool(app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"]),
    }

def issue_internal_jwt(user, provider):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user["id"]),
            "username": user["username"],
            "role": user["role"],
            "store": user["store_name"],
            "auth_provider": provider,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "iss": "techstore-local",
            "aud": "techstore-web",
        },
        app.config["JWT_SECRET"],
        algorithm="HS256",
    )

def complete_login(user, provider):
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user.get("full_name") or user["username"]
    session["store_name"] = user["store_name"]
    session["role"] = user["role"]
    session["auth_provider"] = provider
    token = issue_internal_jwt(user, provider)
    response = redirect(url_for("inventory"))
    response.set_cookie(
        "techstore_access_token",
        token,
        max_age=3600,
        httponly=True,
        samesite="Lax",
        secure=False,
    )
    return response

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
        user = get_db().execute("""
            SELECT id, username, password_hash, full_name, email, store_name, role,
                   failed_attempts, locked_until
            FROM users WHERE lower(username) = lower(%s) OR lower(email) = lower(%s)
        """, (username, username)).fetchone()
        now = datetime.now(timezone.utc)
        if user and user["locked_until"] and user["locked_until"] > now:
            remaining = max(1, int((user["locked_until"] - now).total_seconds() // 60) + 1)
            flash(f"Cuenta bloqueada. Intenta nuevamente en {remaining} minutos.", "error")
        elif user is None or not check_password_hash(user["password_hash"], password):
            if user:
                with get_db() as conn:
                    attempt_state = conn.execute("""
                        UPDATE users
                        SET failed_attempts = CASE
                                WHEN locked_until IS NOT NULL AND locked_until <= NOW() THEN 1
                                ELSE failed_attempts + 1
                            END,
                            locked_until = CASE
                                WHEN (CASE
                                    WHEN locked_until IS NOT NULL AND locked_until <= NOW() THEN 1
                                    ELSE failed_attempts + 1
                                END) >= %s
                                THEN NOW() + (%s * INTERVAL '1 minute')
                                ELSE NULL
                            END
                        WHERE id = %s
                        RETURNING failed_attempts, locked_until
                    """, (MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, user["id"])).fetchone()
                attempts = attempt_state["failed_attempts"]
                locked_until = attempt_state["locked_until"]
                if locked_until:
                    flash("Cuenta bloqueada durante 1 minuto por tres intentos fallidos.", "error")
                else:
                    flash(f"Credenciales incorrectas. Quedan {MAX_LOGIN_ATTEMPTS - attempts} intentos.", "error")
            else:
                flash("Credenciales incorrectas.", "error")
        else:
            with get_db() as conn:
                conn.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s", (user["id"],))
            return complete_login(user, "basic")
    return render_template("login.html")

def github_request(url, data=None, token=None):
    headers = {"Accept": "application/json", "User-Agent": "TechStore-Lab07"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    body = urlencode(data).encode() if data else None
    with urlopen(Request(url, data=body, headers=headers), timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

@app.get("/auth/github")
def github_login():
    if not app.config["GITHUB_CLIENT_ID"] or not app.config["GITHUB_CLIENT_SECRET"]:
        flash("GitHub todavía no está configurado. Agrega Client ID y Client Secret en el archivo .env.", "error")
        return redirect(url_for("login"))
    state = secrets.token_urlsafe(32)
    session["github_oauth_state"] = state
    params = urlencode({
        "client_id": app.config["GITHUB_CLIENT_ID"],
        "redirect_uri": app.config["GITHUB_REDIRECT_URI"],
        "scope": "read:user user:email",
        "state": state,
        "allow_signup": "true",
    })
    return redirect(f"https://github.com/login/oauth/authorize?{params}")

@app.get("/auth/github/callback")
def github_callback():
    if not secrets.compare_digest(request.args.get("state", ""), session.pop("github_oauth_state", "")):
        flash("La validación de seguridad de GitHub no coincide. Inicia el acceso nuevamente.", "error")
        return redirect(url_for("login"))
    code = request.args.get("code")
    if not code:
        flash("GitHub no devolvió un código de autorización.", "error")
        return redirect(url_for("login"))
    try:
        token_data = github_request(
            "https://github.com/login/oauth/access_token",
            {
                "client_id": app.config["GITHUB_CLIENT_ID"],
                "client_secret": app.config["GITHUB_CLIENT_SECRET"],
                "code": code,
                "redirect_uri": app.config["GITHUB_REDIRECT_URI"],
            },
        )
        github_token = token_data.get("access_token")
        if not github_token:
            raise ValueError(token_data.get("error_description", "GitHub no entregó un token"))
        profile = github_request("https://api.github.com/user", token=github_token)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        app.logger.warning("GitHub OAuth falló: %s", error)
        flash("No fue posible completar el acceso con GitHub. Verifica la configuración OAuth.", "error")
        return redirect(url_for("login"))

    github_id = str(profile["id"])
    username = f"github_{profile['login']}"
    email = profile.get("email") or f"{profile['login']}@users.noreply.github.com"
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE github_id = %s", (github_id,)).fetchone()
        if user is None:
            user = conn.execute("""
                INSERT INTO users
                    (username, password_hash, full_name, email, store_name, role, github_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                username,
                generate_password_hash(secrets.token_urlsafe(32)),
                profile.get("name") or profile["login"],
                email,
                app.config["GITHUB_DEFAULT_STORE"],
                "EMPLEADO",
                github_id,
            )).fetchone()
        else:
            user = conn.execute("""
                UPDATE users SET full_name = %s, email = %s, username = %s,
                    failed_attempts = 0, locked_until = NULL
                WHERE id = %s RETURNING *
            """, (profile.get("name") or profile["login"], email, username, user["id"])).fetchone()
    return complete_login(user, "github")

def google_request(url, data=None, token=None):
    headers = {"Accept": "application/json", "User-Agent": "TechStore-Lab08"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = urlencode(data).encode() if data else None
    with urlopen(Request(url, data=body, headers=headers), timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

@app.get("/auth/google")
def google_login():
    if not app.config["GOOGLE_CLIENT_ID"] or not app.config["GOOGLE_CLIENT_SECRET"]:
        flash("Google todavía no está configurado. Agrega Client ID y Client Secret en el archivo .env.", "error")
        return redirect(url_for("login"))
    state = secrets.token_urlsafe(32)
    session["google_oauth_state"] = state
    params = urlencode({
        "client_id": app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": app.config["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")

@app.get("/auth/google/callback")
def google_callback():
    expected_state = session.pop("google_oauth_state", "")
    if not expected_state or not secrets.compare_digest(request.args.get("state", ""), expected_state):
        flash("La validación de seguridad de Google no coincide. Inicia el acceso nuevamente.", "error")
        return redirect(url_for("login"))
    code = request.args.get("code")
    if not code:
        flash("Google no devolvió un código de autorización.", "error")
        return redirect(url_for("login"))
    try:
        token_data = google_request(
            "https://oauth2.googleapis.com/token",
            {
                "client_id": app.config["GOOGLE_CLIENT_ID"],
                "client_secret": app.config["GOOGLE_CLIENT_SECRET"],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": app.config["GOOGLE_REDIRECT_URI"],
            },
        )
        google_token = token_data.get("access_token")
        if not google_token:
            raise ValueError(token_data.get("error_description", "Google no entregó un token"))
        profile = google_request("https://openidconnect.googleapis.com/v1/userinfo", token=google_token)
        if not profile.get("email_verified"):
            raise ValueError("La cuenta de Google no tiene un correo verificado")
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        app.logger.warning("Google OAuth falló: %s", error)
        flash("No fue posible completar el acceso con Google. Verifica la configuración OAuth.", "error")
        return redirect(url_for("login"))

    google_id = str(profile["sub"])
    username = f"google_{google_id}"
    email = profile.get("email") or f"{google_id}@google.local"
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE google_id = %s", (google_id,)).fetchone()
        if user is None:
            user = conn.execute("""
                INSERT INTO users
                    (username, password_hash, full_name, email, store_name, role, google_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                username,
                generate_password_hash(secrets.token_urlsafe(32)),
                profile.get("name") or email,
                email,
                app.config["GOOGLE_DEFAULT_STORE"],
                "EMPLEADO",
                google_id,
            )).fetchone()
        else:
            user = conn.execute("""
                UPDATE users SET full_name = %s, email = %s,
                    failed_attempts = 0, locked_until = NULL
                WHERE id = %s RETURNING *
            """, (profile.get("name") or email, email, user["id"])).fetchone()
    return complete_login(user, "google")

@app.post("/logout")
def logout():
    session.clear()
    response = redirect(url_for("login"))
    response.delete_cookie("techstore_access_token")
    return response

def product_state(product):
    if not product["active"]:
        return "inactive"
    if product["stock"] == 0:
        return "out"
    if product["stock"] <= product["min_stock"]:
        return "low"
    return "healthy"

@app.get("/")
@login_required
def inventory():
    products = get_db().execute("""
        SELECT id, sku, name, category, brand, stock, min_stock, price,
               description, active, created_at, updated_at
        FROM products
        ORDER BY active DESC, stock ASC, name ASC
    """).fetchall()
    for product in products:
        product["state"] = product_state(product)
    active_products = [product for product in products if product["active"]]
    stats = {
        "products": len(active_products),
        "units": sum(product["stock"] for product in active_products),
        "alerts": sum(product["state"] in ("low", "out") for product in active_products),
        "value": sum(product["stock"] * product["price"] for product in active_products),
    }
    categories = sorted({product["category"] for product in active_products})
    return render_template("tasks.html", products=products, stats=stats, categories=categories)

def parse_product_form():
    values = {
        "sku": request.form.get("sku", "").strip().upper(),
        "name": request.form.get("name", "").strip(),
        "category": request.form.get("category", "").strip(),
        "brand": request.form.get("brand", "").strip(),
        "description": request.form.get("description", "").strip(),
        "active": request.form.get("active") == "on",
    }
    try:
        values["stock"] = int(request.form.get("stock", "0"))
        values["min_stock"] = int(request.form.get("min_stock", "0"))
        values["price"] = Decimal(request.form.get("price", "0"))
    except (ValueError, InvalidOperation):
        return values, "Stock, stock mínimo y precio deben ser valores numéricos válidos."
    if any(not values[field] for field in ("sku", "name", "category", "brand")):
        return values, "Completa el SKU, nombre, categoría y marca."
    if values["stock"] < 0 or values["min_stock"] < 0 or values["price"] < 0:
        return values, "Los valores numéricos no pueden ser negativos."
    return values, None

@app.route("/products/new", methods=("GET", "POST"))
@login_required
def create_product():
    product = None
    if request.method == "POST":
        product, error = parse_product_form()
        if error:
            flash(error, "error")
        else:
            try:
                with get_db() as conn:
                    conn.execute("""
                        INSERT INTO products
                            (sku, name, category, brand, stock, min_stock, price, description, active)
                        VALUES (%(sku)s, %(name)s, %(category)s, %(brand)s, %(stock)s,
                                %(min_stock)s, %(price)s, %(description)s, %(active)s)
                    """, product)
                flash("Producto registrado correctamente.", "success")
                return redirect(url_for("inventory"))
            except psycopg.errors.UniqueViolation:
                flash("El SKU ya está registrado. Usa un código diferente.", "error")
    return render_template("task_form.html", product=product)

def find_product(product_id):
    product = get_db().execute("""
        SELECT id, sku, name, category, brand, stock, min_stock, price, description, active
        FROM products WHERE id = %s
    """, (product_id,)).fetchone()
    if product is None:
        abort(404)
    return product

@app.route("/products/<int:product_id>/edit", methods=("GET", "POST"))
@login_required
def edit_product(product_id):
    product = find_product(product_id)
    if request.method == "POST":
        values, error = parse_product_form()
        values["id"] = product_id
        if error:
            product = values
            flash(error, "error")
        else:
            try:
                with get_db() as conn:
                    conn.execute("""
                        UPDATE products
                        SET sku = %(sku)s, name = %(name)s, category = %(category)s,
                            brand = %(brand)s, stock = %(stock)s, min_stock = %(min_stock)s,
                            price = %(price)s, description = %(description)s,
                            active = %(active)s, updated_at = NOW()
                        WHERE id = %(id)s
                    """, values)
                flash("Producto actualizado correctamente.", "success")
                return redirect(url_for("inventory"))
            except psycopg.errors.UniqueViolation:
                flash("El SKU ya pertenece a otro producto.", "error")
    return render_template("task_form.html", product=product)

@app.post("/products/<int:product_id>/delete")
@login_required
def delete_product(product_id):
    find_product(product_id)
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = %s", (product_id,))
    flash("Producto eliminado del inventario.", "success")
    return redirect(url_for("inventory"))

if os.environ.get("SKIP_DB_INIT") != "1":
    init_db()
