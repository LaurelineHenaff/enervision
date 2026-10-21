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
3. Pull requests petites et ciblées, liées à une issue GitHub : `Closes #12` dans la description ferme l'issue au merge et déplace sa carte dans le Project. Une PR sans issue est tolérée pour une correction triviale.
4. Une approbation minimum, donnée par quelqu'un d'autre que l'auteur, et une CI verte avant le merge. Chacun relit au moins une PR par jour.
5. Merge en **squash**, seule méthode autorisée sur le dépôt (réglages du dépôt : merge commit et rebase désactivés, message du squash = titre de la PR). Le titre de la PR devient donc l'unique commit sur `main` : c'est lui qui décide de la version (`feat:`, `fix:`, `!` pour une rupture), et la CI le vérifie. La branche source est supprimée automatiquement au merge (réglage « Automatically delete head branches ») ; supprimer aussi la copie locale avec `git branch -d`.
6. Commits en [Conventional Commits](https://www.conventionalcommits.org/fr) avec un type parmi `feat`, `fix`, `docs`, `chore`, `infra`, `test`, `refactor`, `ci`. Le nom de branche, chaque commit et le titre de la PR sont vérifiés par la CI. Chacun commite avec son propre compte et son vrai nom, sur son poste.
7. Aucun secret dans Git : variables dans un `.env` ignoré, avec un `.env.example` versionné. Les accès (API, VM, AWS) restent hors dépôt.
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

**Versionnage.** Une seule version pour tout le monorepo, en [SemVer](https://semver.org/lang/fr/) : `vMAJOR.MINOR.PATCH`. Les tags ne sont posés que sur `main`.

- `feat:` incrémente le MINOR, `fix:` le PATCH, un `!` après le type (`feat!:`) ou un pied `BREAKING CHANGE:` le MAJOR.
- La release se lance à la main, après la recette du staging, par la personne qui a recetté : GitHub > Actions > Release > Run workflow. Elle saisit le sha affiché par `version.sha` dans http://10.43.43.50:8000/health (réseau de l'école) et coche la confirmation. Le workflow vérifie que ce commit est sur `main`, que sa CI est verte et qu'il est plus récent que le dernier tag, puis calcule la version (au moins un `feat:` ou un `fix:` depuis le dernier tag), crée le tag et la GitHub Release avec ses notes. Les merges qui arrivent entre-temps n'ont aucun effet : le tag est posé sur le commit recetté. Il n'y a pas de PR de release. Les commits `docs:`, `chore:`, `ci:`, `test:`, `refactor:` et `infra:` seuls ne donnent pas de version. Une seule release s'exécute à la fois. Annoncer dans le canal de l'équipe la recette en cours (« je recette `b2e91b8` ») évite que deux personnes recettent des versions différentes.

**Promotion.** On construit une fois et on promeut le même artefact, sans le reconstruire.

| Environnement | Déclencheur | Cible |
|---|---|---|
| dev | local, `docker compose` | poste de chacun |
| staging | merge sur `main` | VM Proxmox du groupe |
| production | tag `vX.Y.Z` | AWS |

1. Le merge sur `main` construit les images Docker, les tague avec le SHA du commit et les déploie en staging après passage de la CI (tests, Trivy).
2. **Recette.** Une personne teste le staging et relève le sha déployé dans `version.sha` de http://10.43.43.50:8000/health. Elle prévient l'équipe de la version qu'elle recette (« je recette `b2e91b8` ») pour que personne ne lance une autre release en parallèle.
3. **Release.** La même personne lance GitHub > Actions > Release > Run workflow avec ce sha et la case de confirmation cochée. Le tag `vX.Y.Z` est posé sur ce commit exact et re-tague la même image (sans la reconstruire) avec la version.
4. **Mise en production.** Le tag lance `deploy-production.yml`. L'environnement GitHub `production` exige une approbation avant le déploiement : la page de l'exécution affiche d'abord un résumé (version, commit, lien vers les notes de la release). L'auteur de la release peut approuver lui-même. Une fois déployée, l'API de production doit annoncer l'environnement `production` et le commit du tag sur `/health` ; le workflow le contrôle.

**Retour arrière.**

- **Staging.** Il suit `main`, donc on annule le commit fautif par une PR `revert` (le staging se met à jour environ 10 minutes après le merge). En urgence, avec accès à la VM : ajouter `IMAGE_TAG=sha-<commit complet>` dans `/etc/enervision/staging.env` ; le staging est alors figé sur cette version, et le script affiche un avertissement à chaque passage tant que la ligne existe. La retirer dès que le correctif est fusionné.
- **Production.** GitHub > Actions > « Déploiement en production » > Run workflow, en indiquant le tag vers lequel revenir (par exemple `v1.4.2`, visible sur la page Releases). Le workflow vérifie que le tag existe et que ses images sont publiées, puis demande la même approbation que pour une mise en production, sauvegarde la base sur l'instance, redéploie ce tag et contrôle `/health`. Aucun tag n'est créé.
- **Ensuite.** Corriger par une PR `revert` ou un correctif, puis faire une nouvelle release par la procédure normale. Revenir au code précédent ne défait pas les données écrites entre-temps : les sauvegardes sont dans `/var/backups/enervision` sur l'instance (les cinq dernières).
- **Prérequis.** L'environnement GitHub `production` doit autoriser la branche `main` en plus des tags `v*` (Settings > Environments > production > Deployment branches and tags), car un lancement manuel s'exécute depuis `main`.

**Modèles ML.** Dans MLflow, un modèle entraîné devient `challenger`. Il est promu `champion` (alias utilisé par `/predict` en production) seulement s'il bat le champion actuel sur les métriques de validation. La promotion est tracée dans le registre et mentionnée dans la PR ou le rapport de décision.
