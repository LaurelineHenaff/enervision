# Politique Git

Le projet suit un GitHub Flow avec des branches courtes. Le dépôt est un monorepo.

## Structure

```
api/        API (données, prédictions, anomalies) et ses tests (api/tests)
etl/        batch d'ingestion et nettoyage en pandas, tests (etl/tests)
ml/         entraînement, challengers, MLflow, tests (ml/tests)
frontend/   dashboard web, tests Cypress (frontend/cypress)
infra/      Terraform, Docker, scripts de déploiement (infra/scripts)
docs/       architecture, rapports de décision, comptes rendus
.github/    workflows CI/CD et gabarit de PR
```

Chaque composant garde ses tests. Les workflows de CI/CD vivent dans `.github/workflows/`, seul emplacement lu par GitHub Actions.

## Règles

1. `main` est toujours déployable. Aucun push direct : tout passe par une pull request.
2. Une branche par tâche, créée depuis `main` à jour, nommée directement par son sujet, sans préfixe ni `/` : minuscules et tirets, 50 caractères maximum (ex. `endpoint-readings`, `ci-trivy`). Durée de vie visée : moins d'un jour, deux au maximum.
3. Pull requests petites et ciblées, liées à un ticket Notion (lien dans la description), avec une description et ce qui a été testé.
4. Une approbation minimum, donnée par quelqu'un d'autre que l'auteur, et une CI verte avant le merge. Chacun relit au moins une PR par jour.
5. Merge en **squash**, puis suppression de la branche.
6. Commits en [Conventional Commits](https://www.conventionalcommits.org/fr) avec un type parmi `feat`, `fix`, `docs`, `chore`, `infra`, `test`, `refactor`, `ci`. Le nom de branche, chaque commit et le titre de la PR sont vérifiés par la CI. Chacun commite avec son propre compte et son vrai nom, sur son poste.
7. Aucun secret dans Git : variables dans un `.env` ignoré, avec un `.env.example` versionné. Les accès (API, VM, Azure) restent hors dépôt.
8. Un conflit se résout dans la branche de la tâche (`git rebase main` ou `git merge main`), jamais en réécrivant `main`.

## Cycle d'une tâche

```
git switch main && git pull
git switch -c ma-tache
# ... travail, commits fréquents
git push -u origin ma-tache
# ouvrir la PR, demander une revue, corriger, squash merge
```

## Revues

Relire, c'est vérifier que le code répond au ticket, qu'il est testé, lisible et sans secret. Les remarques se font dans la PR. L'auteur répond ou corrige, le reviewer approuve quand tout est réglé. Le rôle tournant (PO, Tech Lead, etc.) ne dispense personne de relire.

## Versions, tags et promotion

**Versionnage.** Une seule version pour tout le monorepo, en [SemVer](https://semver.org/lang/fr/) : `vMAJOR.MINOR.PATCH`. Tant que le produit n'est pas livré, on reste en `v0.x`. Les tags ne sont posés que sur `main`.

- `feat:` incrémente le MINOR, `fix:` le PATCH, un `!` après le type (`feat!:`) ou un pied `BREAKING CHANGE:` le MAJOR.
- Un candidat à la livraison est tagué `v0.2.0-rc.1` avant le tag final `v0.2.0`.
- La version est calculée à partir des Conventional Commits, avec release-please (GitHub Action) : il ouvre une PR « release » qui met à jour le `CHANGELOG.md`, et son merge crée le tag et la GitHub Release. Personne ne tague à la main.

**Promotion.** On construit une fois et on promeut le même artefact, sans le reconstruire.

| Environnement | Déclencheur | Cible |
|---|---|---|
| dev | local, `docker compose` | poste de chacun |
| staging | merge sur `main` | VM Proxmox du groupe |
| production | tag `vX.Y.Z` | Azure |

1. Le merge sur `main` construit les images Docker, les tague avec le SHA du commit et les déploie en staging après passage de la CI (tests, Trivy).
2. Le tag `vX.Y.Z` re-tague la même image (sans la reconstruire) avec la version, puis la déploie en production. L'environnement GitHub `production` exige une approbation manuelle d'une personne autre que l'auteur.
3. Un retour arrière se fait en redéployant le tag précédent.

**Modèles ML.** Dans MLflow, un modèle entraîné devient `challenger`. Il est promu `champion` (alias utilisé par `/predict` en production) seulement s'il bat le champion actuel sur les métriques de validation. La promotion est tracée dans le registre et mentionnée dans la PR ou le rapport de décision.
