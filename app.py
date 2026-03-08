"""
Application Web - Recommandateur de Cartes de Crédit Canadiennes
Flask app avec questionnaire multi-étapes et interface moderne
"""

import io
import os
import re
from collections import defaultdict
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from questionnaire import UserProfile, QuestionnaireEngine, QuestionType
from recommender import RecommendationEngine
from card_database import get_all_cards

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "creditcard-recommender-2025-secret")

SECTIONS = [
    {"id": 1,  "name": "Profil de base",          "icon": "user",           "questions": ["province", "age", "status", "income_personal", "income_household", "credit_score", "denied_recently"]},
    {"id": 2,  "name": "Situation bancaire",        "icon": "building-columns","questions": ["banks", "open_to_new_bank"]},
    {"id": 3,  "name": "Cartes actuelles",          "icon": "credit-card",    "questions": ["has_cards", "num_cards"]},
    {"id": 4,  "name": "Dépenses mensuelles",       "icon": "dollar-sign",    "questions": ["total_monthly", "spending_groceries", "spending_gas", "spending_restaurants", "spending_pharmacy", "spending_transport", "spending_subscriptions", "spending_entertainment", "spending_online"]},
    {"id": 5,  "name": "Habitudes d'achat",         "icon": "shopping-cart",  "questions": ["grocery_stores", "gas_stations", "uses_costco", "uses_walmart", "telecom_services"]},
    {"id": 6,  "name": "Voyages",                   "icon": "plane",          "questions": ["travel_frequency", "travel_destinations", "travel_budget", "airlines", "lounge_interest", "reward_preference"]},
    {"id": 7,  "name": "Préférences",               "icon": "sliders",        "questions": ["max_annual_fee", "pays_balance_full", "has_debt", "points_comfort", "desired_num_cards", "open_to_multiple", "priorities"]},
    {"id": 8,  "name": "Assurances & style de vie","icon": "shield",          "questions": ["device_insurance", "home_owner", "has_vehicle", "amazon_usage", "amazon_prime", "food_delivery"]},
    {"id": 9,  "name": "Optimisation",              "icon": "chart-line",     "questions": ["spending_foreign", "employer_insurance", "points_valuation", "card_strategy"]},
    {"id": 10, "name": "Finalisation",              "icon": "flag-checkered", "questions": ["timeline", "network_preference", "must_have_feature"]},
]


def build_profile_from_session() -> UserProfile:
    """Reconstruit un UserProfile depuis les données de session"""
    profile = UserProfile()
    answers = session.get("answers", {})

    field_map = {
        "province": "province",
        "age": "age_range",
        "status": "status",
        "income_personal": "income_personal",
        "income_household": "income_household",
        "credit_score": "credit_score",
        "denied_recently": "denied_recently",
        "banks": "banks",
        "open_to_new_bank": "open_to_new_bank",
        "has_cards": "has_cards",
        "num_cards": "num_cards",
        "total_monthly": "total_monthly",
        "spending_groceries": "spending_groceries",
        "spending_gas": "spending_gas",
        "spending_restaurants": "spending_restaurants",
        "spending_pharmacy": "spending_pharmacy",
        "spending_transport": "spending_transport",
        "spending_subscriptions": "spending_subscriptions",
        "spending_entertainment": "spending_entertainment",
        "spending_online": "spending_online",
        "grocery_stores": "grocery_stores",
        "gas_stations": "gas_stations",
        "uses_costco": "uses_costco",
        "uses_walmart": "uses_walmart",
        "telecom_services": "telecom_services",
        "travel_frequency": "travel_frequency",
        "travel_destinations": "travel_destinations",
        "travel_budget": "travel_budget",
        "airlines": "airlines",
        "lounge_interest": "lounge_interest",
        "reward_preference": "reward_preference",
        "max_annual_fee": "max_annual_fee",
        "pays_balance_full": "pays_balance_full",
        "has_debt": "has_debt",
        "points_comfort": "points_comfort",
        "desired_num_cards": "desired_num_cards",
        "open_to_multiple": "open_to_multiple",
        "priorities": "priorities",
        "device_insurance": "device_insurance",
        "home_owner": "home_owner",
        "has_vehicle": "has_vehicle",
        "amazon_usage": "amazon_usage",
        "amazon_prime": "amazon_prime",
        "food_delivery": "food_delivery",
        "spending_foreign": "spending_foreign",
        "employer_insurance": "employer_insurance",
        "points_valuation": "points_valuation",
        "card_strategy": "card_strategy",
        "timeline": "timeline",
        "network_preference": "network_preference",
        "must_have_feature": "must_have_feature",
    }

    numeric_fields = {
        "spending_groceries", "spending_gas", "spending_restaurants",
        "spending_pharmacy", "spending_transport", "spending_subscriptions",
        "spending_entertainment", "spending_online", "spending_foreign"
    }

    bool_fields = {"has_cards"}

    for q_id, attr in field_map.items():
        if q_id in answers:
            val = answers[q_id]
            if q_id in numeric_fields:
                try:
                    setattr(profile, attr, float(val) if val else 0.0)
                except (ValueError, TypeError):
                    setattr(profile, attr, 0.0)
            elif q_id in bool_fields:
                setattr(profile, attr, val == "Oui")
            else:
                setattr(profile, attr, val)

    return profile


