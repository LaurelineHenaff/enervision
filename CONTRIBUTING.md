# Politique Git

Le projet suit un GitHub Flow avec des branches courtes. Le dépôt est un monorepo.

## Structure

```
backend/     API et ETL
frontend/    dashboard web
infra/       IaC (Terraform), Docker, scripts de déploiement
data/        scripts et modèles de données (jamais de données sensibles)
docs/        architecture, décisions, comptes rendus
```

## Règles

1. `main` est toujours déployable. Aucun push direct : tout passe par une pull request.
2. Une branche par tâche, créée depuis `main` à jour, nommée `feat/…`, `fix/…`, `docs/…`, `chore/…` ou `infra/…` (ex. `feat/endpoint-readings`). Durée de vie visée : moins d'un jour, deux au maximum.
3. Pull requests petites et ciblées, liées à un ticket (`Closes #12`), avec une description et ce qui a été testé.
4. Une approbation minimum, donnée par quelqu'un d'autre que l'auteur, et une CI verte avant le merge. Chacun relit au moins une PR par jour.
5. Merge en **squash**, puis suppression de la branche.
6. Commits en [Conventional Commits](https://www.conventionalcommits.org/fr) : `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`. Chacun commite avec son propre compte et son vrai nom, sur son poste.
7. Aucun secret dans Git : variables dans un `.env` ignoré, avec un `.env.example` versionné. Les accès (API, VM, Azure) restent hors dépôt.
8. Un conflit se résout dans la branche de la tâche (`git rebase main` ou `git merge main`), jamais en réécrivant `main`.

## Cycle d'une tâche

```
git switch main && git pull
git switch -c feat/ma-tache
# ... travail, commits fréquents
git push -u origin feat/ma-tache
# ouvrir la PR, demander une revue, corriger, squash merge
```

## Revues

Relire, c'est vérifier que le code répond au ticket, qu'il est testé, lisible et sans secret. Les remarques se font dans la PR. L'auteur répond ou corrige, le reviewer approuve quand tout est réglé. Le rôle tournant (PO, Tech Lead, etc.) ne dispense personne de relire.
