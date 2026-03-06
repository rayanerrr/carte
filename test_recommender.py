#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement du système de recommandation
"""

from recommender import generate_recommendation_report
from questionnaire import UserProfile

def test_basic_profile():
    """Test avec un profil de base"""
    print("=== TEST 1: Profil de base ===")

    # Créer un profil utilisateur de test
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

    # Générer le rapport de recommandation
    report = generate_recommendation_report(profile)
    print(report)
    print("\n" + "="*60 + "\n")

def test_student_profile():
    """Test avec un profil d'étudiant"""
    print("=== TEST 2: Profil étudiant ===")

    # Créer un profil étudiant
    profile = UserProfile()
    profile.province = "Ontario"
    profile.age_range = "18–24 ans"
    profile.status = "Étudiant à temps plein"
    profile.income_personal = "Moins de 20 000 $"
    profile.income_household = "80 000–119 999 $"
    profile.credit_score = "Je ne sais pas"
    profile.denied_recently = "Non"

    # Dépenses mensuelles
    profile.spending_groceries = 300.0
    profile.spending_gas = 100.0
    profile.spending_restaurants = 200.0
    profile.spending_pharmacy = 50.0
    profile.spending_transport = 100.0
    profile.spending_subscriptions = 50.0
    profile.spending_entertainment = 150.0
    profile.spending_online = 200.0

    # Habitudes d'achat
    profile.grocery_stores = ["Walmart Supercentre", "Loblaws"]
    profile.gas_stations = ["Petro-Canada"]
    profile.uses_costco = "Rarement"
    profile.telecom_services = ["Fido"]

    # Voyages
    profile.travel_frequency = "Jamais ou presque"

    # Préférences
    profile.max_annual_fee = "0 $ (sans frais seulement)"
    profile.pays_balance_full = "Toujours"
    profile.points_comfort = "Je ne suis pas sûr(e) — expliquez la différence"
    profile.priorities = ["Frais annuels les plus bas possible", "Cashback simple sans gérer des points"]

    # Assurances
    profile.device_insurance = "Non"
    profile.home_owner = "Je vis chez mes parents ou un proche"
    profile.has_vehicle = "Non"

    # Style de vie
    profile.amazon_usage = "Rarement"
    profile.food_delivery = "1–3 fois par mois"

    # Étudiant
    profile.school_type = "Oui, université"

    # Final
    profile.timeline = "Dans 1–3 mois"
    profile.network_preference = "Aucune préférence"

    # Générer le rapport de recommandation
    report = generate_recommendation_report(profile)
    print(report)
    print("\n" + "="*60 + "\n")

def test_premium_profile():
    """Test avec un profil premium"""
    print("=== TEST 3: Profil premium ===")

    # Créer un profil premium
    profile = UserProfile()
    profile.province = "Colombie-Britannique"
    profile.age_range = "35–44 ans"
    profile.status = "Employé à temps plein"
    profile.income_personal = "150 000 $ et plus"
    profile.income_household = "200 000 $ et plus"
    profile.credit_score = "Excellent (760+)"
    profile.denied_recently = "Non"

    # Dépenses mensuelles
    profile.spending_groceries = 1000.0
    profile.spending_gas = 400.0
    profile.spending_restaurants = 800.0
    profile.spending_pharmacy = 200.0
    profile.spending_transport = 300.0
    profile.spending_subscriptions = 300.0
    profile.spending_entertainment = 500.0
    profile.spending_online = 600.0

    # Habitudes d'achat
    profile.grocery_stores = ["Costco", "Metro"]
    profile.gas_stations = ["Costco", "Esso"]
    profile.uses_costco = "Oui, régulièrement"
    profile.telecom_services = ["Rogers"]

    # Voyages
    profile.travel_frequency = "4–5 fois par an"
    profile.travel_destinations = "Partout dans le monde"
    profile.airlines = ["Air Canada", "British Airways"]
    profile.lounge_interest = "Oui, c'est très important pour moi"
    profile.nexus_interest = "Oui"

    # Préférences
    profile.max_annual_fee = "Jusqu'à 500 $"
    profile.pays_balance_full = "Toujours"
    profile.points_comfort = "Je suis à l'aise et j'aime optimiser mes points"
    profile.priorities = ["Avantages voyage (assurances, salons, miles)", "Maximiser les récompenses sur les achats du quotidien"]

    # Assurances
    profile.device_insurance = "Non"
    profile.home_owner = "Propriétaire"
    profile.has_vehicle = "Oui, 2 véhicules ou plus"

    # Style de vie
    profile.amazon_usage = "Oui, je fais la majorité de mes achats en ligne via Amazon"
    profile.food_delivery = "Presque tous les jours"
    profile.charity_donations = "Oui, régulièrement"

    # Final
    profile.timeline = "Dans les 30 prochains jours"
    profile.network_preference = "American Express"

    # Générer le rapport de recommandation
    report = generate_recommendation_report(profile)
    print(report)
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    print("🧪 TEST DU SYSTÈME DE RECOMMANDATION DE CARTES DE CRÉDIT")
    print("=" * 60)

    # Exécuter les tests
    test_basic_profile()
    test_student_profile()
    test_premium_profile()

    print("✅ Tests terminés avec succès!")