def get_questions_for_section(section_id: int) -> list:
    """Retourne les questions pour une section donnée"""
    engine = QuestionnaireEngine()
    section = next((s for s in SECTIONS if s["id"] == section_id), None)
    if not section:
        return []

    questions = []
    for q_id in section["questions"]:
        q = next((q for q in engine.questions if q.id == q_id), None)
        if q:
            questions.append(q)
    return questions


@app.route("/")
def index():
    session.clear()
    cards = get_all_cards()
    return render_template("index.html", total_cards=len(cards))


@app.route("/questionnaire", methods=["GET"])
def questionnaire_start():
    session.clear()
    session["answers"] = {}
    return redirect(url_for("questionnaire_section", section_id=1))


@app.route("/questionnaire/<int:section_id>", methods=["GET", "POST"])
def questionnaire_section(section_id: int):
    if "answers" not in session:
        return redirect(url_for("questionnaire_start"))

    if section_id < 1 or section_id > len(SECTIONS):
        return redirect(url_for("results"))

    section = SECTIONS[section_id - 1]

    if request.method == "POST":
        # Sauvegarder les réponses de cette section
        answers = session.get("answers", {})
        questions = get_questions_for_section(section_id)

        for q in questions:
            field_name = q.id
            if q.question_type == QuestionType.MULTI_CHOICE:
                val = request.form.getlist(field_name)
                answers[field_name] = val if val else []
            elif q.question_type == QuestionType.NUMERIC:
                raw = request.form.get(field_name, "0").strip()
                try:
                    answers[field_name] = float(raw) if raw else 0.0
                except ValueError:
                    answers[field_name] = 0.0
            else:
                val = request.form.get(field_name, "")
                if val:
                    answers[field_name] = val

        session["answers"] = answers

        # Aller à la prochaine section ou aux résultats
        if section_id < len(SECTIONS):
            return redirect(url_for("questionnaire_section", section_id=section_id + 1))
        else:
            return redirect(url_for("results"))

    # GET - Afficher la section
    questions = get_questions_for_section(section_id)
    current_answers = session.get("answers", {})
    progress_pct = int((section_id - 1) / len(SECTIONS) * 100)

    # Gérer la visibilité conditionnelle côté serveur
    travel_active = current_answers.get("travel_frequency", "") not in ["Jamais ou presque", ""]

    return render_template(
        "questionnaire.html",
        section=section,
        section_id=section_id,
        total_sections=len(SECTIONS),
        sections=SECTIONS,
        questions=questions,
        current_answers=current_answers,
        progress_pct=progress_pct,
        travel_active=travel_active,
        QuestionType=QuestionType,
    )


@app.route("/resultats")
def results():
    if "answers" not in session:
        return redirect(url_for("index"))

    profile = build_profile_from_session()
    engine = RecommendationEngine(profile)
    recommendations = engine.recommend(num_results=5)

    # Calculer les dépenses totales
    spending = {
        "Épicerie": profile.spending_groceries,
        "Essence": profile.spending_gas,
        "Restaurants": profile.spending_restaurants,
        "Pharmacie": profile.spending_pharmacy,
        "Transport": profile.spending_transport,
        "Abonnements": profile.spending_subscriptions,
        "Divertissement": profile.spending_entertainment,
        "Achats en ligne": profile.spending_online,
    }
    total_monthly = sum(spending.values())

    return render_template(
        "results.html",
        recommendations=recommendations,
        profile=profile,
        spending=spending,
        total_monthly=total_monthly,
    )


