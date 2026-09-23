from __future__ import annotations

import io
import json
import os
import secrets
import sqlite3
import tempfile
from html import escape
import urllib.error
import urllib.request
from calendar import monthrange
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from re import sub
from uuid import uuid4

from flask import Flask, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from gerador_abnt import gerar_documento_abnt

try:
    import stripe
except ImportError:  # O app continua iniciável até a dependência ser instalada.
    stripe = None


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "abnt.sqlite3"))
ALLOWED_EXTENSION = ".docx"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_CONTENT_LENGTH = 35 * 1024 * 1024
PLANS = {
    "basic": {"name": "Básico", "monthly_limit": 5, "price_label": "R$ 14,90/mês", "annual_label": "R$ 149/ano"},
    "pro": {"name": "Pro", "monthly_limit": None, "price_label": "R$ 24,90/mês", "annual_label": "R$ 249/ano"},
}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret"),
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
)


class ValidationError(Exception):
    pass


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'none',
    subscription_status TEXT NOT NULL DEFAULT 'inactive',
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    current_period_end TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS usage (
    user_id INTEGER NOT NULL,
    period TEXT NOT NULL,
    generations INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, period),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS stripe_events (
    event_id TEXT PRIMARY KEY,
    received_at TEXT NOT NULL
);
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.executescript(SCHEMA)
    return g.db


@app.teardown_appcontext
def close_db(exception: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.context_processor
def inject_app_context() -> dict[str, object]:
    user = current_user()
    return {"current_user": user, "plans": PLANS, "csrf_token": csrf_token}


def current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def _enviar_email_resend(destinatario: str, assunto: str, html: str) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    remetente = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    if not api_key:
        app.logger.info("RESEND_API_KEY não configurada; e-mail não enviado.")
        return False
    payload = json.dumps({"from": remetente, "to": [destinatario], "subject": assunto, "html": html}).encode("utf-8")
    requisicao = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=10) as resposta:
            return 200 <= resposta.status < 300
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        app.logger.exception("Falha ao enviar e-mail transacional pelo Resend")
        return False


def csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf() -> None:
    if not secrets.compare_digest(request.form.get("csrf_token", ""), session.get("csrf_token", "")):
        raise ValidationError("Sessão expirada. Atualize a página e tente novamente.")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Crie uma conta ou entre para continuar.", "erro")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def subscription_active(user: sqlite3.Row | None) -> bool:
    if not user:
        return False
    if os.getenv("ALLOW_UNPAID_GENERATION", "0") == "1":
        return True
    return user["subscription_status"] in {"active", "trialing"} and user["plan"] in PLANS


def current_period() -> str:
    now = utc_now()
    return f"{now.year:04d}-{now.month:02d}"


def usage_for(user_id: int) -> int:
    row = get_db().execute("SELECT generations FROM usage WHERE user_id = ? AND period = ?", (user_id, current_period())).fetchone()
    return int(row["generations"]) if row else 0


def check_and_consume_generation(user: sqlite3.Row) -> None:
    if not subscription_active(user):
        raise ValidationError("Escolha um plano e conclua o pagamento para gerar documentos.")
    selected_plan = user["plan"] if user["plan"] in PLANS else "basic"
    limit = PLANS[selected_plan]["monthly_limit"]
    used = usage_for(user["id"])
    if limit is not None and used >= limit:
        raise ValidationError("Você atingiu o limite de 5 documentos deste mês.")
    db = get_db()
    db.execute(
        "INSERT INTO usage(user_id, period, generations) VALUES (?, ?, 1) "
        "ON CONFLICT(user_id, period) DO UPDATE SET generations = generations + 1",
        (user["id"], current_period()),
    )
    db.commit()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            validate_csrf()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if "@" not in email or len(email) > 254:
                raise ValidationError("Informe um e-mail válido.")
            if len(password) < 8:
                raise ValidationError("A senha deve ter pelo menos 8 caracteres.")
            db = get_db()
            db.execute(
                "INSERT INTO users(email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, generate_password_hash(password), utc_now().isoformat()),
            )
            db.commit()
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            session.clear()
            session["user_id"] = user["id"]
            csrf_token()
            _enviar_email_resend(
                email,
                "Sua conta no Conversor ABNT foi criada",
                f"<p>Olá!</p><p>Sua conta no <strong>Conversor ABNT</strong> foi criada com sucesso.</p><p>Agora você pode escolher um plano e gerar seus documentos acadêmicos em Word.</p><p>Se você não criou esta conta, ignore este e-mail.</p><p>E-mail cadastrado: {escape(email)}</p>",
            )
            flash("Conta criada. Agora escolha um plano para ativar as gerações.", "success")
            return redirect(url_for("plans"))
        except sqlite3.IntegrityError:
            flash("Este e-mail já está cadastrado.", "erro")
        except ValidationError as error:
            flash(str(error), "erro")
    return render_template("auth.html", mode="register")


