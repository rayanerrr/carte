#!/usr/bin/env python3
"""
Script pour tester avec un profil corrigé
"""

from recommender import RecommendationEngine, generate_recommendation_report
from questionnaire import UserProfile

def test_corrected_profile():
    """Test avec un profil corrigé"""
    print("=== TEST AVEC PROFIL CORRIGÉ ===")

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

    # Habitudes d'achat - changer l'utilisation de Costco
    profile.grocery_stores = ["Metro", "IGA"]
    profile.gas_stations = ["Esso", "Shell"]
    profile.uses_costco = "Rarement"  # Changement ici
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

    # Tester le moteur de recommandation
    engine = RecommendationEngine(profile)

    # Vérifier les cartes éligibles
    eligible_cards = engine._filter_eligible_cards()
    print(f"Cartes éligibles: {len(eligible_cards)}")

    for card in eligible_cards:
        print(f"  - {card.name}")

    # Générer le rapport complet
    print("\n=== RAPPORT DE RECOMMANDATION ===")
    report = generate_recommendation_report(profile)
    print(report)

if __name__ == "__main__":
    test_corrected_profile()