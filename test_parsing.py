#!/usr/bin/env python3
"""
Script pour tester les fonctions de parsing
"""

from recommender import RecommendationEngine
from questionnaire import UserProfile

def test_parsing():
    """Teste les fonctions de parsing"""
    profile = UserProfile()
    profile.credit_score = "Très bon (720–759)"
    profile.income_personal = "80 000–99 999 $"
    profile.income_household = "80 000–119 999 $"
    profile.max_annual_fee = "Jusqu'à 150 $"

    engine = RecommendationEngine(profile)

    # Tester le parsing du score de crédit
    credit_score = engine._parse_credit_score()
    print(f"Score de crédit parsé: {credit_score}")

    # Tester le parsing du revenu
    income_personal = engine._parse_income(profile.income_personal)
    income_household = engine._parse_income(profile.income_household)
    print(f"Revenu personnel parsé: {income_personal}")
    print(f"Revenu du ménage parsé: {income_household}")

    # Tester le parsing des frais maximaux
    max_fee = engine._parse_max_fee()
    print(f"Frais maximaux parsés: {max_fee}")

    # Vérifier les cartes individuellement
    print("\n=== VÉRIFICATION INDIVIDUELLE DES CARTES ===")
    from card_database import get_all_cards
    cards = get_all_cards()

    for card in cards:
        print(f"\nCarte: {card.name}")
        print(f"  Score de crédit minimum: {card.min_credit_score}")
        print(f"  Revenu personnel minimum: {card.min_income_personal}")
        print(f"  Frais annuels: {card.annual_fee}")
        print(f"  Compatible avec Costco: {card.compatible_with_costco}")

        # Vérifier les conditions
        if credit_score < card.min_credit_score:
            print(f"  ❌ Score de crédit insuffisant ({credit_score} < {card.min_credit_score})")
        else:
            print(f"  ✅ Score de crédit suffisant ({credit_score} >= {card.min_credit_score})")

if __name__ == "__main__":
    test_parsing()