@app.route("/entrar", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            validate_csrf()
            email = request.form.get("email", "").strip().lower()
            user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if not user or not check_password_hash(user["password_hash"], request.form.get("password", "")):
                raise ValidationError("E-mail ou senha incorretos.")
            session.clear()
            session["user_id"] = user["id"]
            csrf_token()
            return redirect(request.args.get("next") or url_for("account"))
        except ValidationError as error:
            flash(str(error), "erro")
    return render_template("auth.html", mode="login")


@app.post("/sair")
def logout():
    validate_csrf()
    session.clear()
    return redirect(url_for("index"))


@app.route("/conta")
@login_required
def account():
    user = current_user()
    used = usage_for(user["id"])
    return render_template("account.html", user=user, used=used, active=subscription_active(user))


@app.route("/planos")
def plans():
    return render_template("plans.html")


@app.post("/checkout/<plan>/<interval>")
@login_required
def checkout(plan: str, interval: str):
    validate_csrf()
    if plan not in PLANS or interval not in {"monthly", "annual"}:
        flash("Plano inválido.", "erro")
        return redirect(url_for("plans"))
    price_id = os.getenv(f"STRIPE_PRICE_{plan.upper()}_{interval.upper()}")
    product_id = os.getenv(f"STRIPE_PRODUCT_{plan.upper()}_{interval.upper()}")
    if not price_id and stripe and os.getenv("STRIPE_SECRET_KEY") and product_id:
        stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
        product = stripe.Product.retrieve(product_id)
        price_id = product.get("default_price")
        if isinstance(price_id, dict):
            price_id = price_id.get("id")
    if not stripe or not os.getenv("STRIPE_SECRET_KEY") or not price_id:
        flash("A cobrança ainda não foi configurada. Siga o checklist de configuração do Stripe.", "erro")
        return redirect(url_for("plans"))
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    user = current_user()
    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=user["email"],
        client_reference_id=str(user["id"]),
        metadata={"user_id": str(user["id"]), "plan": plan},
        subscription_data={"metadata": {"user_id": str(user["id"]), "plan": plan}},
        success_url=url_for("account", _external=True) + "?checkout=success",
        cancel_url=url_for("plans", _external=True) + "?checkout=cancelled",
    )
    return redirect(checkout_session.url, code=303)


@app.post("/portal-stripe")
@login_required
def stripe_portal():
    validate_csrf()
    if not stripe or not os.getenv("STRIPE_SECRET_KEY"):
        flash("O portal de cobrança ainda não foi configurado.", "erro")
        return redirect(url_for("account"))
    user = current_user()
    if not user["stripe_customer_id"]:
        flash("Ainda não há uma assinatura Stripe vinculada a esta conta.", "erro")
        return redirect(url_for("plans"))
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    portal_session = stripe.billing_portal.Session.create(
        customer=user["stripe_customer_id"],
        return_url=url_for("account", _external=True),
    )
    return redirect(portal_session.url, code=303)


