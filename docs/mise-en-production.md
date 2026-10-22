# Mise en production et release

Ce guide s'adresse à toute personne de l'équipe qui doit faire passer une version du staging à la production, y compris sans avoir suivi la mise en place du pipeline. Il dit quoi faire, dans quel ordre et où cliquer. Il est la seule description de cette procédure : les autres documents y renvoient.

Pour le reste : les règles de branches, de commits et de versions sont dans [`CONTRIBUTING.md`](../CONTRIBUTING.md), le fonctionnement du staging dans [`deploiement-staging.md`](deploiement-staging.md) et l'infrastructure AWS dans [`infra/terraform/aws/README.md`](../infra/terraform/aws/README.md).

> **La production est désactivée tant que la variable de dépôt `PRODUCTION_ENABLED` n'est pas à `true`** (*Settings > Secrets and variables > Actions > Variables*), ce qui suppose que l'infrastructure AWS existe. Dans cet état, les étapes 1 à 4 fonctionnent normalement. À l'étape 5, le run « Déploiement en production » apparaît avec le statut *skipped* et ne demande aucune approbation : il n'y a donc rien à chercher ni à valider.

## Vocabulaire

- **Recette** : test du staging par une personne de l'équipe, avant de figer une version.
- **sha** : identifiant court (7 caractères) d'un commit, par exemple `1824be5`. C'est lui qui relie le staging, la release et la production.
- **Release** : opération qui pose un tag de version `vX.Y.Z` sur un commit et publie une GitHub Release avec ses notes.
- **GHCR** : le registre d'images Docker de GitHub, où la CI publie les images des modules.
- **SSM** (AWS Systems Manager) : service qui permet de lancer des commandes sur l'instance de production sans SSH.
- **Environnement `production`** : réglage GitHub (*Settings > Environments*) qui impose une approbation humaine avant le déploiement.

## Le parcours en cinq étapes

1. Une PR est fusionnée sur `main` et le staging se met à jour tout seul.
2. Une personne fait la recette du staging.
3. Cette personne lance la release sur le sha recetté.
4. Le tag déclenche la préparation de la production.
5. Une personne approuve le déploiement.

## 1. Fusion et mise à jour du staging

Le merge d'une PR (squash) crée un `push` sur `main`. La CI s'exécute, puis `Publication des images`, puis la VM tire les nouvelles images (le mécanisme est décrit dans `deploiement-staging.md`). Le staging est à jour quand `version.sha` de http://10.43.43.50:8000/health (réseau de l'école) est le sha du commit de merge. Il n'y a pas de délai garanti : il faut attendre la fin de la CI, celle de la publication, puis au plus 2 minutes de minuteur.

**Ce que `/health` affiche n'est pas le numéro de version.** `version` y contient le titre du commit et son sha, et change à chaque merge. Le numéro `vX.Y.Z` n'existe qu'après l'étape 3. Tant qu'aucune release n'est lancée, la dernière version publiée reste la précédente, même si des PR ont été fusionnées entre-temps.

## 2. Recette

Une seule personne recette à la fois. Elle annonce dans le canal de l'équipe le sha qu'elle recette (« je recette `1824be5` ») pour que personne ne lance une autre release en parallèle.

Il n'existe pas de grille de recette écrite : il s'agit de vérifier sur le staging ce qui a changé depuis la dernière version. Pour le lister, depuis un clone à jour :

```bash
git log <dernier-tag>..<sha> --oneline
```

La page *Releases* du dépôt donne le dernier tag. La release est figée sur le sha saisi à l'étape suivante, quels que soient les merges qui arrivent ensuite. Un merge arrivé pendant la recette fait pourtant avancer le staging : `/health` n'affiche plus le sha recetté, alors que la case de confirmation de l'étape 3 atteste qu'il l'affiche. Il faut alors recetter le nouvel état, ou convenir dans l'équipe de ne pas fusionner pendant une recette.

## 3. Release

1. Relever `version.sha` dans http://10.43.43.50:8000/health.
2. Ouvrir GitHub > *Actions* > *Release* (colonne de gauche) > *Run workflow*, la branche `main` étant sélectionnée. Il faut avoir le droit d'écriture sur le dépôt.
3. Coller le sha, cocher la confirmation, lancer. La case est une déclaration : le workflow ne peut pas lire le staging lui-même, c'est la personne qui atteste avoir vérifié `/health` et fait la recette.

Le workflow vérifie le sha, calcule la version selon les règles de `CONTRIBUTING.md`, puis crée le tag et la GitHub Release (avec ses notes générées) sur ce commit exact. Le tag déclenche deux workflows : `Publication des images`, qui ajoute le tag de version à l'image déjà construite pour ce commit, sans reconstruction, et `Déploiement en production`. Le résumé du run `Release` affiche la version calculée et la liste des commits inclus.