@app.route("/cartes")
def all_cards():
    """Page listant toutes les cartes"""
    cards = get_all_cards()
    network_filter = request.args.get("network", "")
    tier_filter = request.args.get("tier", "")
    fee_filter = request.args.get("max_fee", "")

    filtered = cards
    if network_filter:
        filtered = [c for c in filtered if c.network.value == network_filter]
    if tier_filter:
        filtered = [c for c in filtered if c.tier.value == tier_filter]
    if fee_filter:
        try:
            max_fee = float(fee_filter)
            filtered = [c for c in filtered if c.annual_fee <= max_fee]
        except ValueError:
            pass

    filtered.sort(key=lambda c: (-c.welcome_bonus, c.annual_fee))

    return render_template("cards.html", cards=filtered, total=len(cards),
                           network_filter=network_filter, tier_filter=tier_filter)


@app.route("/api/cards")
def api_cards():
    """API JSON des cartes"""
    cards = get_all_cards()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "issuer": c.issuer,
        "network": c.network.value,
        "annual_fee": c.annual_fee,
        "base_rate": c.base_rate,
        "welcome_bonus": c.welcome_bonus,
        "reward_program": c.reward_program,
    } for c in cards])


# ---------------------------------------------------------------------------
# Classificateur de relevés — ML (TF-IDF + Régression Logistique)
# ---------------------------------------------------------------------------

_CLASSIFIER = None  # chargé au premier appel


def _load_classifier():
    """Charge le modèle ML depuis le disque, ou l'entraîne si absent."""
    global _CLASSIFIER
    if _CLASSIFIER is not None:
        return _CLASSIFIER

    import joblib
    from pathlib import Path
    pkl = Path(__file__).parent / "merchant_classifier.pkl"

    if not pkl.exists():
        app.logger.info("merchant_classifier.pkl absent — entraînement en cours...")
        from train_classifier import train
        train()

    _CLASSIFIER = joblib.load(pkl)
    app.logger.info("Classifieur ML chargé.")
    return _CLASSIFIER


def _classify_description(clf, description: str) -> str:
    """Prédit la catégorie d'une description de transaction.
    Retourne None si la confiance est trop faible (<35 %)."""
    desc = description.upper()
    proba = clf.predict_proba([desc])[0]
    best_idx = proba.argmax()
    confidence = proba[best_idx]
    if confidence < 0.35:
        return None
    return clf.classes_[best_idx]

_SKIP_KEYWORDS = [
    "balance", "solde", "total", "paiement", "payment", " credit ", " crédit ",
    "interest", "intérêt", "frais annuel", "annual fee", "minimum payment",
    "new balance", "previous balance", "opening balance", "closing balance",
    "interest charge", "frais de change", "transfert", "transfer",
    "mise en garde", "statement", "relevé",
]

_STORE_MAP = {
    "grocery_stores": [
        ("Maxi",       ["maxi"]),
        ("IGA",        ["iga "]),
        ("Metro",      ["metro "]),
        ("Provigo",    ["provigo"]),
        ("Loblaws",    ["loblaws", "loblaw"]),
        ("Costco",     ["costco"]),
        ("Walmart",    ["walmart"]),
        ("Super C",    ["super-c", "super c"]),
        ("Sobeys",     ["sobeys"]),
        ("FreshCo",    ["freshco"]),
        ("No Frills",  ["no frills"]),
        ("Farm Boy",   ["farm boy"]),
    ],
    "gas_stations": [
        ("Petro-Canada",   ["petro-canada", "petrocanada", "petro canada"]),
        ("Esso",           ["esso"]),
        ("Shell",          ["shell"]),
        ("Ultramar",       ["ultramar"]),
        ("Canadian Tire",  ["canadian tire gas"]),
        ("Pioneer",        ["pioneer"]),
        ("Irving",         ["irving oil"]),
    ],
    "telecom_services": [
        ("Bell",           ["bell canada", "bell mobility", "bell fibe"]),
        ("Vidéotron",      ["videotron", "vidéotron"]),
        ("TELUS",          ["telus "]),
        ("Rogers",         ["rogers "]),
        ("Fido",           ["fido "]),
        ("Koodo",          ["koodo"]),
        ("Virgin",         ["virgin mobile", "virgin plus"]),
        ("Freedom Mobile", ["freedom mobile"]),
        ("Public Mobile",  ["public mobile"]),
    ],
}

