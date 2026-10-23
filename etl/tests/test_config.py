"""Configuration : les valeurs de l'API Mock viennent des variables d'environnement."""
import importlib

from mock_client import config


def test_lit_les_variables_d_environnement(monkeypatch):
    monkeypatch.setenv("MOCK_API_URL", "http://autre-mock.test")
    monkeypatch.setenv("MOCK_API_USERNAME", "bob")
    monkeypatch.setenv("MOCK_API_PASSWORD", "mdp")
    try:
        importlib.reload(config)
        assert config.MOCK_API_URL == "http://autre-mock.test"
        assert config.MOCK_API_USERNAME == "bob"
        assert config.MOCK_API_PASSWORD == "mdp"
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_url_par_defaut_et_sans_slash_final(monkeypatch):
    monkeypatch.delenv("MOCK_API_URL", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    try:
        importlib.reload(config)
        assert config.MOCK_API_URL == "http://10.43.43.80:8000"
        monkeypatch.setenv("MOCK_API_URL", "http://mock.test/")
        importlib.reload(config)
        assert config.MOCK_API_URL == "http://mock.test"
    finally:
        monkeypatch.undo()
        importlib.reload(config)