Si ces deux workflows n'apparaissent pas après la release, le tag a été créé avec le jeton par défaut de GitHub, qui ne déclenche aucun workflow. Le workflow `Release` utilise normalement une GitHub App (variable d'organisation `RELEASE_APP_ID`, secret `RELEASE_APP_PRIVATE_KEY`) : vérifier qu'elle est toujours installée sur le dépôt.

**Si la release est refusée**, le message d'erreur du run indique pourquoi :

| Message | Cause | Que faire |
|---|---|---|
| Cocher la confirmation | la case n'était pas cochée | relancer en la cochant, après avoir vérifié `/health` |
| Sha invalide, ou inconnu ou ambigu | sha mal copié | recopier `version.sha` : 7 à 40 caractères hexadécimaux en minuscules |
| n'est pas sur `main` | le sha vient d'une autre branche | utiliser le sha affiché par le staging |
| porte déjà la version | ce commit est déjà publié | rien à faire |
| plus ancien que `vX.Y.Z` | une version plus récente existe déjà | recetter un commit plus récent |
| La CI du commit n'est pas verte (résultat : `failure`) | la CI de ce commit a échoué | corriger par une PR, puis recetter le nouveau commit |
| La CI du commit n'est pas verte (résultat : `aucune`) | aucune CI `push` n'existe pour ce commit | arrive si GitHub perd l'événement (incident du 21/10 sur les merges de #81 et #88) : fusionner une PR suivante et utiliser son sha |
| Aucun commit `feat` ou `fix` | seuls des commits sans effet sur la version depuis le dernier tag | rien à publier |

## 4. Préparation de la production

Le tag lance `Déploiement en production`. Son premier job (`resume`) n'a pas d'environnement : il écrit tout de suite, sur la page du run, un résumé avec le tag, le commit et le lien vers les notes de la version. Le job `deploy` attend ensuite l'approbation de l'environnement `production`.

## 5. Approbation et déploiement

Quand la production est activée, la personne qui approuve ouvre le run *Déploiement en production* du tag (onglet *Actions*), lit le résumé et vérifie que le tag est bien celui annoncé à l'équipe. Elle clique sur *Review deployments*, coche `production`, puis *Approve and deploy*. Les relecteurs sont ceux de *Settings > Environments > production* (six personnes) et l'auteur de la release peut approuver lui-même. Les administrateurs du dépôt peuvent aussi contourner l'approbation.

Après l'approbation, le workflow attend jusqu'à 10 minutes que les images du tag soient publiées sur GHCR, sauvegarde la base sur l'instance (`/var/backups/enervision`, les cinq dernières copies), déploie le tag par SSM puis contrôle que `/health` annonce l'environnement `production` et le commit du tag. Le détail technique est dans le README d'AWS. Un déploiement réussi se termine par « Production à jour : vX.Y.Z (sha) ». Un seul déploiement de production s'exécute à la fois.

Pour activer la production, la liste ordonnée des opérations (Terraform, `production.env`, variables GitHub) est dans `infra/terraform/aws/README.md`.

## Retour arrière

**Staging.** Le staging suit `main` : la voie normale est une PR `revert` du commit fautif, qui se déploie comme n'importe quel merge. En urgence, avec accès à la VM, ajouter `IMAGE_TAG=sha-<commit complet>` (les 40 caractères) dans `/etc/enervision/staging.env` : au passage suivant du minuteur, le staging redéploie cette image et reste figé dessus. `update-staging.sh` écrit un avertissement à chaque passage tant que la ligne existe, visible avec `journalctl -u update-staging.service`. Pendant ce temps, les recettes des autres portent sur une version qui ne bouge plus : retirer la ligne dès que le correctif est fusionné.

**Production.** GitHub > *Actions* > *Déploiement en production* > *Run workflow*, en indiquant un tag déjà publié (par exemple `v1.4.2`, visible sur la page *Releases*). Le workflow accepte uniquement un tag `vX.Y.Z` existant et situé sur `main`, demande la même approbation que pour une mise en production, sauvegarde la base, redéploie ce tag et contrôle `/health`. Aucun tag n'est créé. Un tag antérieur à l'ajout du sha dans `/health` (la série `v1.0.x`) échouerait au contrôle final.

Revenir au code précédent ne défait pas les données écrites entre-temps : en cas de doute sur la base, les sauvegardes de l'instance sont le recours. Ensuite, corriger par une PR `revert` ou un correctif, puis refaire une release par la procédure normale.