_DATE_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    r"|Janv?|F[eé]vr?|Mars|Avr|Mai|Juin|Juil|A[oô]ut|Sept?|Oct|Nov|D[eé]c)\w*\.?\s+\d{1,2}(?:\s+\d{4})?"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
    r"|Janv?|F[eé]vr?|Mars|Avr|Mai|Juin|Juil|A[oô]ut|Sept?|Oct|Nov|D[eé]c)\w*\.?(?:\s+\d{4})?)",
    re.IGNORECASE,
)

_AMOUNT_RE = re.compile(r"([\d,]{1,6}\.\d{2})\s*(?:CR|DB|cr|db)?\s*$")


def _extraire_texte(files):
    """Extrait le texte brut de tous les fichiers uploadés (PDF ou texte)."""
    try:
        import pdfplumber
    except ImportError:
        raise ValueError("pdfplumber n'est pas installé. Relancez : pip install pdfplumber")

    all_text = ""
    for f in files:
        if not f or f.filename == "":
            continue
        data = f.read()
        fname = f.filename.lower()

        if fname.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        all_text += t + "\n"
        elif fname.endswith((".txt", ".csv")):
            all_text += data.decode("utf-8", errors="ignore") + "\n"
        elif fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
            raise ValueError(
                "Les images ne sont pas supportées sans OCR. "
                "Téléversez des fichiers PDF ou texte (.txt)."
            )

    if not all_text.strip():
        raise ValueError(
            "Aucun texte extrait. Assurez-vous que vos PDFs ne sont pas scannés/image."
        )
    return all_text


def _extraire_transactions(text):
    """Extrait les lignes de transaction (description + montant)."""
    transactions = []
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 8:
            continue

        amount_m = _AMOUNT_RE.search(line)
        if not amount_m:
            continue

        try:
            amount = float(amount_m.group(1).replace(",", ""))
        except ValueError:
            continue

        if amount <= 0 or amount > 9999:
            continue

        description = line[: amount_m.start()].strip()
        date_m = _DATE_RE.match(description)
        if date_m:
            description = description[date_m.end():].strip()

        if len(description) < 3:
            continue

        desc_lower = description.lower()
        if any(kw in desc_lower for kw in _SKIP_KEYWORDS):
            continue

        transactions.append({"description": description, "amount": amount})

    return transactions


def _detect_months(text):
    """Estime le nombre de mois couverts dans le texte."""
    month_years = set()

    for m in re.finditer(r"\b(\d{4})-(\d{2})-\d{2}\b", text):
        month_years.add((m.group(1), m.group(2)))

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05",
        "jun": "06", "jul": "07", "aug": "08", "sep": "09", "oct": "10",
        "nov": "11", "dec": "12",
        "janv": "01", "févr": "02", "fevr": "02", "mars": "03", "avr": "04",
        "mai": "05", "juin": "06", "juil": "07", "août": "08", "aout": "08",
        "sept": "09",
    }
    pattern = r"\b(" + "|".join(month_map.keys()) + r")[a-z]*\.?\s+(\d{4})\b"
    for m in re.finditer(pattern, text, re.IGNORECASE):
        key = m.group(1).lower()[:4]
        if key in month_map:
            month_years.add((m.group(2), month_map[key]))

    return max(1, len(month_years))


def _detect_stores(text_lower):
    """Détecte les commerces spécifiques présents dans le texte."""
    detected = {"grocery_stores": [], "gas_stations": [], "telecom_services": []}
    for cat, stores in _STORE_MAP.items():
        for name, keywords in stores:
            if any(kw in text_lower for kw in keywords):
                detected[cat].append(name)
    return detected


def _detect_food_delivery(text_lower):
    kws = ["ubereats", "uber eats", "doordash", "door dash",
           "skip the dishes", "skipthedishes", "foodora"]
    total = sum(text_lower.count(kw) for kw in kws)
    if total == 0:
        return "Rarement"
    if total >= 8:
        return "Presque tous les jours"
    if total >= 4:
        return "1–2 fois par semaine"
    return "1–3 fois par mois"


