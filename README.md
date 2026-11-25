# Calquory
Un client signale qu’une application échoue uniquement dans son environnement. Le support demande des journaux, des paramètres et un échantillon de données. Ces fichiers contiennent des informations confidentielles.

Le CLI Python projette un journal JSON selon une liste de champs autorisés, remplace les références de commande par des alias cohérents et supprime les lignes superflues tant qu’un double enregistrement de livraison reste observable.

## Démarrage

Depuis la racine du dépôt avec Python 3.10 ou ultérieur et Make :

```sh
make demo
make test
```

Commande directe :

```sh
python3 -m calquory reduce examples/events.json examples/policy.json > dossier.json
python3 -m calquory replay dossier.json
```

Cinq événements deviennent deux livraisons avec le même alias. La commande `replay` reproduit le doublon sur le dossier exporté.

Codes de sortie : 0 prêt ou reproduit, 1 politique bloquante ou problème absent, 2 entrée invalide.

## Organisation

- `calquory.py` contient le moteur et son interface en ligne de commande.
- `examples/` contient les entrées fictives et reproductibles.
- `tests/` couvre le comportement nominal et les cas limites.

## Périmètre du socle

Le socle accepte un journal JSON structuré et l’oracle intégré `duplicate_delivery_v1`. Il émet des alias et des catégories d’événements prédéfinies. Une politique qui retire la clé nécessaire bloque l’export des événements. Les traces libres, commandes de reproduction externes et garanties générales d’anonymat restent hors de ce périmètre.

## Premier chantier à reprendre

Introduire un second fichier de commandes lié aux événements. Préserver les références entre fichiers et rejouer le même échec sur une copie indépendante du dossier. Ajouter une politique qui rend le cas impossible à partager.

## Préparer un dossier commun de reprise et d’accès

Le profil d’export fixe accepte la chronologie `timeline.v1` de Horvessane. Il conserve les références locales numérotées, les relations d’ordre et les comparaisons de présence, d’égalité ou de durée. Les noms, les empreintes et les instants absolus sont retirés. Le rejeu recalcule le constat sur les valeurs projetées. La topologie temporelle et le type de constat demeurent visibles dans le dossier.

```sh
python3 -m calquory pack-timeline chronologie.json > dossier-partageable.json
python3 -m calquory replay dossier-partageable.json > constats.json
```

L’exercice complet se lance avec `make demo-suite` depuis [Horvessane](https://github.com/PISSARAW/Horvessane).
