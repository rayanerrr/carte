#!/usr/bin/env python3
"""
Script de débogage pour le moteur de recommandation
"""

from recommender import RecommendationEngine
from questionnaire import UserProfile

def debug_recommendation(profile, profile_name):
    """Débogue le moteur de recommandation pour un profil donné"""
    print(f"=== DÉBOGAGE: {profile_name} ===")

    # Afficher quelques informations du profil
    print(f"Score de crédit: {profile.credit_score}")
    print(f"Revenu personnel: {profile.income_personal}")
    print(f"Préférence réseau: {profile.network_preference}")
    print(f"Frais annuels max: {profile.max_annual_fee}")

    # Créer le moteur de recommandation
    engine = RecommendationEngine(profile)

    # Vérifier les cartes éligibles
    eligible_cards = engine._filter_eligible_cards()
    print(f"Cartes éligibles: {len(eligible_cards)}")

    # Afficher les cartes éligibles
    for card in eligible_cards:
        print(f"  - {card.name}")

    # Générer les recommandations
    recommendations = engine.recommend(num_results=3)
    print(f"Recommandations générées: {len(recommendations)}")

    # Afficher les recommandations
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec.card.name} (Score: {rec.score}, ROI: {rec.annual_roi}$)")

    print()

def test_debug_profile():
    """Test avec un profil de débogage"""
    profile = UserProfile()
    profile.province = "Québec"
    profile.age_range = "25–34 ans"
    profile.status = "Employé à temps plein"
    profile.income_personal = "80 000–99 999 $"
    profile.income_household = "80 000–119 999 $"
    profile.credit_score = "Très bon (720–759)"
    profile.denied_recently = "Non"

    # Dépenses mensuelles
    profile.spending_groceries = 600.0
    profile.spending_gas = 200.0
    profile.spending_restaurants = 300.0
    profile.spending_pharmacy = 100.0
    profile.spending_transport = 150.0
    profile.spending_subscriptions = 100.0
    profile.spending_entertainment = 200.0
    profile.spending_online = 400.0

    # Habitudes d'achat
    profile.grocery_stores = ["Metro", "IGA"]
    profile.gas_stations = ["Esso", "Shell"]
    profile.uses_costco = "Oui, occasionnellement"
    profile.telecom_services = ["Rogers"]

    # Voyages
    profile.travel_frequency = "2–3 fois par an"
    profile.travel_destinations = "Aux États-Unis principalement"
    profile.airlines = ["Air Canada", "WestJet"]
    profile.lounge_interest = "Oui, si c'est inclus dans les avantages"

    # Préférences
    profile.max_annual_fee = "Jusqu'à 150 $"
    profile.pays_balance_full = "Toujours"
    profile.points_comfort = "Je préfère nettement le cashback — simple et direct"
    profile.priorities = ["Maximiser les récompenses sur les achats du quotidien", "Cashback simple sans gérer des points"]

    # Assurances
    profile.device_insurance = "Non"
    profile.home_owner = "Locataire"
    profile.has_vehicle = "Oui, 1 véhicule"

    # Style de vie
    profile.amazon_usage = "Oui, mais c'est un parmi plusieurs sites"
    profile.food_delivery = "1–2 fois par semaine"

    # Final
    profile.timeline = "Dans les 30 prochains jours"
    profile.network_preference = "American Express"

    debug_recommendation(profile, "Profil de test")

if __name__ == "__main__":
    test_debug_profile()