@app.post("/stripe/webhook")
def stripe_webhook():
    if not stripe or not os.getenv("STRIPE_WEBHOOK_SECRET"):
        return jsonify(error="Stripe webhook não configurado"), 503
    payload = request.get_data()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, os.environ["STRIPE_WEBHOOK_SECRET"])
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify(error="Webhook inválido"), 400
    db = get_db()
    if db.execute("SELECT 1 FROM stripe_events WHERE event_id = ?", (event["id"],)).fetchone():
        return jsonify(received=True)
    obj = event["data"]["object"]
    event_type = event["type"]
    metadata = obj.get("metadata", {}) or {}
    user_id = metadata.get("user_id") or obj.get("client_reference_id")
    if not user_id and obj.get("subscription"):
        row = db.execute("SELECT id FROM users WHERE stripe_subscription_id = ?", (obj.get("subscription"),)).fetchone()
        user_id = row["id"] if row else None
    if not user_id and obj.get("customer"):
        row = db.execute("SELECT id FROM users WHERE stripe_customer_id = ?", (obj.get("customer"),)).fetchone()
        user_id = row["id"] if row else None
    if user_id:
        if event_type == "checkout.session.completed":
            plan = metadata.get("plan", "")
            subscription_id = obj.get("subscription")
            if plan in PLANS:
                db.execute("UPDATE users SET plan = ?, subscription_status = 'active', stripe_customer_id = ?, stripe_subscription_id = ? WHERE id = ?", (plan, obj.get("customer"), subscription_id, user_id))
        elif event_type in {"customer.subscription.updated", "invoice.paid"}:
            plan = metadata.get("plan")
            if plan in PLANS:
                db.execute("UPDATE users SET plan = ?, subscription_status = 'active', current_period_end = ? WHERE id = ?", (plan, str(obj.get("current_period_end", "")), user_id))
            else:
                db.execute("UPDATE users SET subscription_status = 'active' WHERE id = ?", (user_id,))
        elif event_type in {"customer.subscription.deleted", "invoice.payment_failed"}:
            db.execute("UPDATE users SET subscription_status = 'past_due' WHERE id = ?", (user_id,))
    db.execute("INSERT INTO stripe_events(event_id, received_at) VALUES (?, ?)", (event["id"], utc_now().isoformat()))
    db.commit()
    return jsonify(received=True)


@app.route("/gerar", methods=["POST"])
@login_required
def gerar_documento():
    try:
        validate_csrf()
        user = current_user()
        with tempfile.TemporaryDirectory(prefix="abnt_request_") as pasta_temporaria:
            pasta = Path(pasta_temporaria)
            dados = _coletar_dados_formulario(pasta)
            _validar_dados_obrigatorios(dados)
            check_and_consume_generation(user)
            caminho_saida = pasta / f"{_normalizar_nome_arquivo(dados['titulo']) or 'trabalho_abnt'}_{uuid4().hex[:8]}.docx"
            arquivo_gerado = gerar_documento_abnt(dados, caminho_saida)
            conteudo = arquivo_gerado.read_bytes()
        resposta = send_file(io.BytesIO(conteudo), as_attachment=True, download_name=arquivo_gerado.name, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        resposta.headers["Cache-Control"] = "no-store, private"
        return resposta
    except ValidationError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("index"))
    except Exception:
        app.logger.exception("Falha ao gerar documento ABNT")
        flash("Não foi possível gerar o documento. Revise os dados enviados e tente novamente.", "erro")
        return redirect(url_for("index"))


@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok", "database": "ok"}


def _coletar_dados_formulario(pasta_temporaria: Path) -> dict[str, object]:
    return {
        "autores": _obter_autores_por_campos_numerados(), "instituicao": _obter_texto("instituicao"), "curso_disciplina": _obter_texto("curso_disciplina"), "professor": _obter_texto("professor"), "cidade": _obter_texto("cidade"), "ano": _obter_texto("ano"), "fonte": _obter_texto("fonte") or "Arial", "titulo": _obter_texto("titulo"), "subtitulo": _obter_texto("subtitulo"), "tipo_trabalho": _obter_texto("tipo_trabalho"), "natureza_trabalho": _obter_texto("natureza_trabalho"), "folha_aprovacao": _obter_texto("folha_aprovacao"), "texto_aprovacao": _obter_texto("texto_aprovacao"), "banca_examinadora": _obter_lista("banca_examinadora"), "dedicatoria": _obter_texto("dedicatoria"), "agradecimentos": _obter_texto("agradecimentos"), "epigrafe": _obter_texto("epigrafe"), "resumo": _obter_texto("resumo"), "palavras_chave": _obter_lista("palavras_chave"), "abstract": _obter_texto("abstract"), "keywords": _obter_lista("keywords"), "secoes_textuais": _obter_secoes_por_campos_numerados(pasta_temporaria), "referencias": _obter_lista("referencias"), "glossario": _obter_texto("glossario"), "apendice": _obter_texto("apendice"), "anexo": _obter_texto("anexo"), "indice": _obter_texto("indice")}


