"""
Application Web - Recommandateur de Cartes de Crédit Canadiennes
Flask app avec questionnaire multi-étapes et interface moderne
"""

import os
import json
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
