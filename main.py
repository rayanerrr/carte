"""
Application de recommandation de cartes de crédit canadiennes
Interface en ligne de commande
"""

import os
import sys
from questionnaire import QuestionnaireEngine, QuestionType, UserProfile
from recommender import RecommendationEngine, generate_recommendation_report
from card_database import get_all_cards, CreditCard


def clear_screen():
    """Nettoie l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Affiche l'en-tête"""
    print("\n" + "=" * 70)
    print("  🇨🇦  RECOMMANDATEUR DE CARTES DE CRÉDIT CANADIENNES  🇨🇦")
    print("=" * 70)
    print("\nTrouvez la carte de crédit parfaite pour VOTRE profil en quelques minutes.")
    print("Répondez honnêtement pour des recommandations précises.\n")


def print_progress(current: int, total: int):
    """Affiche la progression"""
    pct = (current / total * 100) if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n[{bar}] {current}/{total} ({pct:.0f}%)")


def ask_question(question) -> any:
    """Pose une question et retourne la réponse"""

    print(f"\n{'─' * 60}")
    print(f"📋 {question.text}")
    print(f"{'─' * 60}")

    if question.warning:
        print(f"\n⚠️  {question.warning}\n")

    if question.question_type == QuestionType.SINGLE_CHOICE:
        for i, option in enumerate(question.options, 1):
            print(f"  {i}. {option}")
        print()

        while True:
            try:
                choice = input(f"Votre choix (1-{len(question.options)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(question.options):
                    return question.options[idx]
                print("❌ Choix invalide. Essayez à nouveau.")
            except ValueError:
                print("❌ Veuillez entrer un nombre.")

    elif question.question_type == QuestionType.MULTI_CHOICE:
        print("\n(Séparez vos choix par des virgules, ex: 1,3,5)")
        for i, option in enumerate(question.options, 1):
            print(f"  {i}. {option}")
        print()

        while True:
            try:
                choices = input("Vos choix: ").strip()
                indices = [int(x.strip()) - 1 for x in choices.split(",")]
                valid = all(0 <= idx < len(question.options) for idx in indices)
                if valid:
                    return [question.options[idx] for idx in indices]
                print("❌ Choix invalide. Essayez à nouveau.")
            except ValueError:
                print("❌ Veuillez entrer des nombres séparés par des virgules.")

    elif question.question_type == QuestionType.NUMERIC:
        while True:
            try:
                value = input("Votre réponse (en $, ou 0): ").strip()
                return float(value)
            except ValueError:
                print("❌ Veuillez entrer un nombre valide.")

    elif question.question_type == QuestionType.TEXT:
        value = input("Votre réponse (ou Entrée pour passer): ").strip()
        return value if value else None

    elif question.question_type == QuestionType.RANKING:
        print("\n(Classez par ordre d'importance, ex: 3,1,2 pour 3ème > 1er > 2ème)")
        for i, option in enumerate(question.options, 1):
            print(f"  {i}. {option}")
        print()

        while True:
            try:
                ranking = input("Votre classement: ").strip()
                indices = [int(x.strip()) - 1 for x in ranking.split(",")]
                valid = len(set(indices)) == len(indices) and all(0 <= idx < len(question.options) for idx in indices)
                if valid:
                    return [question.options[idx] for idx in indices]
                print("❌ Choix invalide. Essayez à nouveau.")
            except ValueError:
                print("❌ Veuillez entrer des nombres séparés par des virgules.")

    return None


def run_questionnaire() -> UserProfile:
    """Exécute le questionnaire complet"""

    clear_screen()
    print_header()

    engine = QuestionnaireEngine()

    # Calculer le nombre total de questions pertinentes
    total_questions = sum(1 for q in engine.questions if engine._should_show(q))
    print(f"Le questionnaire contient environ {total_questions} questions.")
    print("Vous pouvez passer certaines questions non-obligatoires avec Entrée.\n")

    input("Appuyez sur Entrée pour commencer...")

    question = engine.get_next_question()
    question_num = 0

    while question:
        clear_screen()
        print_progress(question_num, total_questions)

        answer = ask_question(question)

        if answer is not None or not question.required:
            engine.submit_answer(question.id, answer if answer is not None else "Non spécifié")
            question_num += 1

        question = engine.get_next_question()

    clear_screen()
    print("\n✅ Questionnaire terminé!\n")
    print("Analyse de votre profil en cours...")

    return engine.profile


def display_results(profile: UserProfile):
    """Affiche les résultats de recommandation"""

    engine = RecommendationEngine(profile)
    recommendations = engine.recommend(num_results=3)

    clear_screen()

    print("\n" + "=" * 70)
    print("  🎯 RÉSULTATS DE VOTRE ANALYSE")
    print("=" * 70)

    if not recommendations:
        print("\n❌ Aucune carte recommandée pour votre profil.")
        print("\nLes critères de filtrage sont peut-être trop restrictifs.")
        print("Essayez de modifier:")
        print("  • Votre utilisation de Costco")
        print("  • Votre préférence de réseau (Visa/Mastercard/Amex)")
        print("  • Vos frais annuels maximum")
        input("\nAppuyez sur Entrée pour retourner...")
        main()
        return

    for i, rec in enumerate(recommendations, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"

        print(f"\n{medal} RECOMMANDATION #{i}")
        print("-" * 50)
        print(f"\n📛 {rec.card.name}")
        print(f"🏦 {rec.card.issuer}")
        print(f"💳 {rec.card.network.value}")
        print(f"💰 Frais annuels: {rec.card.annual_fee}$" + (" (1ère année gratuite!)" if rec.card.first_year_free else ""))
        print(f"📊 Taux de base: {rec.card.base_rate}%")
        if rec.card.reward_program:
            print(f"🎁 Programme: {rec.card.reward_program}")

        print(f"\n📈 MATCH: {rec.match_percentage}%")
        print(f"💵 ROI ANNUEL ESTIMÉ: {rec.annual_roi}$")

        if rec.reasons:
            print("\n✅ Pourquoi cette carte vous convient:")
            for reason in rec.reasons:
                print(f"   • {reason}")

        if rec.warnings:
            print("\n⚠️ Points d'attention:")
            for warning in rec.warnings:
                print(f"   • {warning}")

        if rec.already_has_benefits:
            print("\nℹ️  Avantages que vous possédez déjà:")
            for benefit in rec.already_has_benefits:
                print(f"   • {benefit}")

    print("\n" + "=" * 70)
    print("💡 CONSEIL: Le ROI est calculé selon VOS dépenses réelles.")
    print("   Une carte avec frais annuels peut être plus rentable si les")
    print("   récompenses et avantages dépassent le coût des frais.")
    print("=" * 70)

    # Option pour voir plus de détails
    print("\n\nVoulez-vous:")
    print("1. Voir le détail complet du calcul ROI")
    print("2. Voir d'autres cartes (top 5-10)")
    print("3. Recommencer le questionnaire")
    print("4. Quitter")

    choice = input("\nVotre choix (1-4): ").strip()

    if choice == "1":
        display_roi_details(profile, recommendations[0].card if recommendations else None)
    elif choice == "2":
        display_more_cards(profile)
    elif choice == "3":
        main()
        return

    print("\nMerci d'avoir utilisé le recommandateur de cartes de crédit! 🇨🇦")


def display_roi_details(profile: UserProfile, card: CreditCard):
    """Affiche le détail du calcul ROI"""

    if not card:
        print("Aucune carte à analyser.")
        return

    clear_screen()
    print("\n" + "=" * 70)
    print(f"  📊 DÉTAIL DU ROI - {card.name}")
    print("=" * 70)

    spending = {
        "groceries": profile.spending_groceries,
        "gas": profile.spending_gas,
        "restaurants": profile.spending_restaurants,
        "pharmacy": profile.spending_pharmacy,
        "transport": profile.spending_transport,
        "subscriptions": profile.spending_subscriptions,
        "entertainment": profile.spending_entertainment,
        "online": profile.spending_online,
    }

    print("\n📍 VOS DÉPENSES MENSUELLES:")
    categories = {
        "groceries": "Épicerie",
        "gas": "Essence",
        "restaurants": "Restaurants",
        "pharmacy": "Pharmacie",
        "transport": "Transport",
        "subscriptions": "Abonnements",
        "entertainment": "Divertissement",
        "online": "Achats en ligne",
    }

    total_monthly = 0
    for key, label in categories.items():
        amount = spending.get(key, 0)
        if amount > 0:
            rate = card.get_reward_rate(key)
            annual_reward = amount * 12 * (rate / 100)
            total_monthly += amount
            print(f"   {label}: {amount}$/mois → {rate}% → {annual_reward:.2f}$/an")

    print(f"\n   TOTAL: {total_monthly}$/mois")

    rewards_annual = card.calculate_annual_value(spending)
    print(f"\n💰 RÉCOMPENSES ANNUELLES: {rewards_annual:.2f}$")

    if card.welcome_bonus > 0:
        print(f"🎁 BONUS DE BIENVENUE: {card.welcome_bonus}$")

    fees = card.annual_fee if not card.first_year_free else 0
    print(f"💸 FRAIS ANNUELS: {fees}$")

    net = rewards_annual + card.welcome_bonus - fees
    print(f"\n📈 ROI NET: {net:.2f}$")

    input("\nAppuyez sur Entrée pour retourner...")


def display_more_cards(profile: UserProfile):
    """Affiche plus de cartes"""

    engine = RecommendationEngine(profile)
    all_recs = engine.recommend(num_results=10)

    clear_screen()
    print("\n" + "=" * 70)
    print("  📋 TOP 10 DES CARTES POUR VOTRE PROFIL")
    print("=" * 70)

    for i, rec in enumerate(all_recs, 1):
        print(f"\n{i}. {rec.card.name}")
        print(f"   {rec.card.issuer} | {rec.card.network.value} | {rec.card.annual_fee}$")
        print(f"   Match: {rec.match_percentage}% | ROI: {rec.annual_roi}$/an")

    input("\nAppuyez sur Entrée pour retourner...")


def quick_demo():
    """Démo rapide avec un profil aléatoire généré automatiquement"""
    import random

    print("\n🚀 LANCEMENT DE LA DÉMO RAPIDE...\n")
    print("Génération d'un profil aléatoire...\n")

    profile = UserProfile()

    # Profil de base (aléatoire)
    profile.province = random.choice(["Québec", "Ontario", "Colombie-Britannique", "Alberta"])
    profile.age_range = random.choice(["18–24 ans", "25–34 ans", "35–44 ans", "45–54 ans", "55–64 ans"])
    profile.status = random.choice(["Employé à temps plein", "Employé à temps partiel", "Travailleur autonome", "Étudiant à temps plein"])
    profile.income_personal = random.choice(["20 000–39 999 $", "40 000–59 999 $", "60 000–79 999 $", "80 000–99 999 $", "100 000–149 999 $"])
    profile.income_household = random.choice(["40 000–79 999 $", "80 000–119 999 $", "120 000–149 999 $", "150 000–199 999 $"])
    profile.credit_score = random.choice(["Excellent (760+)", "Très bon (720–759)", "Bon (680–719)", "Acceptable (640–679)"])

    # Banque
    profile.banks = random.sample(["RBC", "TD", "BMO", "Banque Scotia", "Desjardins", "Banque Nationale", "Tangerine", "Simplii Financial"], k=random.randint(1, 2))
    profile.open_to_new_bank = random.choice(["Oui, sans problème", "Oui, mais seulement si le bénéfice est clairement supérieur", "Non, je préfère rester avec mon institution actuelle"])

    # Cartes actuelles
    profile.has_cards = random.choice([True, False])
    profile.num_cards = random.randint(1, 4) if profile.has_cards else 0

    # Dépenses (aléatoires, entre 100 et 800$)
    profile.spending_groceries = round(random.uniform(200, 800), 0)
    profile.spending_gas = round(random.uniform(50, 300), 0)
    profile.spending_restaurants = round(random.uniform(100, 400), 0)
    profile.spending_pharmacy = round(random.uniform(20, 100), 0)
    profile.spending_transport = round(random.uniform(50, 200), 0)
    profile.spending_subscriptions = round(random.uniform(30, 150), 0)
    profile.spending_entertainment = round(random.uniform(50, 200), 0)
    profile.spending_online = round(random.uniform(100, 400), 0)

    # Habitudes d'achat
    profile.grocery_stores = random.sample(["Maxi", "Provigo", "IGA", "Metro", "Super C", "Walmart Supercentre", "Loblaws", "Costco"], k=random.randint(1, 3))
    profile.gas_stations = random.sample(["Petro-Canada", "Esso", "Shell", "Ultramar", "Canadian Tire", "Costco"], k=random.randint(1, 2))
    # Maintenant qu'il y a des cartes Mastercard compatibles Costco, on peut permettre toutes les options
    profile.uses_costco = random.choice(["Oui, régulièrement", "Oui, occasionnellement", "Rarement", "Jamais"])
    profile.uses_walmart = random.choice(["Oui, régulièrement", "Oui, occasionnellement", "Rarement", "Jamais"])
    profile.telecom_services = random.sample(["Rogers", "Fido", "TELUS", "Bell", "Vidéotron", "Koodo", "Public Mobile"], k=random.randint(1, 2))

    # Voyages
    profile.travel_frequency = random.choice(["Jamais ou presque", "1 fois par an", "2–3 fois par an", "4–5 fois par an", "6 fois et plus par an"])
    profile.travel_destinations = random.choice(["Au Canada uniquement", "Aux États-Unis principalement", "En Europe principalement", "Partout dans le monde"])
    profile.travel_budget = random.choice(["Moins de 1 000 $", "1 000–2 999 $", "3 000–4 999 $", "5 000–9 999 $", "10 000 $ et plus"])
    profile.airlines = random.sample(["Air Canada", "WestJet", "Porter", "Air Transat"], k=random.randint(1, 2))
    profile.lounge_interest = random.choice(["Oui, c'est très important pour moi", "Oui, si c'est inclus dans les avantages", "Non, ce n'est pas utile pour moi"])
    profile.reward_preference = random.choice(["Points/miles transférables vers des compagnies aériennes", "Remise directe sur les achats voyage (cashback voyage)", "Flexible — peu importe si la valeur est bonne"])

    # Préférences
    profile.max_annual_fee = random.choice(["0 $ (sans frais seulement)", "Jusqu'à 50 $", "Jusqu'à 100 $", "Jusqu'à 150 $", "Jusqu'à 200 $", "Plus de 500 $ si le ROI est démontré"])
    profile.pays_balance_full = random.choice(["Toujours", "Presque toujours", "Parfois", "Rarement"])
    profile.has_debt = random.choice(["Non", "Oui, moins de 1 000 $", "Oui, 1 000–4 999 $"])
    profile.points_comfort = random.choice(["Je suis à l'aise et j'aime optimiser mes points", "Je connais les bases mais sans complexité", "Je préfère nettement le cashback — simple et direct"])
    profile.desired_num_cards = random.choice(["1 seule", "2 cartes maximum", "3 cartes maximum"])
    profile.open_to_multiple = random.choice(["Oui, si l'application me prouve que c'est plus rentable", "Peut-être", "Non, une seule carte"])
    profile.priorities = random.sample(["Maximiser les récompenses sur les achats du quotidien", "Avantages voyage (assurances, salons, miles)", "Cashback simple sans gérer des points", "Frais annuels les plus bas possible", "Assurances (achats, appareils, voyage)"], k=random.randint(1, 3))

    # Style de vie
    profile.amazon_usage = random.choice(["Oui, je fais la majorité de mes achats en ligne via Amazon", "Oui, mais c'est un parmi plusieurs sites", "Rarement", "Jamais"])
    profile.amazon_prime = random.choice(["Oui", "Non", "J'envisage de le prendre"])
    profile.home_owner = random.choice(["Propriétaire", "Locataire"])
    profile.has_vehicle = random.choice(["Oui, 1 véhicule", "Oui, 2 véhicules ou plus", "Non"])

    profile.timeline = random.choice(["Immédiatement", "Dans les 30 prochains jours", "Dans 1–3 mois"])
    profile.network_preference = random.choice(["Visa", "Mastercard", "American Express", "Aucune préférence"])

    # Afficher le profil généré
    print("=" * 60)
    print("  📋 PROFIL GÉNÉRÉ")
    print("=" * 60)
    print(f"  📍 Province: {profile.province}")
    print(f"  🎂 Âge: {profile.age_range}")
    print(f"  💼 Statut: {profile.status}")
    print(f"  💰 Revenu personnel: {profile.income_personal}")
    print(f"  📊 Score de crédit: {profile.credit_score}")
    print(f"  🏦 Banques: {', '.join(profile.banks)}")
    print(f"\n  🛒 Dépenses mensuelles:")
    print(f"     • Épicerie: {profile.spending_groceries}$")
    print(f"     • Essence: {profile.spending_gas}$")
    print(f"     • Restaurants: {profile.spending_restaurants}$")
    print(f"     • En ligne: {profile.spending_online}$")
    print(f"  ✈️  Voyages: {profile.travel_frequency}")
    print(f"  🎯 Préférence: {profile.points_comfort}")
    print(f"  💳 Frais annuels max: {profile.max_annual_fee}")
    print("=" * 60)

    display_results(profile)


def main():
    """Fonction principale"""

    clear_screen()
    print_header()

    print("Que souhaitez-vous faire?")
    print("1. Commencer le questionnaire complet")
    print("2. Démo rapide (profil prédéfini)")
    print("3. Voir toutes les cartes dans la base de données")
    print("4. Quitter")

    choice = input("\nVotre choix (1-4): ").strip()

    if choice == "1":
        profile = run_questionnaire()
        display_results(profile)
    elif choice == "2":
        quick_demo()
    elif choice == "3":
        cards = get_all_cards()
        clear_screen()
        print(f"\n📊 BASE DE DONNÉES: {len(cards)} cartes")
        print("=" * 70)

        for card in cards[:20]:  # Afficher les 20 premières
            print(f"• {card.name} ({card.issuer}) - {card.annual_fee}$ - {card.tier.value}")

        if len(cards) > 20:
            print(f"\n... et {len(cards) - 20} autres cartes")

        input("\nAppuyez sur Entrée pour retourner...")
        main()
    elif choice == "4":
        print("\nMerci et à bientôt! 👋\n")
        sys.exit(0)
    else:
        print("\n❌ Choix invalide.")
        input("Appuyez sur Entrée...")
        main()


if __name__ == "__main__":
    main()
