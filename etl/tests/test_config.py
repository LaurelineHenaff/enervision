"""Configuration : les valeurs de l'API Mock viennent des variables d'environnement."""
import importlib

from api_mock import config


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
