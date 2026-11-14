# Lab-SCM-Git-cours-devops-
 
Petit outil en ligne de commande, écrit en Python, qui indique si une adresse IP appartient à **AWS**. Il peut aussi analyser un **groupe d'adresses IP** : il calcule le plus petit sous-réseau qui les contient toutes et indique si ce sous-réseau est couvert par les plages AWS.
 
Le projet a été réalisé en binôme dans le cadre du TP **SCM / Git** du cours DevOps. L'objectif était de pratiquer les branches, les merges, la résolution de conflits et le découpage d'une feature en sous-features.
 
Le script de départ est [`awsip.py`](https://github.com/psantus/does-this-ip-belong-to-aws/blob/main/python/awsip.py), de *psantus/does-this-ip-belong-to-aws*.
 
---
 
## Fonctionnalités
 
### Vérifier une IP (fonctions de base)
- Télécharge la liste officielle des plages IP AWS ([`ip-ranges.json`](https://ip-ranges.amazonaws.com/ip-ranges.json)).
- Trouve toutes les plages AWS qui contiennent l'IP donnée, avec le service et la région de chacune.
- Pour chaque plage, ajoute :
  - la **première IP** de la plage ;
  - la **dernière IP** de la plage ;
  - le **nombre d'adresses** de la plage.
### Analyser un groupe d'IPs (nouvelle feature)
Cette feature est découpée en sous-features :
 
| # | Sous-feature | Fonction |
|---|---|---|
| 1 | Lire et valider les IPs (arguments ou fichier) | `parse_ips()` |
| 2 | Calculer le plus petit sous-réseau commun | `smallest_subnet()` |
| 3 | Croiser ce sous-réseau avec les plages AWS | `aws_coverage()` |
| 4 | Interface en ligne de commande et menu interactif | `main()`, `interactive_menu()` |
 
La couverture AWS peut être :
- **totale** : le sous-réseau est entièrement contenu dans une plage AWS ;
- **partielle** : le sous-réseau chevauche une ou plusieurs plages AWS sans y être entièrement contenu ;
- **aucune** : le sous-réseau n'a aucun lien avec AWS.
Les entrées invalides sont ignorées et comptées. Mélanger des IPv4 et des IPv6 dans un même groupe est refusé.
 
---
 
## Structure du projet
 
```
.
├── awsip.py      # Fonctions de base : téléchargement des plages AWS, recherche d'une IP
├── features.py   # Analyse de groupe (sous-features 1 à 3) + point d'entrée (CLI / menu)
├── Test.py       # Tests unitaires de parse_ips et aws_coverage
└── README.md
```
 
---
 
## Prérequis
 
- **Python 3.7 ou plus**
- Une connexion Internet, pour télécharger `ip-ranges.json`
- Aucune dépendance externe : le projet n'utilise que la bibliothèque standard (`ipaddress`, `argparse`, `json`, `urllib`, `unittest`)
---
 
## Installation
 
```bash
git clone https://github.com/pul24r3/Lab-SCM-Git-cours-devops-.git
cd Lab-SCM-Git-cours-devops-
```
 
---
 
## Utilisation
 
Le point d'entrée du programme est `features.py`.
 
### Vérifier une seule IP
```bash
python features.py check 52.95.110.1
```
Le programme affiche, au format JSON, les plages AWS qui contiennent cette IP. Si l'IP n'appartient pas à AWS, il affiche une liste vide `[]`.
```json
[
  {
    "ip_prefix": "52.95.110.0/24",
    "region": "eu-west-3",
    "service": "AMAZON",
    "network_border_group": "eu-west-3",
    "first_ip": "52.95.110.0",
    "last_ip": "52.95.110.255",
    "num_addresses": 256
  }
]
```
 
### Analyser un groupe d'IPs
```bash
python features.py group 52.95.110.1 52.95.110.40
```
ou depuis un fichier, avec une IP par ligne (les lignes vides et celles qui commencent par `#` sont ignorées) :
```bash
python features.py group --file ips.txt
```
Exemple de sortie :
```
========== GROUP IP ANALYSIS ==========
IPs analyzed       : 2
Smallest subnet    : 52.95.110.0/26
Network capacity   : 64 addresses
AWS coverage       : totale
 - AMAZON / eu-west-3 (52.95.110.0/24) : totale
```
 
### Menu interactif
Si on lance le programme sans argument, un menu propose de choisir entre les deux modes :
```bash
python features.py
```
```
========== AWS IP ANALYZER ==========
1. Check a single IP address
2. Analyze a group of IP addresses
```
 
### Aide
```bash
python features.py --help
python features.py group --help
```
 
> Les valeurs des exemples ne sont données qu'à titre d'illustration. Les plages AWS changent régulièrement.
 
---
 
## Tests
 
Les tests utilisent `unittest`, qui fait partie de Python. Ils ne nécessitent **pas** de connexion Internet, car ils travaillent sur un faux extrait de `ip-ranges.json`.
 
```bash
python -m unittest Test -v
```
 
Ce qui est testé :
- **`parse_ips`** : tri et suppression des doublons, signalement des entrées invalides, lecture depuis un fichier, erreur si aucune IP n'est valide, refus du mélange IPv4/IPv6 ;
- **`aws_coverage`** : couverture totale, partielle et aucune, et réseau IPv6 comparé à des plages IPv4.
---
 
## Workflow Git utilisé
 
1. Chaque membre du binôme développe sur sa propre branche (`Joseph`, `feature/nb-adress`, `feature/smallest-subnet`, …).
2. Les premières évolutions sont ajoutées sur `awsip.py` en parallèle : première et dernière IP de la plage d'un côté, nombre d'adresses de l'autre.
3. Une première branche est mergée sur `main`.
4. Les conflits entre la seconde branche et `main` sont résolus lors du merge.
5. La feature « analyse de groupe » est découpée en sous-features, développées sur des branches séparées puis intégrées.
---
 
## Auteurs
 
Projet réalisé en binôme :
- Joseph BAMENOU — sous-features 1 et 3 (`parse_ips`, `aws_coverage`), tests
- Marys MYASSI — sous-feature 2 (`smallest_subnet`), CLI