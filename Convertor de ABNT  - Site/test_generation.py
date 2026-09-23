import os
import tempfile
from pathlib import Path

os.environ["ALLOW_UNPAID_GENERATION"] = "1"
os.environ["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "abnt_generation.sqlite3")
Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
from app import app

app.config.update(TESTING=True)
client = app.test_client()
with client.session_transaction() as sess:
    sess["csrf_token"] = "test-token"
client.post("/cadastro", data={"csrf_token": "test-token", "email": "geracao@example.com", "password": "senha-segura-123"})
with client.session_transaction() as sess:
    token = sess["csrf_token"]
form = {
    "csrf_token": token, "instituicao": "Universidade Teste", "professor": "Prof. Teste", "cidade": "São Paulo", "ano": "2026", "titulo": "Trabalho de Teste", "autor_1": "Aluno Teste", "secao_titulo": "Introdução", "secao_nivel": "1", "secao_conteudo": "Este é um parágrafo de teste."
}
response = client.post("/gerar", data=form)
assert response.status_code == 200, response.status_code
assert response.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
assert response.data[:2] == b"PK"
assert not list(Path.cwd().glob("*.docx"))
print("generation ok", len(response.data), "bytes")
