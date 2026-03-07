"""
Application Web - Recommandateur de Cartes de Crédit Canadiennes
Flask app avec questionnaire multi-étapes et interface moderne
"""

import os
import re
import json
import base64
import anthropic
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


def _analyser_releves_avec_claude(files):
    """
    Analyse des relevés de carte de crédit (PDF/images/texte) avec Claude Opus.
    Retourne un dict avec les dépenses mensuelles moyennes par catégorie
    et des informations sur les commerces habituels.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    content = []
    uploaded_file_ids = []

    for f in files:
        if not f or f.filename == "":
            continue
        data = f.read()
        fname = f.filename.lower()

        if fname.endswith(".pdf"):
            uploaded = client.beta.files.upload(
                file=(f.filename, data, "application/pdf"),
            )
            uploaded_file_ids.append(uploaded.id)
            content.append({
                "type": "document",
                "source": {"type": "file", "file_id": uploaded.id},
            })
        elif fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
            mt = "image/png" if fname.endswith(".png") else "image/jpeg"
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mt,
                    "data": base64.standard_b64encode(data).decode("utf-8"),
                },
            })
        else:
            content.append({
                "type": "text",
                "text": "Relevé de carte de crédit:\n" + data.decode("utf-8", errors="ignore"),
            })

    if not content:
        raise ValueError("Aucun fichier valide fourni.")

    content.append({
        "type": "text",
        "text": (
            "Analysez ce ou ces relevé(s) de carte de crédit canadien(s) et extrayez les "
            "dépenses MENSUELLES MOYENNES par catégorie.\n\n"
            "Réponds UNIQUEMENT avec un objet JSON valide ayant exactement ces champs "
            "(aucun texte avant ou après le JSON) :\n"
            "{\n"
            '  "spending_groceries": <montant CAD mensuel moyen - épicerie, supermarché>,\n'
            '  "spending_gas": <montant CAD mensuel moyen - essence, carburant>,\n'
            '  "spending_restaurants": <montant CAD mensuel moyen - restaurants, cafés, livraison repas (UberEats, DoorDash, Skip)>,\n'
            '  "spending_pharmacy": <montant CAD mensuel moyen - pharmacie (Jean Coutu, Pharmaprix, etc.)>,\n'
            '  "spending_transport": <montant CAD mensuel moyen - transport (Uber, taxi, STM/OPUS, stationnement)>,\n'
            '  "spending_subscriptions": <montant CAD mensuel moyen - abonnements (téléphone, internet, Netflix, Spotify, Disney+, etc.)>,\n'
            '  "spending_entertainment": <montant CAD mensuel moyen - divertissement (cinéma, événements, sports, etc.)>,\n'
            '  "spending_online": <montant CAD mensuel moyen - achats en ligne (Amazon, boutiques web, etc.)>,\n'
            '  "spending_foreign": <montant CAD mensuel moyen - transactions en devises étrangères (USD/EUR/etc.) - converti en CAD à 1.38 si nécessaire>,\n'
            '  "grocery_stores": [liste des épiceries identifiées, ex: ["Maxi","IGA","Metro"]],\n'
            '  "gas_stations": [liste des stations-essence, ex: ["Petro-Canada","Esso"]],\n'
            '  "telecom_services": [liste des télécoms, ex: ["Fido","Bell","TELUS"]],\n'
            '  "uses_costco": "Oui, régulièrement" | "Oui, occasionnellement" | "Rarement" | "Jamais",\n'
            '  "uses_walmart": "Oui, régulièrement" | "Oui, occasionnellement" | "Rarement" | "Jamais",\n'
            '  "amazon_usage": "Oui, je fais la majorité de mes achats en ligne via Amazon" | "Oui, mais c\'est un parmi plusieurs sites" | "Rarement" | "Jamais",\n'
            '  "amazon_prime": true | false,\n'
            '  "food_delivery": "Presque tous les jours" | "1–2 fois par semaine" | "1–3 fois par mois" | "Rarement",\n'
            '  "months_analyzed": <nombre entier de mois couverts par les relevés>,\n'
            '  "notes": "<courte note sur la fiabilité de l\'analyse>"\n'
            "}\n\n"
            "Règles importantes :\n"
            "- Si plusieurs mois : calculez la MOYENNE mensuelle, pas le total\n"
            "- Ignorez les remboursements/paiements de solde/frais annuels de carte\n"
            "- Arrondissez chaque montant à l'entier le plus proche\n"
            "- Si une catégorie n'apparaît pas : mets 0\n"
        ),
    })

    use_files = bool(uploaded_file_ids)
    create_kwargs = {
        "model": "claude-opus-4-6",
        "max_tokens": 2048,
        "thinking": {"type": "adaptive"},
        "system": (
            "Tu es un expert-comptable spécialisé en analyse de relevés de carte de crédit "
            "canadiens. Tu réponds UNIQUEMENT avec du JSON valide, sans aucun texte avant ou après."
        ),
        "messages": [{"role": "user", "content": content}],
    }

    if use_files:
        response = client.beta.messages.create(**create_kwargs, betas=["files-api-2025-04-14"])
    else:
        response = client.messages.create(**create_kwargs)

    # Cleanup uploaded files
    for fid in uploaded_file_ids:
        try:
            client.beta.files.delete(fid)
        except Exception:
            pass

    # Extract JSON from response
    raw = next((b.text for b in response.content if b.type == "text"), "")
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(raw)


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
        result = _analyser_releves_avec_claude(files)

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
