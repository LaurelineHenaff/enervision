"""Validation des schémas Pydantic exposés par l'API."""
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.user import Role, User
from app.schemas.user import UserCreate, UserRead


def test_user_create_valide():
    user = UserCreate(email="alice@example.com", password="motdepasse")
    assert user.email == "alice@example.com"


def test_user_create_email_invalide():
    with pytest.raises(ValidationError):
        UserCreate(email="pas-un-email", password="motdepasse")


def test_user_create_mot_de_passe_trop_court():
    with pytest.raises(ValidationError):
        UserCreate(email="alice@example.com", password="court")


def test_user_create_ignore_le_role():
    # Impossible de s'inscrire en admin : le champ est ignoré
    user = UserCreate(email="alice@example.com", password="motdepasse", role="admin")
    assert not hasattr(user, "role")


def test_user_read_n_expose_pas_le_hash():
    user = User(
        id=1,
        email="alice@example.com",
        hashed_password="hash-secret",
        is_active=True,
        role=Role.USER,
        created_at=datetime.now(UTC),
    )
    data = UserRead.model_validate(user).model_dump()
    assert "hashed_password" not in data
    assert data["role"] == "user"
