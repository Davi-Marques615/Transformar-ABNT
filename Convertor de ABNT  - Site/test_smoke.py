import os
import tempfile
from pathlib import Path

os.environ["ALLOW_UNPAID_GENERATION"] = "1"
os.environ["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "abnt_smoke.sqlite3")
Path(os.environ["DATABASE_PATH"]).unlink(missing_ok=True)
from app import app

app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
client = app.test_client()
for path in ["/", "/planos", "/entrar", "/cadastro", "/health"]:
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code)

with client.session_transaction() as sess:
    sess["csrf_token"] = "test-token"
response = client.post("/cadastro", data={"csrf_token": "test-token", "email": "teste@example.com", "password": "senha-segura-123"}, follow_redirects=True)
assert response.status_code == 200
assert b"Escolha seu plano" in response.data
response = client.get("/conta")
assert response.status_code == 200
print("smoke ok")
