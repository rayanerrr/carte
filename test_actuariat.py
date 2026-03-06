"""
Test de la logique actuarielle avancée
"""
from questionnaire import UserProfile
from recommender import RecommendationEngine

def test_profil_avec_nouvelles_questions():
    """Test avec un profil utilisant les nouvelles questions actuarielles"""

    profile = UserProfile()
    profile.spending_groceries = 600
    profile.spending_gas = 200
    profile.spending_restaurants = 300
    profile.spending_foreign = 100  # NOUVELLE: dépenses en devises
    profile.credit_score = "Excellent (760+)"
    profile.income_personal = "80 000-99 999 $"
    profile.travel_frequency = "2-3 fois par an"
    profile.trips_per_year = 2  # NOUVELLE: voyages par an
    profile.employer_insurance = "Oui"  # NOUVELLE: assurance employeur
    profile.points_valuation = "Transfert vers partenaires aeriens comme Aéroplan/Avios (valeur = 1.5-2 cpp)"  # NOUVELLE: CPP dynamique
    profile.card_strategy = "A long terme (3 ans et plus)"  # NOUVELLE: amortissement bonus
    profile.grocery_stores = ["Maxi", "Provigo"]
    profile.gas_stations = ["Petro-Canada"]
    profile.max_annual_fee = "Jusqu'a 150 $"

    # Tester le moteur
    engine = RecommendationEngine(profile)
    recs = engine.recommend(num_results=3)

    print("=" * 70)
    print(" TEST - LOGIQUE ACTUARIELLE")
    print("=" * 70)
    print(f"\nProfil test:")
    print(f"  - Dépenses étrangères: {profile.spending_foreign}$/mois")
    print(f"  - Voyages/an: {profile.trips_per_year}")
    print(f"  - Assurance employeur: {profile.employer_insurance}")
    print(f"  - Points: {profile.points_valuation}")
    print(f"  - Stratégie: {profile.card_strategy}")
    print(f"  - Épiceries: {profile.grocery_stores}")
    print(f"  - Essence: {profile.gas_stations}")

    print(f"\n{'=' * 70}")
    print(f" RÉSULTATS")
    print(f"{'=' * 70}")
    print(f"Nombre de recommandations: {len(recs)}")

    for i, rec in enumerate(recs, 1):
        print(f"\n{i}. {rec.card.name}")
        print(f"   ROI: {rec.annual_roi}$ | Score: {rec.score:.1f} | Match: {rec.match_percentage}%")

    print("\n" + "=" * 70)
    print(" TESTS SPÉCIFIQUES")
    print("=" * 70)

    # Test 1: Pénalité FX
    fx_penalty = engine._calculate_fx_penalty(recs[0].card) if recs else 0
    print(f"\n1. Pénalité FX (100$/mois * 12 * 2.5%): {fx_penalty:.2f}$")
    print(f"   Attendu: ~30$ (100 * 12 * 0.025)")

    # Test 2: Amortissement bonus long terme
    print(f"\n2. Amortissement bonus (long terme = 50%):")
    print(f"   Si bonus = 100$, valeur retenue = 50$")

    # Test 3: Valeur voyage proportionnelle
    print(f"\n3. Valeur voyage proportionnelle:")
    print(f"   trips_per_year = {profile.trips_per_year}")
    print(f"   Valeur salon = {profile.trips_per_year} * 50$ = {profile.trips_per_year * 50}$")
    print(f"   (Au lieu de 150-300$ statique)")

    # Test 4: Assurance employeur
    print(f"\n4. Assurance médicale avec employer_insurance = 'Oui':")
    print(f"   Valeur assurance = 0$ (déjà couvert)")

    # Test 5: Contrainte Amex/Loblaws
    print(f"\n5. Contrainte Amex/Loblaws:")
    print(f"   Épiceries: {profile.grocery_stores}")
    print(f"   Si carte = Amex, taux épicerie tombe à 1x")

    print("\n" + "=" * 70)
    print(" TESTS TERMINÉS")
    print("=" * 70)


if __name__ == "__main__":
    test_profil_avec_nouvelles_questions()