def _analyser_releves_local(files):
    """
    Analyse des relevés de carte de crédit sans API externe.
    Extraction PDF + classifieur ML (TF-IDF + Régression Logistique).
    """
    text = _extraire_texte(files)
    text_lower = text.lower()

    transactions = _extraire_transactions(text)
    months = _detect_months(text)

    clf = _load_classifier()

    totals = defaultdict(float)
    unclassified_amount = 0.0
    for t in transactions:
        cat = _classify_description(clf, t["description"])
        if cat:
            totals[cat] += t["amount"]
        else:
            unclassified_amount += t["amount"]

    # Les non-classifiés vont en partie dans achats divers
    totals["spending_online"] += unclassified_amount * 0.35

    stores = _detect_stores(text_lower)

    # Fréquence Costco/Walmart selon nombre d'occurrences
    def _freq(keyword):
        n = text_lower.count(keyword)
        if n == 0:
            return "Jamais"
        if n >= 4:
            return "Oui, régulièrement"
        return "Oui, occasionnellement"

    amazon_n = text_lower.count("amazon")
    if amazon_n == 0:
        amazon_usage = "Jamais"
    elif amazon_n >= 5:
        amazon_usage = "Oui, je fais la majorité de mes achats en ligne via Amazon"
    else:
        amazon_usage = "Oui, mais c'est un parmi plusieurs sites"

    cats = [
        "spending_groceries", "spending_gas", "spending_restaurants",
        "spending_pharmacy", "spending_transport", "spending_subscriptions",
        "spending_entertainment", "spending_online",
    ]

    result = {cat: round(totals[cat] / months) for cat in cats}
    result.update({
        "spending_foreign": 0,
        "grocery_stores":   stores["grocery_stores"],
        "gas_stations":     stores["gas_stations"],
        "telecom_services": stores["telecom_services"],
        "uses_costco":      _freq("costco"),
        "uses_walmart":     _freq("walmart"),
        "amazon_usage":     amazon_usage,
        "amazon_prime":     "amazon prime" in text_lower,
        "food_delivery":    _detect_food_delivery(text_lower),
        "months_analyzed":  months,
        "notes": (
            f"{len(transactions)} transactions détectées sur {months} mois. "
            "Vérifiez les montants — certains commerces peu connus peuvent être mal classifiés."
        ),
    })
    return result


@app.route("/analyser-releves", methods=["GET", "POST"])
def analyser_releves():
    """Page d'upload et d'analyse automatique des relevés de carte de crédit."""
    if request.method == "GET":
        session.clear()
        session["answers"] = {}
        return render_template("upload_releve.html")

    files = request.files.getlist("releves")
    if not files or all(f.filename == "" for f in files):
        return render_template("upload_releve.html", error="Veuillez sélectionner au moins un relevé.")

    try:
        result = _analyser_releves_local(files)

        # Pré-remplir la session avec les données extraites
        answers = session.get("answers", {})

        champs_numeriques = [
            "spending_groceries", "spending_gas", "spending_restaurants",
            "spending_pharmacy", "spending_transport", "spending_subscriptions",
            "spending_entertainment", "spending_online",
        ]
        for champ in champs_numeriques:
            if champ in result and result[champ] is not None:
                answers[champ] = float(result[champ])

        if result.get("spending_foreign"):
            answers["spending_foreign"] = float(result["spending_foreign"])

        for champ_liste in ["grocery_stores", "gas_stations", "telecom_services"]:
            if result.get(champ_liste):
                answers[champ_liste] = result[champ_liste]

        for champ_str in ["uses_costco", "uses_walmart", "amazon_usage", "food_delivery"]:
            if result.get(champ_str):
                answers[champ_str] = result[champ_str]

        if result.get("amazon_prime") is not None:
            answers["amazon_prime"] = "Oui" if result["amazon_prime"] else "Non"

        total_spending = sum(float(result.get(c, 0) or 0) for c in champs_numeriques)
        answers["spending_auto_filled"] = True

        session["answers"] = answers
        session["spending_auto"] = result

        return render_template(
            "upload_releve.html",
            result=result,
            success=True,
            total_spending=round(total_spending),
        )

    except Exception as e:
        app.logger.error(f"Erreur analyse relevés: {e}")
        return render_template(
            "upload_releve.html",
            error=f"Erreur lors de l'analyse : {str(e)}",
        )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
