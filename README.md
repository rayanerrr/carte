<div align="center">

# CarteIdéale

**Trouve la carte de crédit canadienne qui te correspond vraiment.**

*Un moteur de recommandation personnalisé — pas un classement générique.*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Cards](https://img.shields.io/badge/Cartes-116-E63946?style=flat-square)](/)
[![License](https://img.shields.io/badge/Licence-MIT-22C55E?style=flat-square)](LICENSE)

</div>

---

## Pourquoi CarteIdéale ?

La plupart des comparateurs de cartes de crédit affichent le même top 5 à tout le monde. CarteIdéale fonctionne différemment : un questionnaire de 10 sections analyse ton profil complet — tes dépenses réelles, tes commerces habituels, ta tolérance aux frais, tes habitudes de voyage — et calcule un score de compatibilité unique pour chacune des 116 cartes de la base de données.

Une carte à 99% de match pour toi peut être à 34% pour quelqu'un d'autre.

---

## Fonctionnement de l'algorithme

### Les 8 dimensions scorées

Chaque carte reçoit un score entre `0.0` et `1.0` sur 8 dimensions indépendantes.

| Dimension | Ce qu'elle mesure |
|---|---|
| `rewards_earning` | Taux de récompenses ajustés à **tes** dépenses réelles (épicerie, essence, restos…) avec les CPP réels (Milesopedia 2025) |
| `fee_value` | Compatibilité des frais annuels avec ton budget — dégradé progressif dès que tu approches ton max |
| `reward_type_fit` | Cashback vs points — si tu veux du cashback simple, les cartes à points sont fortement pénalisées |
| `eligibility` | Probabilité d'approbation — revenu vs minimum requis, score de crédit vs exigences de la carte |
| `insurance_coverage` | Assurances utiles selon **ta situation** — les couvertures déjà incluses via ton employeur comptent moins |
| `points_program_quality` | Valeur réelle du programme (Amex MR = 2.0¢/pt, Aéroplan = 1.6¢/pt, Scene+ = 1.0¢/pt…) |
| `travel_perks` | Salons, crédit NEXUS, 1er bagage gratuit — pondéré selon ta fréquence de voyage |
| `network_store_fit` | Visa / Mastercard / Amex vs tes commerces habituels (Costco accepte MC seulement, Maxi/Provigo refusent Amex) |

### Les poids s'adaptent à ton profil

Les poids de base sont ajustés dynamiquement selon tes réponses :

```
"Cashback seulement"        →  reward_type_fit  : 3.5 → 6.0
"Maximiser les récompenses" →  rewards_earning  : 5.0 → 8.0
"Frais les plus bas"        →  fee_value        : 4.0 → 7.0
"Avantages voyage"          →  travel_perks     : 1.5 → 4.5
"4+ voyages/an"             →  travel_perks     : +2.0  insurance : +1.0
"Jamais de voyage"          →  travel_perks     : plafonné à 0.5
"Costco régulier"           →  network_store_fit: 1.5 → 4.5
```

### Les red flags — pénalités multiplicatives

Certaines incompatibilités sont si critiques qu'elles pénalisent le score de façon dramatique. Les multiplicateurs se combinent entre eux.

| Situation | Multiplicateur |
|---|---|
| Costco régulier + Visa ou Amex | `× 0.12` — quasi-élimination |
| Amex + épicerie uniquement Maxi/Provigo | `× 0.38` |
| Préfère cashback strict + carte points | `× 0.55` |
| Refusé récemment + carte exigeante | `× 0.40` |
| Ne voyage pas + carte voyage >200$/an | `× 0.50` |
| Institution exclue par l'utilisateur | `× 0.00` — élimination totale |

### La formule finale

```
             [ Σ (Score_i × Poids_i(profil)) ]
Match_% = max│ ──────────────────────────── × 100 × Π(red_flags), 5 │  min 99
             [       Σ Poids_i(profil)       ]
```

Le classement combine le match et le ROI annuel :

```
Score_rang = Match_% × 0.60  +  ROI_normalisé × 0.40
```

---

## Base de données

**116 cartes canadiennes** couvrant 25+ émetteurs.

<details>
<summary>Voir tous les émetteurs</summary>

| Émetteur | Cartes |
|---|---|
| American Express | Cobalt, Gold Rewards, Platinum |
| ATB | Gold Cash Rewards, Gold My Rewards, World Elite |
| BMO | CashBack World Elite, eclipse Visa Infinite, VIPorter (3 niveaux) |
| BRIM | Mastercard, World Elite |
| CIBC | Aeroplan Visa, Costco Mastercard, Dividend Platinum, Select |
| Desjardins | Bonus, Cash Back (3 niveaux), Odyssey (3 niveaux) |
| Home Trust | Preferred Visa, Secured Visa |
| KOHO | Essential, Extra, Everything |
| MBNA | Rewards Platinum Plus, World Elite, Smart Cash, True Line |
| Meridian | Cashback Visa, Cashback Visa Infinite, Travel Rewards |
| National Bank | mycredit, Platinum, World, World Elite |
| Neo Financial | Mastercard, World, World Elite, Cathay |
| PC Financial | PC World Elite |
| RBC | Avion Visa Infinite, British Airways, Cash Back, ION, ION+ |
| Rogers | Red Mastercard, Red World Elite, Red World Legend |
| Scotiabank | Gold Amex, Passport Visa Infinite, Platinum Amex, Momentum |
| Simplii | Cash Back Visa |
| Tangerine | Money-Back, World Mastercard |
| TD | Cash Back, Cash Back Infinite, Low Rate, Platinum Travel, Rewards |
| Tims | Mastercard |
| Triangle | Mastercard, World Elite |
| WestJet RBC | Mastercard, World Elite |
| Wealthsimple | Visa Infinite |

</details>

---

## Stack technique

```
Backend     Flask 3.0 + Python 3.11
Templating  Jinja2
Frontend    HTML/CSS vanilla — aucun framework JS
Icônes      Font Awesome 6.5
Fonts       Inter (Google Fonts)
Déploiement Gunicorn — Railway / Render ready
```

---

## Lancer localement

```bash
# Cloner
git clone https://github.com/rayanerrr/carte.git
cd carte

# Installer les dépendances
pip install -r requirements.txt

# Lancer
python app.py
```

App disponible sur `http://localhost:5000`.

---

## Déployer sur Railway

```bash
# Installer Railway CLI (si pas déjà fait)
npm install -g @railway/cli

# Se connecter
railway login

# Créer le projet et déployer
railway init
railway up

# Générer une URL publique
railway domain
```

Le `Procfile` est déjà configuré :

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## Structure du projet

```
carte/
├── app.py                  # Routes Flask (questionnaire, résultats, API)
├── card_database.py        # 116 cartes avec tous leurs attributs
├── recommender.py          # Moteur de scoring + algorithme de match
├── questionnaire.py        # Définition des questions (10 sections)
├── requirements.txt
├── Procfile
├── templates/
│   ├── base.html           # Layout global + navbar
│   ├── index.html          # Page d'accueil
│   ├── questionnaire.html  # Formulaire multi-sections
│   ├── results.html        # Résultats personnalisés
│   └── cards.html          # Catalogue complet avec filtres
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## Valeurs CPP utilisées

*Source : Milesopedia & Prince of Travel (2025)*

| Programme | CPP optimisé | CPP rachat simple |
|---|---|---|
| Amex Membership Rewards | 2.0 ¢/pt | 1.2 ¢/pt |
| Aéroplan | 1.6 ¢/pt | 1.2 ¢/pt |
| Asia Miles | 1.5 ¢/pt | 1.2 ¢/pt |
| RBC Avion Elite | 1.5 ¢/pt | 1.0 ¢/pt |
| Scene+ | 1.0 ¢/pt | 1.0 ¢/pt |
| WestJet Dollars | 1.0 ¢/pt | 1.0 ¢/pt |
| PC Optimum | 1.0 ¢/pt | 1.0 ¢/pt |
| TD / BMO / CIBC Rewards | 0.8 ¢/pt | 0.8 ¢/pt |
| Cashback pur | 1.0 ¢/pt | 1.0 ¢/pt |

---

<div align="center">

*Les informations présentées sont à titre indicatif. Vérifiez toujours les conditions officielles des émetteurs.*

</div>
