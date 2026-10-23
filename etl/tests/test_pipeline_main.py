"""Point d'entrée python -m pipeline : choix du traitement."""
import json

import pandas as pd

from pipeline.__main__ import JOBS, main


def test_sans_argument_ou_traitement_inconnu_renvoie_2(capsys):
    assert main([]) == 2
    assert main(["inexistant"]) == 2
    assert "clean-history" in capsys.readouterr().err


def test_chaque_traitement_declare_est_importable():
    import importlib

    for module in JOBS.values():
        assert callable(importlib.import_module(module).main)


def test_lance_le_traitement_demande(tmp_path):
    entree, sortie, meta = tmp_path / "in.csv", tmp_path / "out.parquet", tmp_path / "meta.json"
    meta.write_text(json.dumps({"frequency": "1h", "sites": {}}))
    pd.DataFrame(
        {"timestamp": ["2023-01-01 00:00:00"], "site_id": ["SITE001"], "consumption_kwh": [1.0]}
    ).to_csv(entree, index=False)

    assert main(["clean-history", "--input", str(entree), "--metadata", str(meta), "--output", str(sortie)]) == 0
    assert len(pd.read_parquet(sortie)) == 1
