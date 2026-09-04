from __future__ import annotations

from datetime import datetime
from pathlib import Path
from re import sub
from uuid import uuid4
import tempfile

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from gerador_abnt import gerar_documento_abnt


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
ALLOWED_EXTENSION = ".docx"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024

app = Flask(__name__)
app.config["SECRET_KEY"] = "altere-esta-chave-em-producao"
app.config["OUTPUT_DIR"] = OUTPUT_DIR


class ValidationError(Exception):
    pass


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/gerar", methods=["POST"])
def gerar_documento():
    try:
        with tempfile.TemporaryDirectory(prefix="abnt_imagens_") as pasta_temporaria:
            dados = _coletar_dados_formulario(Path(pasta_temporaria))
            _validar_dados_obrigatorios(dados)
            caminho_saida = _criar_caminho_saida(dados["titulo"])
            arquivo_gerado = gerar_documento_abnt(dados, caminho_saida)
        return send_file(
            arquivo_gerado,
            as_attachment=True,
            download_name=arquivo_gerado.name,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except ValidationError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("index"))
    except Exception:
        app.logger.exception("Falha ao gerar documento ABNT")
        flash("Não foi possível gerar o documento. Revise os dados enviados e tente novamente.", "erro")
        return redirect(url_for("index"))


@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}


def _coletar_dados_formulario(pasta_temporaria: Path) -> dict[str, object]:
    autores = _obter_autores_por_campos_numerados()
    secoes = _obter_secoes_por_campos_numerados(pasta_temporaria)

    return {
        "autores": autores,
        "instituicao": _obter_texto("instituicao"),
        "curso_disciplina": _obter_texto("curso_disciplina"),
        "professor": _obter_texto("professor"),
        "cidade": _obter_texto("cidade"),
        "ano": _obter_texto("ano"),
        "titulo": _obter_texto("titulo"),
        "subtitulo": _obter_texto("subtitulo"),
        "tipo_trabalho": _obter_texto("tipo_trabalho"),
        "natureza_trabalho": _obter_texto("natureza_trabalho"),
        "folha_aprovacao": _obter_texto("folha_aprovacao"),
        "texto_aprovacao": _obter_texto("texto_aprovacao"),
        "banca_examinadora": _obter_lista("banca_examinadora"),
        "dedicatoria": _obter_texto("dedicatoria"),
        "agradecimentos": _obter_texto("agradecimentos"),
        "epigrafe": _obter_texto("epigrafe"),
        "resumo": _obter_texto("resumo"),
        "palavras_chave": _obter_lista("palavras_chave"),
        "abstract": _obter_texto("abstract"),
        "keywords": _obter_lista("keywords"),
        "secoes_textuais": secoes,
        "referencias": _obter_lista("referencias"),
        "glossario": _obter_texto("glossario"),
        "apendice": _obter_texto("apendice"),
        "anexo": _obter_texto("anexo"),
        "indice": _obter_texto("indice"),
    }


def _validar_dados_obrigatorios(dados: dict[str, object]) -> None:
    campos_obrigatorios = {
        "instituicao": "Instituição",
        "professor": "Professor(a)",
        "cidade": "Cidade",
        "ano": "Ano",
        "titulo": "Título",
    }

    for chave, rotulo in campos_obrigatorios.items():
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
    valores_multiplos = request.form.getlist(nome)
    if valores_multiplos and any(valor.strip() for valor in valores_multiplos):
        return [valor.strip() for valor in valores_multiplos if valor.strip()]

    texto = _obter_texto(nome)
    if not texto:
        return []

    separador = ";" if ";" in texto else "\n"
    return [item.strip() for item in texto.split(separador) if item.strip()]


def _obter_autores_por_campos_numerados() -> list[str]:
    autores: list[str] = []
    # Garantir ordem correta dos autores
    chaves_ordenadas = sorted([k for k in request.form.keys() if k.startswith("autor_")], 
                              key=lambda x: int(x.split('_')[1]))
    for chave in chaves_ordenadas:
        valor = request.form.get(chave, "").strip()
        if valor:
            autores.append(valor)
    return autores


def _obter_secoes_por_campos_numerados(pasta_temporaria: Path) -> list[dict[str, object]]:
    titulos = request.form.getlist("secao_titulo")
    niveis = request.form.getlist("secao_nivel")
    conteudos = request.form.getlist("secao_conteudo")
    secoes = []
    for indice, (t, n, c) in enumerate(zip(titulos, niveis, conteudos), start=1):
        if t.strip():
            secoes.append({
                "titulo": t.strip(),
                "nivel": int(n) if n.isdigit() else 1,
                "conteudo": c.strip(),
                "imagens": _obter_imagens_da_secao(indice, pasta_temporaria),
            })
    return secoes


def _obter_imagens_da_secao(indice: int, pasta_temporaria: Path) -> list[dict[str, object]]:
    imagens = []
    for slot in (1,):
        arquivo = request.files.get(f"secao_imagem_{indice}_{slot}")
        if not arquivo or not arquivo.filename:
            continue
        extensao = Path(secure_filename(arquivo.filename)).suffix.lower()
        if extensao not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(f"A imagem {slot} da seção {indice} deve estar em PNG, JPG, GIF, BMP ou TIFF.")
        conteudo = arquivo.read()
        if len(conteudo) > MAX_IMAGE_BYTES:
            raise ValidationError(f"A imagem {slot} da seção {indice} excede o limite de 10 MB.")
        nome = f"secao_{indice}_imagem_{slot}{extensao}"
        caminho = pasta_temporaria / nome
        caminho.write_bytes(conteudo)
        imagens.append({
            "caminho": str(caminho),
            "alinhamento": request.form.get(f"secao_imagem_{indice}_{slot}_alinhamento", "center"),
            "largura_mm": request.form.get(f"secao_imagem_{indice}_{slot}_largura", "100"),
            "titulo": request.form.get(f"secao_imagem_{indice}_{slot}_titulo", "").strip(),
            "fonte": request.form.get(f"secao_imagem_{indice}_{slot}_fonte", "").strip(),
        })
    return imagens

#
def _criar_caminho_saida(titulo: str) -> Path:
    app.config["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)
    nome_base = _normalizar_nome_arquivo(titulo) or "trabalho_abnt"
    identificador = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
    return app.config["OUTPUT_DIR"] / f"{nome_base}_{identificador}{ALLOWED_EXTENSION}"


def _normalizar_nome_arquivo(texto: str) -> str:
    texto_normalizado = sub(r"[^A-Za-z0-9_-]+", "_", texto.strip().lower())
    texto_normalizado = sub(r"_+", "_", texto_normalizado).strip("_")
    return texto_normalizado[:80]


if __name__ == "__main__":
    app.run(debug=True)
