# CarteIdéale

Recommandateur personnalisé de cartes de crédit canadiennes. Réponds à un questionnaire de 10 sections et obtiens les cartes qui correspondent vraiment à ton profil — pas juste les mieux notées en général.

## Fonctionnement

L'algorithme évalue chaque carte sur 8 dimensions pondérées dynamiquement selon tes réponses :

- **Rewards** — taux de récompenses ajustés à tes vraies dépenses (CPP réels de Milesopedia/Prince of Travel)
- **Frais** — compatibilité des frais annuels avec ton budget
- **Type de récompense** — cashback vs points selon ta préférence
- **Éligibilité** — revenu et score de crédit vs exigences de la carte
- **Assurances** — couvertures utiles selon ta situation (voyage, mobile, etc.)
- **Programme de points** — qualité réelle du programme (Amex MR, Aéroplan, Scene+, etc.)
- **Avantages voyage** — salons, NEXUS, bagage gratuit selon ta fréquence de voyage
- **Réseau** — compatibilité Visa/Mastercard/Amex avec tes commerces habituels (Costco, Maxi, etc.)

Des pénalités multiplicatives éliminent ou pénalisent fortement les cartes incompatibles (ex: Visa chez Costco, Amex chez Maxi/Provigo, carte voyage premium si tu ne voyages jamais).

## Base de données

116 cartes canadiennes couvrant : Amex, BMO, BRIM, CIBC, Desjardins, Home Trust, KOHO, MBNA, Meridian, National Bank, Neo Financial, PC Financial, RBC, Rogers, Scotiabank, Simplii, Tangerine, TD, Tims, Triangle, Wealthsimple, ATB et autres.

## Stack

- **Backend** : Python 3.11 / Flask
- **Frontend** : Jinja2, HTML/CSS vanilla, Font Awesome
- **Déploiement** : Gunicorn (Railway / Render compatible)

## Lancer localement

```bash
pip install -r requirements.txt
python app.py
```

L'app tourne sur `http://localhost:5000`.

## Déployer

Le projet est prêt pour Railway ou Render. Le `Procfile` et `requirements.txt` sont déjà configurés.

```bash
railway login
railway init
railway up
railway domain
```

## Structure

```
app.py              # Routes Flask
card_database.py    # 116 cartes avec tous leurs attributs
recommender.py      # Moteur de scoring et de recommandation
questionnaire.py    # Questions et types de champs
templates/          # Jinja2 HTML
static/             # CSS + JS
```
