"""
Moteur de questionnaire pour recommandation de cartes de crédit
Questionnaire conditionnel et intelligent
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class QuestionType(Enum):
    SINGLE_CHOICE = "single"
    MULTI_CHOICE = "multi"
    NUMERIC = "numeric"
    TEXT = "text"
    RANKING = "ranking"


@dataclass
class Question:
    id: str
    text: str
    question_type: QuestionType
    options: List[str] = field(default_factory=list)
    section: str = ""
    warning: str = ""
    show_condition: Optional[Dict[str, Any]] = None  # Condition pour afficher la question
    required: bool = True


@dataclass
class UserProfile:
    """Profil utilisateur complet"""
    # Section 1 - Profil de base
    province: str = ""
    age_range: str = ""
    status: str = ""
    income_personal: str = ""
    income_household: str = ""
    credit_score: str = ""
    denied_recently: str = ""

    # Section 2 - Situation bancaire
    banks: List[str] = field(default_factory=list)
    open_to_new_bank: str = ""

    # Section 3 - Cartes actuelles
    has_cards: bool = False
    num_cards: int = 0
    current_cards: List[Dict] = field(default_factory=list)

    # Section 4 - Dépenses
    total_monthly: str = ""
    spending_groceries: float = 0.0
    spending_gas: float = 0.0
    spending_restaurants: float = 0.0
    spending_pharmacy: float = 0.0
    spending_transport: float = 0.0
    spending_subscriptions: float = 0.0
    spending_entertainment: float = 0.0
    spending_clothing: float = 0.0
    spending_electronics: float = 0.0
    spending_online: float = 0.0
    spending_healthcare: float = 0.0
    spending_business: float = 0.0
    other_expenses: Dict[str, float] = field(default_factory=dict)

    # Section 5 - Habitudes d'achat
    grocery_stores: List[str] = field(default_factory=list)
    gas_stations: List[str] = field(default_factory=list)
    pharmacy_stores: List[str] = field(default_factory=list)
    telecom_services: List[str] = field(default_factory=list)
    uses_canadian_tire: str = ""
    uses_hudson_bay: str = ""
    uses_walmart: str = ""
    uses_costco: str = ""
    foreign_purchases: str = ""

    # Section 6 - Voyages
    travel_frequency: str = ""
    travel_destinations: str = ""
    travel_budget: str = ""
    booking_method: str = ""
    airlines: List[str] = field(default_factory=list)
    lounge_interest: str = ""
    nexus_interest: str = ""
    hotel_type: str = ""
    car_rental: str = ""
    travel_insurance_existing: str = ""
    travel_fees_acceptable: str = ""
    reward_preference: str = ""
    redemption_class: str = ""
    air_canada_spending: str = ""
    westjet_spending: str = ""

    # Section 7 - Préférences
    priorities: List[str] = field(default_factory=list)
    points_comfort: str = ""
    max_annual_fee: str = ""
    pays_balance_full: str = ""
    has_debt: str = ""
    desired_num_cards: str = ""
    open_to_multiple: str = ""

    # Section 8 - Assurances
    life_insurance: str = ""
    device_insurance: str = ""
    device_insurance_interest: str = ""
    event_tickets: str = ""
    presale_interest: str = ""
    home_owner: str = ""
    has_vehicle: str = ""

    # Section 9 - Style de vie
    food_delivery: str = ""
    rideshare: str = ""
    amazon_usage: str = ""
    amazon_prime: str = ""
    tuition_payments: str = ""
    has_children: str = ""
    charity_donations: str = ""
    home_improvement: str = ""
    professional_services: str = ""

    # Section 10 - Profil spécifique
    business_registered: str = ""
    separate_cards_business: str = ""
    ad_spending: str = ""
    office_supplies_spending: str = ""
    school_type: str = ""
    cosigner_available: str = ""
    school_partnership: str = ""
    retirement_income: str = ""
    long_stays: str = ""
    long_stay_insurance: str = ""

    # Section 11 - Final
    timeline: str = ""
    network_preference: str = ""
    excluded_institutions: str = ""
    specific_offer: str = ""
    must_have_feature: str = ""
    other_info: str = ""

    # ============== SECTION 12 - OPTIMISATION ACTUARIELLE ==============
    # Dépenses en devises étrangères (mensuel)
    spending_foreign: float = 0.0

    # Assurance médicale existante via employeur
    employer_insurance: str = ""

    # Valuation des points (CPP - Cents Per Point)
    points_valuation: str = ""

    # Stratégie de garde de carte
    card_strategy: str = ""

    # Nombre de voyages par an (pour calcul proportionnel)
    trips_per_year: int = 1


class QuestionnaireEngine:
    """Moteur de questionnaire conditionnel"""

    def __init__(self):
        self.profile = UserProfile()
        self.answers: Dict[str, Any] = {}
        self.current_question = 0
        self.questions = self._build_questions()

    def _build_questions(self) -> List[Question]:
        """Construit toutes les questions du questionnaire"""

        questions = []

        # ============== SECTION 1 - PROFIL DE BASE ==============
        questions.append(Question(
            id="province",
            text="Dans quelle province ou territoire résidez-vous ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            options=[
                "Alberta", "Colombie-Britannique", "Manitoba", "Nouveau-Brunswick",
                "Terre-Neuve-et-Labrador", "Nouvelle-Écosse", "Ontario",
                "Île-du-Prince-Édouard", "Québec", "Saskatchewan",
                "Territoires du Nord-Ouest", "Nunavut", "Yukon"
            ]
        ))

        questions.append(Question(
            id="age",
            text="Quel est votre âge ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            options=[
                "Moins de 18 ans", "18–24 ans", "25–34 ans", "35–44 ans",
                "45–54 ans", "55–64 ans", "65 ans et plus"
            ]
        ))

        questions.append(Question(
            id="status",
            text="Quel est votre statut actuel ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            options=[
                "Employé à temps plein", "Employé à temps partiel",
                "Travailleur autonome", "Retraité", "Étudiant à temps plein",
                "Étudiant à temps partiel", "Sans emploi", "Autre"
            ]
        ))

        questions.append(Question(
            id="income_personal",
            text="Quel est votre revenu personnel annuel brut ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            warning="Certaines cartes premium ont des critères de revenu minimum — votre éligibilité pourrait ne pas être vérifiable.",
            options=[
                "Moins de 20 000 $", "20 000–39 999 $", "40 000–59 999 $",
                "60 000–79 999 $", "80 000–99 999 $", "100 000–149 999 $",
                "150 000 $ et plus", "Préfère ne pas répondre"
            ]
        ))

        questions.append(Question(
            id="income_household",
            text="Quel est votre revenu du ménage annuel brut (vous + conjoint·e si applicable) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            options=[
                "Moins de 40 000 $", "40 000–79 999 $", "80 000–119 999 $",
                "120 000–149 999 $", "150 000–199 999 $", "200 000 $ et plus",
                "Je vis seul(e)", "Préfère ne pas répondre"
            ]
        ))

        questions.append(Question(
            id="credit_score",
            text="Quel est votre score de crédit approximatif ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            warning="Certaines cartes premium nécessitent un excellent crédit — des recommandations non éligibles pourraient apparaître.",
            options=[
                "Je ne sais pas", "Excellent (760+)", "Très bon (720–759)",
                "Bon (680–719)", "Acceptable (640–679)", "Passable (600–639)",
                "Faible (moins de 600)", "Préfère ne pas répondre"
            ]
        ))

        questions.append(Question(
            id="denied_recently",
            text="Avez-vous déjà été refusé(e) pour une carte de crédit dans les 12 derniers mois ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil de base",
            options=["Oui", "Non", "Je ne sais pas"]
        ))

        # ============== SECTION 2 - SITUATION BANCAIRE ==============
        questions.append(Question(
            id="banks",
            text="Avec quelle(s) institution(s) financière(s) avez-vous présentement un compte bancaire ?",
            question_type=QuestionType.MULTI_CHOICE,
            section="Situation bancaire",
            options=[
                "RBC", "TD", "BMO", "CIBC", "Banque Scotia", "Banque Nationale",
                "Desjardins", "Tangerine", "Simplii Financial", "EQ Bank",
                "Motus Bank", "Banque Laurentienne", "ATB Financial",
                "Coast Capital", "Manulife Bank", "Autre", "Aucun compte bancaire"
            ]
        ))

        questions.append(Question(
            id="open_to_new_bank",
            text="Êtes-vous ouvert(e) à ouvrir un compte dans une nouvelle institution financière si cela vous donne accès à une carte plus avantageuse ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Situation bancaire",
            options=[
                "Oui, sans problème", "Oui, mais seulement si le bénéfice est clairement supérieur",
                "Non, je préfère rester avec mon institution actuelle",
                "Non, je ne veux aucun compte bancaire lié à ma carte"
            ]
        ))

        # ============== SECTION 3 - CARTES ACTUELLES ==============
        questions.append(Question(
            id="has_cards",
            text="Avez-vous présentement une ou plusieurs cartes de crédit ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Cartes actuelles",
            options=["Oui", "Non"]
        ))

        questions.append(Question(
            id="num_cards",
            text="Combien de cartes de crédit possédez-vous actuellement ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Cartes actuelles",
            show_condition={"has_cards": "Oui"},
            options=["1", "2", "3", "4", "5 et plus"]
        ))

        # ============== SECTION 4 - DÉPENSES ==============
        questions.append(Question(
            id="total_monthly",
            text="Quel est votre budget mensuel total payé par carte de crédit ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Dépenses mensuelles",
            options=[
                "Moins de 500 $", "500–999 $", "1 000–1 999 $", "2 000–2 999 $",
                "3 000–4 999 $", "5 000–7 499 $", "7 500–9 999 $", "10 000 $ et plus"
            ]
        ))

        questions.append(Question(
            id="spending_groceries",
            text="Combien dépensez-vous par mois en épicerie (nourriture, boissons, produits ménagers) ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_gas",
            text="Combien dépensez-vous par mois en essence / carburant ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_restaurants",
            text="Combien dépensez-vous par mois au restaurant, en livraison de repas ou en nourriture à emporter ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_pharmacy",
            text="Combien dépensez-vous par mois en pharmacie ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_transport",
            text="Combien dépensez-vous par mois en transport (transport en commun, Uber, taxis, stationnement) ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_subscriptions",
            text="Combien dépensez-vous par mois en abonnements récurrents (télécommunications, Internet, streaming, gym) ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_entertainment",
            text="Combien dépensez-vous par mois en divertissement (cinéma, spectacles, événements sportifs) ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        questions.append(Question(
            id="spending_online",
            text="Combien dépensez-vous par mois en achats en ligne (Amazon, commerce électronique) ?",
            question_type=QuestionType.NUMERIC,
            section="Dépenses mensuelles",
            options=[]
        ))

        # ============== SECTION 5 - HABITUDES D'ACHAT ==============
        questions.append(Question(
            id="grocery_stores",
            text="Dans quelle(s) chaîne(s) faites-vous principalement votre épicerie ?",
            question_type=QuestionType.MULTI_CHOICE,
            section="Habitudes d'achat",
            options=[
                "Maxi", "Provigo", "IGA", "Metro", "Super C", "Costco",
                "Walmart Supercentre", "Loblaws", "Real Canadian Superstore",
                "Sobeys", "FreshCo", "Farm Boy", "Marché Adonis", "Autre"
            ]
        ))

        questions.append(Question(
            id="gas_stations",
            text="Dans quelle(s) chaîne(s) achetez-vous votre essence ?",
            question_type=QuestionType.MULTI_CHOICE,
            section="Habitudes d'achat",
            options=[
                "Petro-Canada", "Esso", "Shell", "Ultramar", "Canadian Tire",
                "Costco", "Irving", "Mobil", "Pioneer", "Je n'achète pas d'essence"
            ]
        ))

        questions.append(Question(
            id="uses_costco",
            text="Faites-vous régulièrement des achats chez Costco ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Habitudes d'achat",
            options=["Oui, régulièrement", "Oui, occasionnellement", "Rarement", "Jamais"]
        ))

        questions.append(Question(
            id="uses_walmart",
            text="Faites-vous régulièrement des achats chez Walmart ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Habitudes d'achat",
            options=["Oui, régulièrement", "Oui, occasionnellement", "Rarement", "Jamais"]
        ))

        questions.append(Question(
            id="telecom_services",
            text="Utilisez-vous les services d'une ou plusieurs des compagnies suivantes ?",
            question_type=QuestionType.MULTI_CHOICE,
            section="Habitudes d'achat",
            options=[
                "Rogers", "Fido", "TELUS", "Bell", "Vidéotron", "Koodo",
                "Public Mobile", "Virgin Plus", "Fizz", "Aucun"
            ]
        ))

        # ============== SECTION 6 - VOYAGES ==============
        questions.append(Question(
            id="travel_frequency",
            text="À quelle fréquence voyagez-vous (incluant voyages domestiques et internationaux) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Voyages",
            options=[
                "Jamais ou presque", "1 fois par an", "2–3 fois par an",
                "4–5 fois par an", "6 fois et plus par an"
            ]
        ))

        questions.append(Question(
            id="travel_destinations",
            text="Voyagez-vous principalement :",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Voyages",
            show_condition={"travel_frequency_not": "Jamais ou presque"},
            options=[
                "Au Canada uniquement", "Aux États-Unis principalement",
                "En Europe principalement", "En Asie principalement",
                "Dans les Caraïbes", "Partout dans le monde"
            ]
        ))

        questions.append(Question(
            id="travel_budget",
            text="Quel est votre budget annuel approximatif consacré aux voyages ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Voyages",
            show_condition={"travel_frequency_not": "Jamais ou presque"},
            options=[
                "Moins de 1 000 $", "1 000–2 999 $", "3 000–4 999 $",
                "5 000–9 999 $", "10 000–19 999 $", "20 000 $ et plus"
            ]
        ))

        questions.append(Question(
            id="airlines",
            text="Quelle(s) compagnie(s) aérienne(s) utilisez-vous le plus souvent ?",
            question_type=QuestionType.MULTI_CHOICE,
            section="Voyages",
            show_condition={"travel_frequency_not": "Jamais ou presque"},
            options=[
                "Air Canada", "WestJet", "Porter", "Air Transat",
                "Delta", "American Airlines", "United", "Air France",
                "British Airways", "Aucune préférence"
            ]
        ))

        questions.append(Question(
            id="lounge_interest",
            text="Seriez-vous intéressé(e) par une carte qui offre l'accès aux salons d'aéroport ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Voyages",
            show_condition={"travel_frequency_not": "Jamais ou presque"},
            options=[
                "Oui, c'est très important pour moi",
                "Oui, si c'est inclus dans les avantages",
                "Non, ce n'est pas utile pour moi"
            ]
        ))

        questions.append(Question(
            id="reward_preference",
            text="Préférez-vous les récompenses voyage sous forme de :",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Voyages",
            show_condition={"travel_frequency_not": "Jamais ou presque"},
            options=[
                "Points/miles transférables vers des compagnies aériennes",
                "Remise directe sur les achats voyage (cashback voyage)",
                "Flexible — peu importe si la valeur est bonne",
                "Je ne suis pas intéressé(e) par les récompenses voyage"
            ]
        ))

        # ============== SECTION 7 - PRÉFÉRENCES ==============
        questions.append(Question(
            id="max_annual_fee",
            text="Quel est le montant maximum de frais annuels que vous êtes prêt(e) à payer pour une carte de crédit ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Préférences",
            options=[
                "0 $ (sans frais seulement)", "Jusqu'à 50 $", "Jusqu'à 100 $",
                "Jusqu'à 150 $", "Jusqu'à 200 $", "Jusqu'à 300 $",
                "Jusqu'à 500 $", "Plus de 500 $ si le ROI est démontré"
            ]
        ))

        questions.append(Question(
            id="pays_balance_full",
            text="Payez-vous votre solde de carte de crédit en entier chaque mois ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Préférences",
            options=["Toujours", "Presque toujours", "Parfois", "Rarement", "Jamais"]
        ))

        questions.append(Question(
            id="has_debt",
            text="Avez-vous actuellement des dettes de carte de crédit (solde impayé) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Préférences",
            warning="Si vous avez un solde important, nous recommanderons prioritairement une carte à taux réduit.",
            options=[
                "Non", "Oui, moins de 1 000 $", "Oui, 1 000–4 999 $",
                "Oui, 5 000 $ et plus", "Préfère ne pas répondre"
            ]
        ))

        questions.append(Question(
            id="points_comfort",
            text="Êtes-vous à l'aise avec la gestion de points (stratégies de transfert, optimisation) ou préférez-vous la simplicité du cashback ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Préférences",
            options=[
                "Je suis à l'aise et j'aime optimiser mes points",
                "Je connais les bases mais sans complexité",
                "Je préfère nettement le cashback — simple et direct",
                "Je ne suis pas sûr(e) — expliquez la différence"
            ]
        ))

        questions.append(Question(
            id="desired_num_cards",
            text="Combien de cartes de crédit souhaitez-vous idéalement détenir ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Préférences",
            options=["1 seule", "2 cartes maximum", "3 cartes maximum", "Autant que nécessaire pour maximiser"]
        ))

        questions.append(Question(
            id="open_to_multiple",
            text="Seriez-vous intéressé(e) par une solution avec deux cartes complémentaires si cela maximise vos gains ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Préférences",
            options=[
                "Oui, si l'application me prouve que c'est plus rentable",
                "Peut-être", "Non, une seule carte"
            ]
        ))

        questions.append(Question(
            id="priorities",
            text="Quelle est votre priorité principale pour votre carte de crédit idéale ? (choisissez max 3)",
            question_type=QuestionType.MULTI_CHOICE,
            section="Préférences",
            options=[
                "Maximiser les récompenses sur les achats du quotidien",
                "Avantages voyage (assurances, salons, miles)",
                "Cashback simple sans gérer des points",
                "Frais annuels les plus bas possible",
                "Avantages dans des commerces spécifiques",
                "Assurances (achats, appareils, voyage)",
                "Accumulation rapide pour un voyage spécifique"
            ]
        ))

        # ============== SECTION 8 - ASSURANCES ==============
        questions.append(Question(
            id="device_insurance",
            text="Avez-vous une couverture d'assurance pour vos appareils électroniques (téléphone, ordinateur) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Assurances",
            options=[
                "Oui, via mon opérateur téléphonique",
                "Oui, via une assurance habitation", "Non", "Je ne sais pas"
            ]
        ))

        questions.append(Question(
            id="home_owner",
            text="Êtes-vous propriétaire ou locataire de votre logement ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Assurances",
            options=["Propriétaire", "Locataire", "Je vis chez mes parents ou un proche", "Autre"]
        ))

        questions.append(Question(
            id="has_vehicle",
            text="Avez-vous un véhicule motorisé ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Assurances",
            options=["Oui, 1 véhicule", "Oui, 2 véhicules ou plus", "Non"]
        ))

        # ============== SECTION 9 - STYLE DE VIE ==============
        questions.append(Question(
            id="amazon_usage",
            text="Utilisez-vous Amazon (achats en ligne) de façon régulière ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Style de vie",
            options=[
                "Oui, je fais la majorité de mes achats en ligne via Amazon",
                "Oui, mais c'est un parmi plusieurs sites", "Rarement", "Jamais"
            ]
        ))

        questions.append(Question(
            id="amazon_prime",
            text="Avez-vous un abonnement Amazon Prime ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Style de vie",
            options=["Oui", "Non", "J'envisage de le prendre"]
        ))

        questions.append(Question(
            id="food_delivery",
            text="Utilisez-vous des services de livraison de repas (DoorDash, Uber Eats, Skip) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Style de vie",
            options=[
                "Rarement", "1–3 fois par mois", "1–2 fois par semaine", "Presque tous les jours"
            ]
        ))

        # ============== SECTION 10 - QUESTIONS CONDITIONNELLES ==============

        # Pour travailleurs autonomes
        questions.append(Question(
            id="business_registered",
            text="Avez-vous une entreprise enregistrée (numéro de TPS/TVQ, incorporation) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil travailleur autonome",
            show_condition={"status": "Travailleur autonome"},
            options=["Oui, incorporated", "Oui, enregistrée non incorporée", "Non"]
        ))

        questions.append(Question(
            id="ad_spending",
            text="Avez-vous des dépenses publicitaires (Google Ads, Meta Ads) payées par carte ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil travailleur autonome",
            show_condition={"status": "Travailleur autonome"},
            options=["Oui, plus de 1 000 $/mois", "Oui, moins de 1 000 $/mois", "Non"]
        ))

        # Pour étudiants
        questions.append(Question(
            id="school_type",
            text="Êtes-vous actuellement inscrit(e) dans un établissement d'enseignement postsecondaire ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil étudiant",
            show_condition={"status_in": ["Étudiant à temps plein", "Étudiant à temps partiel"]},
            options=["Oui, université", "Oui, CEGEP", "Oui, collège ou école technique", "Non"]
        ))

        # Pour 65+
        questions.append(Question(
            id="long_stays",
            text="Voyagez-vous souvent pour des séjours prolongés (plus de 15 jours d'affilée) ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Profil 65+",
            show_condition={"age": "65 ans et plus"},
            options=["Oui, régulièrement", "Oui, parfois", "Non"]
        ))

        # ============== SECTION 11 - FINAL ==============
        questions.append(Question(
            id="timeline",
            text="Dans quel délai souhaitez-vous faire votre demande de carte de crédit ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Final",
            options=["Immédiatement", "Dans les 30 prochains jours", "Dans 1–3 mois", "Je planifie seulement pour l'instant"]
        ))

        questions.append(Question(
            id="network_preference",
            text="Avez-vous une préférence pour le réseau de paiement de votre prochaine carte ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Final",
            options=["Visa", "Mastercard", "American Express", "Aucune préférence"]
        ))

        questions.append(Question(
            id="must_have_feature",
            text="Y a-t-il un avantage spécifique qui est absolument non-négociable pour vous ?",
            question_type=QuestionType.TEXT,
            section="Final",
            required=False,
            options=[]
        ))

        # ============== SECTION 12 - OPTIMISATION ACTUARIELLE ==============
        questions.append(Question(
            id="spending_foreign",
            text="Combien dépensez-vous par mois en devises étrangères (achats en ligne US, voyages, abonnements internationaux) ?",
            question_type=QuestionType.NUMERIC,
            section="Optimisation actuarielle",
            options=[]
        ))

        questions.append(Question(
            id="employer_insurance",
            text="Avez-vous déjà une assurance médicale de voyage via votre employeur ou vos assurances personnelles ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Optimisation actuarielle",
            options=["Oui", "Non", "Je ne sais pas"]
        ))

        questions.append(Question(
            id="points_valuation",
            text="Comment préférez-vous utiliser vos points ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Optimisation actuarielle",
            options=[
                "Crédit au compte / Cashback direct (valeur = 1 cpp)",
                "Transfert vers partenaires aériens comme Aéroplan/Avios (valeur = 1.5-2 cpp)"
            ]
        ))

        questions.append(Question(
            id="card_strategy",
            text="Combien de temps prévoyez-vous garder cette carte ?",
            question_type=QuestionType.SINGLE_CHOICE,
            section="Optimisation actuarielle",
            options=[
                "Moins d'un an (Churning)",
                "1-2 ans",
                "À long terme (3 ans et plus)"
            ]
        ))

        return questions

    def get_next_question(self) -> Optional[Question]:
        """Retourne la prochaine question à poser"""
        while self.current_question < len(self.questions):
            q = self.questions[self.current_question]
            if self._should_show(q):
                return q
            self.current_question += 1
        return None

    def _should_show(self, question: Question) -> bool:
        """Détermine si une question doit être affichée selon les conditions"""
        if question.show_condition is None:
            return True

        for key, value in question.show_condition.items():
            if key.endswith("_not"):
                attr_key = key.replace("_not", "")
                if getattr(self.profile, attr_key, "") == value:
                    return False
            elif key.endswith("_in"):
                attr_key = key.replace("_in", "")
                if getattr(self.profile, attr_key, "") not in value:
                    return False
            else:
                if getattr(self.profile, key, "") != value:
                    return False
        return True

    def submit_answer(self, question_id: str, answer: Any):
        """Enregistre une réponse et met à jour le profil"""
        self.answers[question_id] = answer
        self._update_profile(question_id, answer)
        self.current_question += 1

    def _update_profile(self, question_id: str, answer: Any):
        """Met à jour le profil utilisateur selon la réponse"""
        if hasattr(self.profile, question_id):
            setattr(self.profile, question_id, answer)

    def get_progress(self) -> tuple:
        """Retourne la progression (questions répondues, total pertinent)"""
        total = sum(1 for q in self.questions if self._should_show(q))
        answered = len(self.answers)
        return answered, total

    def is_complete(self) -> bool:
        """Vérifie si le questionnaire est complet"""
        return self.get_next_question() is None


if __name__ == "__main__":
    # Test du moteur
    engine = QuestionnaireEngine()
    print(f"Nombre total de questions: {len(engine.questions)}")

    q = engine.get_next_question()
    while q:
        print(f"\n{q.section} - {q.text}")
        for opt in q.options[:3]:  # Afficher seulement 3 options
            print(f"  - {opt}")
        if len(q.options) > 3:
            print(f"  ... et {len(q.options) - 3} autres")
        engine.submit_answer(q.id, q.options[0] if q.options else "test")
        q = engine.get_next_question()

    print("\nQuestionnaire terminé!")