def _validar_dados_obrigatorios(dados: dict[str, object]) -> None:
    for chave, rotulo in {"instituicao": "Instituição", "professor": "Professor(a)", "cidade": "Cidade", "ano": "Ano", "titulo": "Título"}.items():
        if not str(dados.get(chave, "")).strip():
            raise ValidationError(f"O campo {rotulo} é obrigatório.")
    if not dados.get("autores"):
        raise ValidationError("Informe pelo menos um autor.")
    if not dados.get("secoes_textuais"):
        raise ValidationError("Informe pelo menos uma seção com título.")
    ano = str(dados.get("ano", "")).strip()
    if not ano.isdigit() or len(ano) != 4:
        raise ValidationError("O ano deve conter quatro dígitos.")


def _obter_texto(nome: str) -> str:
    return request.form.get(nome, "").strip()


def _obter_lista(nome: str) -> list[str]:
    valores = request.form.getlist(nome)
    if valores and any(valor.strip() for valor in valores):
        return [valor.strip() for valor in valores if valor.strip()]
    texto = _obter_texto(nome)
    if not texto:
        return []
    separador = ";" if ";" in texto else "\n"
    return [item.strip() for item in texto.split(separador) if item.strip()]


def _obter_autores_por_campos_numerados() -> list[str]:
    autores = []
    chaves = sorted([k for k in request.form.keys() if k.startswith("autor_")], key=lambda x: int(x.split("_")[1]))
    for chave in chaves:
        valor = request.form.get(chave, "").strip()
        if valor:
            autores.append(valor)
    return autores


def _obter_secoes_por_campos_numerados(pasta_temporaria: Path) -> list[dict[str, object]]:
    titulos, niveis, conteudos = request.form.getlist("secao_titulo"), request.form.getlist("secao_nivel"), request.form.getlist("secao_conteudo")
    secoes = []
    for indice, (titulo, nivel, conteudo) in enumerate(zip(titulos, niveis, conteudos), start=1):
        if titulo.strip():
            alinhamentos = request.form.getlist("secao_alinhamento_texto")
            espacamentos = request.form.getlist("secao_espacamento_linhas")
            recuos = request.form.getlist("secao_recuo_primeira_linha")
            secoes.append({"titulo": titulo.strip(), "nivel": int(nivel) if nivel.isdigit() else 1, "conteudo": conteudo.strip(), "alinhamento_texto": alinhamentos[indice - 1] if len(alinhamentos) >= indice else "justify", "espacamento_linhas": espacamentos[indice - 1] if len(espacamentos) >= indice else "1.5", "recuo_primeira_linha": recuos[indice - 1] if len(recuos) >= indice else "12.5", "imagens": _obter_imagens_da_secao(indice, pasta_temporaria)})
    return secoes


def _obter_imagens_da_secao(indice: int, pasta_temporaria: Path) -> list[dict[str, object]]:
    imagens = []
    arquivo = request.files.get(f"secao_imagem_{indice}_1")
    if not arquivo or not arquivo.filename:
        return imagens
    extensao = Path(secure_filename(arquivo.filename)).suffix.lower()
    if extensao not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("A imagem deve estar em PNG, JPG, GIF, BMP ou TIFF.")
    conteudo = arquivo.read()
    if len(conteudo) > MAX_IMAGE_BYTES:
        raise ValidationError("A imagem excede o limite de 10 MB.")
    caminho = pasta_temporaria / f"secao_{indice}_imagem_1{extensao}"
    caminho.write_bytes(conteudo)
    imagens.append({"caminho": str(caminho), "alinhamento": request.form.get(f"secao_imagem_{indice}_1_alinhamento", "center"), "largura_mm": request.form.get(f"secao_imagem_{indice}_1_largura", "100"), "titulo": request.form.get(f"secao_imagem_{indice}_1_titulo", "").strip(), "fonte": request.form.get(f"secao_imagem_{indice}_1_fonte", "").strip()})
    return imagens


def _normalizar_nome_arquivo(texto: str) -> str:
    return sub(r"_+", "_", sub(r"[^A-Za-z0-9_-]+", "_", texto.strip().lower())).strip("_")[:80]


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")


# Compatibilidade com imports antigos.
def gerar_documento_abnt_legacy(dados, caminho_saida):
    return gerar_documento_abnt(dados, caminho_saida)


# Evita que imports de teste falhem quando a função era esperada no módulo.
__all__ = ["app", "gerar_documento_abnt_legacy"]
