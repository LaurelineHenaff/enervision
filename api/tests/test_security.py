"""Hachage des mots de passe : garde-fou contre la combinaison passlib / bcrypt incompatible."""
from app.core.security import hash_password, verify_password


def test_hash_et_verification_du_mot_de_passe():
    hashed = hash_password("motdepasse-de-test")
    assert hashed != "motdepasse-de-test"
    assert verify_password("motdepasse-de-test", hashed)
    assert not verify_password("autre-mot-de-passe", hashed)
