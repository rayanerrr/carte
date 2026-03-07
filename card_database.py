"""
Base de données de cartes de crédit canadiennes
~50 cartes avec détails complets pour recommandation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class CardNetwork(Enum):
    VISA = "Visa"
    MASTERCARD = "Mastercard"
    AMEX = "American Express"


class CardTier(Enum):
    STUDENT = "student"
    NO_FEE = "no_fee"
    CASHBACK = "cashback"
    REWARDS = "rewards"
    TRAVEL = "travel"
    PREMIUM = "premium"
    BUSINESS = "business"


@dataclass
class RewardCategory:
    category: str
    rate: float  # % cashback ou points par dollar
    cap_monthly: Optional[float] = None  # Plafond mensuel en $
    cap_annual: Optional[float] = None   # Plafond annuel en $


@dataclass
class Insurance:
    travel_medical: bool = False
    travel_medical_days: int = 0   # Durée réelle de couverture médicale voyage (jours)
                                   # 0 = pas de couverture
                                   # Valeurs typiques au Canada:
                                   # 10-15j: cartes standard (CIBC, RBC entrée de gamme)
                                   # 15j:    Amex Cobalt, Amex Gold, BMO WE, TD
                                   # 21j:    BMO Ascend WE, TD First Class, Scotia Infinite
                                   # 25j:    Scotia Gold Amex
                                   # 31j:    Amex Platinum
                                   # 60j:    Desjardins Odyssey World Elite (exceptionnelle)
    travel_cancellation: bool = False
    travel_interruption: bool = False
    baggage: bool = False
    car_rental: bool = False
    purchase_protection: bool = False
    extended_warranty: bool = False
    mobile_device: bool = False
    common_carrier: bool = False
    hotel_burglary: bool = False
    delay: bool = False


@dataclass
class TravelPerks:
    lounge_access: bool = False
    lounge_visits_per_year: int = 0
    nexus_credit: bool = False
    global_entry_credit: bool = False
    first_bag_free: bool = False
    companion_pass: bool = False
    hotel_status: str = ""
    airline_status: str = ""
    travel_credit_annual: float = 0.0


@dataclass
class CreditCard:
    id: str
    name: str
    issuer: str
    network: CardNetwork
    tier: CardTier

    # Frais et taux
    annual_fee: float = 0.0
    first_year_free: bool = False
    interest_rate: float = 19.99

    # Critères d'éligibilité
    min_income_personal: float = 0.0
    min_income_household: float = 0.0
    min_credit_score: int = 640
    student_only: bool = False

    # Récompenses
    base_rate: float = 0.0  # Taux de base %
    welcome_bonus: float = 0.0  # Valeur estimée en $
    reward_categories: List[RewardCategory] = field(default_factory=list)
    reward_program: str = ""  # Nom du programme (PC Optimum, Aéroplan, etc.)

    # Assurances
    insurance: Insurance = field(default_factory=Insurance)

    # Avantages voyage
    travel_perks: TravelPerks = field(default_factory=TravelPerks)

    # Avantages spécifiques
    grocery_stores: List[str] = field(default_factory=list)
    gas_stations: List[str] = field(default_factory=list)
    restaurant_partners: List[str] = field(default_factory=list)

    # Frais de change
    no_fx_fee: bool = False  # True = aucun frais de conversion de devises

    # Compatibilité
    compatible_with_costco: bool = True  # False si Visa ou Amex

    def get_reward_rate(self, category: str) -> float:
        """Retourne le taux de récompense pour une catégorie donnée"""
        for cat in self.reward_categories:
            if cat.category.lower() == category.lower():
                return cat.rate
        return self.base_rate

    def get_reward_cap(self, category: str) -> Optional[float]:
        """Retourne le plafond mensuel pour une catégorie (None = pas de plafond)"""
        for cat in self.reward_categories:
            if cat.category.lower() == category.lower():
                return cat.cap_monthly
        return None

    def calculate_annual_value(self, spending: Dict[str, float]) -> float:
        """Calcule la valeur annuelle des récompenses basé sur les dépenses"""
        annual_value = 0.0

        for category, monthly_spending in spending.items():
            rate = self.get_reward_rate(category)
            annual_value += monthly_spending * 12 * (rate / 100)

        return annual_value

    def net_annual_value(self, spending: Dict[str, float]) -> float:
        """Valeur nette annuelle (récompenses - frais)"""
        rewards = self.calculate_annual_value(spending)
        fees = self.annual_fee if not self.first_year_free else 0
        return rewards - fees


# ============================================================================
# BASE DE DONNÉES DES CARTES - CARTES AMERICAN EXPRESS
# ============================================================================

def get_amex_cards() -> List[CreditCard]:
    """Retourne toutes les cartes American Express"""

    cards = []

    # 1. Amex Green - Carte verte
    cards.append(CreditCard(
        id="amex_green",
        name="Carte verte American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.TRAVEL,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="MR Points",
        reward_categories=[],
        grocery_stores=["Metro", "Sobeys", "Super C"],
        gas_stations=["Esso", "Shell"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 2. Amex Cobalt
    cards.append(CreditCard(
        id="amex_cobalt",
        name="Carte Cobalt American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.PREMIUM,
        annual_fee=155.88,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=150,
        reward_program="MR Points",
        reward_categories=[
            RewardCategory("groceries", 5.0, cap_monthly=2500),
            RewardCategory("dining", 5.0, cap_monthly=2500),
            RewardCategory("streaming", 3.0),
            RewardCategory("transit", 2.0),
            RewardCategory("gas", 2.0),
        ],
        grocery_stores=["Metro", "Sobeys", "Super C", "IGA", "Food Basics"],
        gas_stations=["Esso", "Shell", "Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 3. Amex Gold
    cards.append(CreditCard(
        id="amex_gold",
        name="Carte Or avec primes American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.PREMIUM,
        annual_fee=250.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=680,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="MR Points",
        reward_categories=[
            RewardCategory("travel", 2.0),
            RewardCategory("gas", 2.0),
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
        ],
        grocery_stores=["Metro", "Sobeys", "Super C", "IGA"],
        gas_stations=["Esso", "Shell", "Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=4,
            nexus_credit=True,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=100,
            hotel_status="",
        ),
    ))

    # 4. Amex Platinum
    cards.append(CreditCard(
        id="amex_platinum",
        name="Carte de Platine American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.PREMIUM,
        annual_fee=799.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=700,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=800,
        reward_program="MR Points",
        reward_categories=[
            RewardCategory("dining", 3.0),
            RewardCategory("travel", 2.0),
        ],
        grocery_stores=[],
        gas_stations=[],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=-1,
            nexus_credit=True,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=200,
            hotel_status="Gold",
        ),
    ))

    # 5. Amex SimplyCash
    cards.append(CreditCard(
        id="amex_simplycash",
        name="Carte RemiseSimple d'American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.25,
        welcome_bonus=40,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("gas", 2.0, cap_monthly=300),
            RewardCategory("groceries", 2.0, cap_monthly=300),
        ],
        grocery_stores=["Metro", "Sobeys", "Super C", "IGA"],
        gas_stations=["Esso", "Shell", "Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 6. Amex SimplyCash Preferred
    cards.append(CreditCard(
        id="amex_simplycash_preferred",
        name="Carte RemiseSimple Privilège d'American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.CASHBACK,
        annual_fee=119.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=2.0,
        welcome_bonus=400,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("gas", 4.0, cap_monthly=1200),
            RewardCategory("groceries", 4.0, cap_monthly=1200),
        ],
        grocery_stores=["Metro", "Sobeys", "Super C", "IGA"],
        gas_stations=["Esso", "Shell", "Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 7. Amex Aeroplan
    cards.append(CreditCard(
        id="amex_aeroplan",
        name="Carte Aéroplan American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.TRAVEL,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("air_canada", 2.0),
            RewardCategory("dining", 1.5),
            RewardCategory("delivery", 1.5),
        ],
        grocery_stores=[],
        gas_stations=[],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            global_entry_credit=False,
            first_bag_free=True,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 8. Amex Aeroplan Reserve
    cards.append(CreditCard(
        id="amex_aeroplan_reserve",
        name="Carte Prestige Aéroplan American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.PREMIUM,
        annual_fee=599.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=700,
        student_only=False,
        base_rate=1.25,
        welcome_bonus=800,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("air_canada", 3.0),
            RewardCategory("dining", 2.0),
            RewardCategory("delivery", 2.0),
        ],
        grocery_stores=[],
        gas_stations=[],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=-1,
            nexus_credit=True,
            global_entry_credit=False,
            first_bag_free=True,
            companion_pass=True,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 9. Amex Marriott Bonvoy
    cards.append(CreditCard(
        id="amex_marriott_bonvoy",
        name="Carte Marriott Bonvoy American Express",
        issuer="Amex",
        network=CardNetwork.AMEX,
        tier=CardTier.TRAVEL,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=21.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=2.0,
        welcome_bonus=250,
        reward_program="Marriott Bonvoy",
        reward_categories=[
            RewardCategory("marriott", 5.0),
        ],
        grocery_stores=[],
        gas_stations=[],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            global_entry_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="Silver",
        ),
    ))

    return cards


def _parse_reward_categories(categories_str: str) -> List[RewardCategory]:
    """Parse une chaîne de catégories de récompenses"""
    if not categories_str or categories_str == "[]":
        return []

    categories = []
    # Enlever les crochets et guillemets
    categories_str = categories_str.strip("[]\"'")

    # Parser chaque catégorie
    for cat in categories_str.split(","):
        cat = cat.strip()
        if ":" in cat:
            parts = cat.split(":")
            category = parts[0].strip()
            rate = float(parts[1].strip())
            cap = parts[2].strip() if len(parts) > 2 else None

            # Parser le cap (ex: "6000/an" ou "null")
            cap_monthly = None
            cap_annual = None
            if cap and cap != "null":
                if "/an" in cap:
                    cap_annual = float(cap.replace("/an", ""))
                else:
                    cap_monthly = float(cap)

            categories.append(RewardCategory(
                category=category,
                rate=rate,
                cap_monthly=cap_monthly,
                cap_annual=cap_annual
            ))

    return categories


def _parse_list(list_str: str) -> List[str]:
    """Parse une chaîne en liste"""
    if not list_str or list_str == "[]" or list_str == "``":
        return []
    # Enlever les crochets et guillemets
    list_str = list_str.strip("[]\"'")
    if list_str == "``":
        return []
    return [item.strip() for item in list_str.split(",")]


def get_rbc_cards() -> List[CreditCard]:
    """Retourne toutes les cartes RBC (Visa et Mastercard)"""

    cards = []

    # 1. RBC Avion Visa Infinite
    cards.append(CreditCard(
        id="rbc_avion_infinite",
        name="RBC Avion Visa Infinite",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=350,
        reward_program="Avion Rewards",
        reward_categories=[RewardCategory("travel", 1.25)],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 2. RBC Avion Visa Platinum
    cards.append(CreditCard(
        id="rbc_avion_platinum",
        name="RBC Avion Visa Platinum",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=350,
        reward_program="Avion Rewards",
        reward_categories=[RewardCategory("travel", 1.25)],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 3. RBC Avion Visa Infinite Privilege
    cards.append(CreditCard(
        id="rbc_avion_privilege",
        name="RBC Avion Visa Infinite Privilege",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.PREMIUM,
        annual_fee=399.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=150000,
        min_income_household=200000,
        min_credit_score=720,
        student_only=False,
        base_rate=1.25,
        welcome_bonus=500,
        reward_program="Avion Rewards",
        reward_categories=[],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=6,
            nexus_credit=True,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 4. RBC British Airways Visa Infinite
    cards.append(CreditCard(
        id="rbc_ba_infinite",
        name="RBC British Airways Visa Infinite",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=165.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=400,
        reward_program="Avios",
        reward_categories=[RewardCategory("british_airways", 2.0)],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 5. RBC Cash Back Mastercard
    cards.append(CreditCard(
        id="rbc_cashback_mc",
        name="RBC Cash Back Mastercard",
        issuer="RBC",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[RewardCategory("groceries", 2.0, cap_annual=6000)],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 6. RBC Cash Back Preferred World Elite Mastercard
    cards.append(CreditCard(
        id="rbc_cashback_we",
        name="RBC Cash Back Preferred World Elite Mastercard",
        issuer="RBC",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=99.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=700,
        student_only=False,
        base_rate=1.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 7. RBC ION Visa
    cards.append(CreditCard(
        id="rbc_ion",
        name="RBC ION Visa",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Avion Rewards",
        reward_categories=[
            RewardCategory("groceries", 1.5),
            RewardCategory("transit", 1.5),
            RewardCategory("streaming", 1.5),
        ],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 8. RBC ION+ Visa
    cards.append(CreditCard(
        id="rbc_ion_plus",
        name="RBC ION+ Visa",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=48.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=120,
        reward_program="Avion Rewards",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("dining", 3.0),
            RewardCategory("transit", 3.0),
            RewardCategory("gas", 3.0),
            RewardCategory("streaming", 3.0),
        ],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=True,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 9. RBC RateAdvantage Visa
    cards.append(CreditCard(
        id="rbc_rate_advantage",
        name="RBC RateAdvantage Visa",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=14.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 10. RBC Visa Classic Low Rate Option
    cards.append(CreditCard(
        id="rbc_classic_low_rate",
        name="RBC Visa Classic Low Rate Option",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=20.0,
        first_year_free=False,
        interest_rate=12.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 11. RBC Visa Platinum
    cards.append(CreditCard(
        id="rbc_visa_platinum",
        name="RBC Visa Platinum",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 12. RBC U.S. Dollar Visa Gold
    cards.append(CreditCard(
        id="rbc_us_gold",
        name="RBC U.S. Dollar Visa Gold",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=65.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=0,
        reward_program="Avion Rewards",
        reward_categories=[],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 13. More Rewards RBC Visa
    cards.append(CreditCard(
        id="rbc_more_rewards",
        name="More Rewards RBC Visa",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="More Rewards",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("dining", 2.0),
        ],
        grocery_stores=["Save-On-Foods"],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 14. More Rewards RBC Visa Infinite
    cards.append(CreditCard(
        id="rbc_more_rewards_infinite",
        name="More Rewards RBC Visa Infinite",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="More Rewards",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("dining", 2.0),
        ],
        grocery_stores=["Save-On-Foods"],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 15. moi RBC Visa
    cards.append(CreditCard(
        id="rbc_moi_visa",
        name="moi RBC Visa",
        issuer="RBC",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Moi Rewards",
        reward_categories=[
            RewardCategory("dining", 2.0),
            RewardCategory("gas", 2.0),
            RewardCategory("ev_charging", 2.0),
        ],
        grocery_stores=["Metro", "Super C", "Jean Coutu", "Premiere Moisson"],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 16. WestJet RBC World Elite Mastercard
    cards.append(CreditCard(
        id="rbc_westjet_we",
        name="WestJet RBC World Elite Mastercard",
        issuer="RBC",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=119.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        student_only=False,
        base_rate=1.5,
        welcome_bonus=300,
        reward_program="WestJet Rewards",
        reward_categories=[
            RewardCategory("westjet", 2.0),
            RewardCategory("groceries", 1.5),
            RewardCategory("dining", 1.5),
        ],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=True,
            companion_pass=True,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    # 17. WestJet RBC Mastercard
    cards.append(CreditCard(
        id="rbc_westjet_mc",
        name="WestJet RBC Mastercard",
        issuer="RBC",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=39.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        student_only=False,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="WestJet Rewards",
        reward_categories=[
            RewardCategory("westjet", 1.5),
            RewardCategory("groceries", 1.0),
            RewardCategory("dining", 1.0),
        ],
        grocery_stores=[],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=False,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=False,
            car_rental=False,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            lounge_visits_per_year=0,
            nexus_credit=False,
            first_bag_free=False,
            companion_pass=False,
            travel_credit_annual=0,
            hotel_status="",
        ),
    ))

    return cards


# ============================================================================
# TD BANK CARDS
# ============================================================================

def get_td_cards() -> List[CreditCard]:
    cards = []

    # 1. TD Aeroplan Visa Infinite
    cards.append(CreditCard(
        id="td_aeroplan_infinite",
        name="TD Aeroplan Visa Infinite",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=139.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("groceries", 1.5),
            RewardCategory("pharmacy", 1.5),
            RewardCategory("gas", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            nexus_credit=True,
            first_bag_free=False,
            travel_credit_annual=0,
        ),
    ))

    # 2. TD Aeroplan Visa Infinite Privilege
    cards.append(CreditCard(
        id="td_aeroplan_infinite_privilege",
        name="TD Aeroplan Visa Infinite Privilege",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.PREMIUM,
        annual_fee=599.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=150000,
        min_income_household=200000,
        min_credit_score=720,
        base_rate=1.25,
        welcome_bonus=750,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
            RewardCategory("gas", 2.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=6,
            nexus_credit=True,
            global_entry_credit=True,
            first_bag_free=True,
            travel_credit_annual=100,
        ),
    ))

    # 3. TD Aeroplan Visa Platinum
    cards.append(CreditCard(
        id="td_aeroplan_platinum",
        name="TD Aeroplan Visa Platinum",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=89.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=35000,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=150,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("groceries", 1.0),
            RewardCategory("pharmacy", 1.0),
            RewardCategory("gas", 1.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            travel_interruption=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 4. TD First Class Travel Visa Infinite
    cards.append(CreditCard(
        id="td_first_class_travel",
        name="TD First Class Travel Visa Infinite",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=139.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=2.0,
        welcome_bonus=400,
        reward_program="TD Rewards",
        reward_categories=[
            RewardCategory("groceries", 6.0),
            RewardCategory("pharmacy", 6.0),
            RewardCategory("gas", 6.0),
            RewardCategory("transport", 3.0),
            RewardCategory("online", 3.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            nexus_credit=True,
            travel_credit_annual=100,
        ),
    ))

    # 5. TD Cash Back Visa Infinite
    cards.append(CreditCard(
        id="td_cashback_infinite",
        name="TD Cash Back Visa Infinite",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=139.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("pharmacy", 3.0),
            RewardCategory("gas", 3.0),
            RewardCategory("transport", 1.5),
            RewardCategory("online", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=True),
    ))

    # 6. TD Rewards Visa (no fee)
    cards.append(CreditCard(
        id="td_rewards_visa",
        name="TD Rewards Visa",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="TD Rewards",
        reward_categories=[
            RewardCategory("restaurants", 2.0),
            RewardCategory("groceries", 2.0),
            RewardCategory("gas", 2.0),
            RewardCategory("transport", 2.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 7. TD Platinum Travel Visa
    cards.append(CreditCard(
        id="td_platinum_travel",
        name="TD Platinum Travel Visa",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=89.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=35000,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.5,
        welcome_bonus=200,
        reward_program="TD Rewards",
        reward_categories=[
            RewardCategory("groceries", 6.0),
            RewardCategory("pharmacy", 6.0),
            RewardCategory("gas", 6.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 8. TD Emerald Flex Rate Visa (low rate)
    cards.append(CreditCard(
        id="td_emerald_flex",
        name="TD Emerald Flex Rate Visa",
        issuer="TD",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=25.0,
        first_year_free=False,
        interest_rate=12.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 9. TD Cash Back Mastercard (no fee)
    cards.append(CreditCard(
        id="td_cashback_mc",
        name="TD Cash Back Mastercard",
        issuer="TD",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=0.5,
        welcome_bonus=50,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 1.0),
            RewardCategory("gas", 1.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# BMO CARDS
# ============================================================================

def get_bmo_cards() -> List[CreditCard]:
    cards = []

    # 1. BMO World Elite Mastercard
    cards.append(CreditCard(
        id="bmo_world_elite_mc",
        name="BMO World Elite Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.PREMIUM,
        annual_fee=150.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=2.0,
        welcome_bonus=500,
        reward_program="BMO Points",
        reward_categories=[
            RewardCategory("transport", 5.0),
            RewardCategory("restaurants", 3.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=4,
            nexus_credit=True,
            travel_credit_annual=150,
        ),
    ))

    # 2. BMO Cashback World Elite Mastercard
    cards.append(CreditCard(
        id="bmo_cashback_we_mc",
        name="BMO Cashback World Elite Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=120.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=200,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 5.0, cap_monthly=500),
            RewardCategory("transport", 4.0),
            RewardCategory("gas", 3.0),
            RewardCategory("pharmacy", 2.0),
            RewardCategory("subscriptions", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=True),
    ))

    # 3. BMO eclipse Visa Infinite
    cards.append(CreditCard(
        id="bmo_eclipse_infinite",
        name="BMO eclipse Visa Infinite",
        issuer="BMO",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=120.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="BMO Points",
        reward_categories=[
            RewardCategory("restaurants", 5.0),
            RewardCategory("groceries", 5.0),
            RewardCategory("transport", 5.0),
            RewardCategory("pharmacy", 5.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=False),
    ))

    # 4. BMO Ascend World Elite Mastercard
    cards.append(CreditCard(
        id="bmo_ascend_we_mc",
        name="BMO Ascend World Elite Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=150.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=350,
        reward_program="Air Miles",
        reward_categories=[
            RewardCategory("transport", 5.0),
            RewardCategory("groceries", 3.0),
            RewardCategory("pharmacy", 3.0),
            RewardCategory("subscriptions", 3.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=4,
            nexus_credit=True,
        ),
    ))

    # 5. BMO Preferred Rate Mastercard (low rate)
    cards.append(CreditCard(
        id="bmo_preferred_rate_mc",
        name="BMO Preferred Rate Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.NO_FEE,
        annual_fee=20.0,
        first_year_free=False,
        interest_rate=12.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 6. BMO Cashback Mastercard (no fee)
    cards.append(CreditCard(
        id="bmo_cashback_mc",
        name="BMO Cashback Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 3.0, cap_monthly=500),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 7. BMO Air Miles World Elite Mastercard
    cards.append(CreditCard(
        id="bmo_air_miles_we_mc",
        name="BMO Air Miles World Elite Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=250,
        reward_program="Air Miles",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("pharmacy", 3.0),
            RewardCategory("gas", 2.0),
            RewardCategory("transport", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=True),
    ))

    # 8. BMO Air Miles Mastercard (no fee)
    cards.append(CreditCard(
        id="bmo_air_miles_mc",
        name="BMO Air Miles Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="Air Miles",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 9. BMO eclipse Rise Visa (student/no fee)
    cards.append(CreditCard(
        id="bmo_eclipse_rise",
        name="BMO eclipse Rise Visa Card",
        issuer="BMO",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="BMO Points",
        reward_categories=[
            RewardCategory("restaurants", 5.0),
            RewardCategory("groceries", 5.0),
            RewardCategory("transport", 5.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# CIBC CARDS
# ============================================================================

def get_cibc_cards() -> List[CreditCard]:
    cards = []

    # 1. CIBC Aeroplan Visa Infinite
    cards.append(CreditCard(
        id="cibc_aeroplan_infinite",
        name="CIBC Aeroplan Visa Infinite",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=139.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("groceries", 1.5),
            RewardCategory("pharmacy", 1.5),
            RewardCategory("gas", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            nexus_credit=True,
            first_bag_free=False,
        ),
    ))

    # 2. CIBC Aeroplan Visa Infinite Privilege
    cards.append(CreditCard(
        id="cibc_aeroplan_infinite_privilege",
        name="CIBC Aeroplan Visa Infinite Privilege",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.PREMIUM,
        annual_fee=599.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=150000,
        min_income_household=200000,
        min_credit_score=720,
        base_rate=1.25,
        welcome_bonus=750,
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
            RewardCategory("gas", 2.0),
            RewardCategory("transport", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=6,
            nexus_credit=True,
            global_entry_credit=True,
            first_bag_free=True,
            travel_credit_annual=100,
        ),
    ))

    # 3. CIBC Aventura Visa Infinite
    cards.append(CreditCard(
        id="cibc_aventura_infinite",
        name="CIBC Aventura Visa Infinite",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=139.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=350,
        reward_program="Aventura",
        reward_categories=[
            RewardCategory("transport", 2.0),
            RewardCategory("groceries", 1.5),
            RewardCategory("pharmacy", 1.5),
            RewardCategory("gas", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=False,
            nexus_credit=True,
            travel_credit_annual=0,
        ),
    ))

    # 4. CIBC Dividend Visa Infinite
    cards.append(CreditCard(
        id="cibc_dividend_infinite",
        name="CIBC Dividend Visa Infinite",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=120.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=200,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 4.0),
            RewardCategory("gas", 4.0),
            RewardCategory("restaurants", 2.0),
            RewardCategory("pharmacy", 2.0),
            RewardCategory("transport", 2.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 5. CIBC Dividend Platinum Visa
    cards.append(CreditCard(
        id="cibc_dividend_platinum",
        name="CIBC Dividend Platinum Visa",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=99.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=35000,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("gas", 2.0),
            RewardCategory("restaurants", 2.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 6. CIBC Dividend Visa (no fee)
    cards.append(CreditCard(
        id="cibc_dividend_visa",
        name="CIBC Dividend Visa",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=0.5,
        welcome_bonus=50,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("pharmacy", 2.0),
            RewardCategory("groceries", 1.0),
            RewardCategory("gas", 1.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 7. CIBC Costco Mastercard (Costco-compatible!)
    cards.append(CreditCard(
        id="cibc_costco_mc",
        name="CIBC Costco Mastercard",
        issuer="CIBC",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("restaurants", 3.0),
            RewardCategory("gas", 2.0),
            RewardCategory("online", 2.0),
            RewardCategory("groceries", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 8. CIBC Select Visa (low rate)
    cards.append(CreditCard(
        id="cibc_select_visa",
        name="CIBC Select Visa",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=29.0,
        first_year_free=False,
        interest_rate=13.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# SCOTIABANK CARDS
# ============================================================================

def get_scotia_cards() -> List[CreditCard]:
    cards = []

    # 1. Scotiabank Passport Visa Infinite (no FX fees)
    cards.append(CreditCard(
        id="scotia_passport_infinite",
        name="Scotiabank Passport Visa Infinite",
        issuer="Banque Scotia",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=150.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        no_fx_fee=True,
        base_rate=1.0,
        welcome_bonus=500,
        reward_program="Scene+",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("restaurants", 2.0),
            RewardCategory("transport", 2.0),
            RewardCategory("gas", 2.0),
            RewardCategory("subscriptions", 2.0),
        ],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=6,
            nexus_credit=True,
        ),
    ))

    # 2. Scotiabank Gold American Express (no FX fees)
    cards.append(CreditCard(
        id="scotia_gold_amex",
        name="Scotiabank Gold American Express",
        issuer="Banque Scotia",
        network=CardNetwork.AMEX,
        tier=CardTier.REWARDS,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=700,
        reward_program="Scene+",
        reward_categories=[
            RewardCategory("groceries", 6.0),
            RewardCategory("restaurants", 5.0),
            RewardCategory("gas", 3.0),
            RewardCategory("subscriptions", 3.0),
            RewardCategory("transport", 3.0),
        ],
        grocery_stores=["Sobeys", "IGA", "FreshCo", "Foodland"],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=True),
    ))

    # 3. Scotiabank Scene+ Visa (no fee)
    cards.append(CreditCard(
        id="scotia_scene_plus_visa",
        name="Scotiabank Scene+ Visa",
        issuer="Banque Scotia",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="Scene+",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("restaurants", 1.0),
            RewardCategory("gas", 1.0),
        ],
        grocery_stores=["Sobeys", "IGA", "FreshCo"],
        gas_stations=["Petro-Canada"],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 4. Scotiabank Value Visa (low rate)
    cards.append(CreditCard(
        id="scotia_value_visa",
        name="Scotiabank Value Visa",
        issuer="Banque Scotia",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=29.0,
        first_year_free=False,
        interest_rate=12.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 5. Scotiabank Platinum American Express (no FX fees, lounge illimité)
    cards.append(CreditCard(
        id="scotia_platinum_amex",
        name="Scotiabank Platinum American Express",
        issuer="Banque Scotia",
        network=CardNetwork.AMEX,
        tier=CardTier.PREMIUM,
        annual_fee=399.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=60000,
        min_income_household=0,
        min_credit_score=700,
        base_rate=2.0,
        welcome_bonus=500,
        reward_program="Scene+",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("restaurants", 3.0),
            RewardCategory("gas", 3.0),
            RewardCategory("transport", 3.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=999,
            nexus_credit=True,
            travel_credit_annual=0,
        ),
    ))

    # 6. Scotiabank American Express (no fee)
    cards.append(CreditCard(
        id="scotia_amex",
        name="Scotiabank American Express Card",
        issuer="Banque Scotia",
        network=CardNetwork.AMEX,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Scene+",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# DESJARDINS CARDS
# ============================================================================

def get_desjardins_cards() -> List[CreditCard]:
    cards = []

    # 1. Desjardins Odyssey World Elite Mastercard
    cards.append(CreditCard(
        id="desjardins_odyssey_we_mc",
        name="Desjardins Odyssey World Elite Mastercard",
        issuer="Desjardins",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.PREMIUM,
        annual_fee=130.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=2.0,
        welcome_bonus=200,
        reward_program="Bonusdollars",
        reward_categories=[
            RewardCategory("restaurants", 3.5),
            RewardCategory("transport", 3.5),
            RewardCategory("groceries", 2.0),
            RewardCategory("gas", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=4,
            nexus_credit=True,
        ),
    ))

    # 2. Desjardins Cash Back World Elite Mastercard
    cards.append(CreditCard(
        id="desjardins_cashback_we_mc",
        name="Desjardins Cash Back World Elite Mastercard",
        issuer="Desjardins",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=100.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=150,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 4.0, cap_monthly=1000),
            RewardCategory("gas", 4.0, cap_monthly=1000),
            RewardCategory("restaurants", 2.0),
            RewardCategory("online", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 3. Desjardins Odyssey Gold Visa Infinite
    cards.append(CreditCard(
        id="desjardins_odyssey_gold_visa",
        name="Desjardins Odyssey Gold Visa Infinite",
        issuer="Desjardins",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=130.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=150,
        reward_program="Bonusdollars",
        reward_categories=[
            RewardCategory("restaurants", 3.0),
            RewardCategory("transport", 3.0),
            RewardCategory("groceries", 1.5),
            RewardCategory("gas", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=True),
    ))

    # 4. Desjardins Visa Modulo (no fee)
    cards.append(CreditCard(
        id="desjardins_visa_modulo",
        name="Desjardins Visa Modulo",
        issuer="Desjardins",
        network=CardNetwork.VISA,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Bonusdollars",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 5. Desjardins Carte du Campus Visa (student)
    cards.append(CreditCard(
        id="desjardins_campus_visa",
        name="Desjardins Carte du Campus Visa",
        issuer="Desjardins",
        network=CardNetwork.VISA,
        tier=CardTier.STUDENT,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=600,
        student_only=True,
        base_rate=1.0,
        welcome_bonus=25,
        reward_program="Bonusdollars",
        reward_categories=[
            RewardCategory("groceries", 1.5),
            RewardCategory("pharmacy", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 6. Desjardins Visa Flexi (low rate)
    cards.append(CreditCard(
        id="desjardins_visa_flexi",
        name="Desjardins Visa Flexi",
        issuer="Desjardins",
        network=CardNetwork.VISA,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=10.9,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# BANQUE NATIONALE CARDS
# ============================================================================

def get_bnc_cards() -> List[CreditCard]:
    cards = []

    # 1. BNC Mastercard World Elite
    cards.append(CreditCard(
        id="bnc_world_elite_mc",
        name="Banque Nationale Mastercard World Elite",
        issuer="Banque Nationale",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.PREMIUM,
        annual_fee=150.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.5,
        welcome_bonus=300,
        reward_program="À la carte Rewards",
        reward_categories=[
            RewardCategory("restaurants", 5.0),
            RewardCategory("subscriptions", 2.0),
            RewardCategory("groceries", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=4,
            nexus_credit=True,
            travel_credit_annual=150,
        ),
    ))

    # 2. BNC Syncro Mastercard (no fee)
    cards.append(CreditCard(
        id="bnc_syncro_mc",
        name="Banque Nationale Syncro Mastercard",
        issuer="Banque Nationale",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="À la carte Rewards",
        reward_categories=[
            RewardCategory("subscriptions", 1.5),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 3. BNC Mastercard Platine
    cards.append(CreditCard(
        id="bnc_platine_mc",
        name="Banque Nationale Mastercard Platine",
        issuer="Banque Nationale",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=89.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=35000,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.5,
        welcome_bonus=150,
        reward_program="À la carte Rewards",
        reward_categories=[
            RewardCategory("restaurants", 2.0),
            RewardCategory("groceries", 2.0),
            RewardCategory("gas", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 4. BNC À Ta Main Visa (student/basic)
    cards.append(CreditCard(
        id="bnc_atamain_visa",
        name="Banque Nationale À Ta Main Visa",
        issuer="Banque Nationale",
        network=CardNetwork.VISA,
        tier=CardTier.STUDENT,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=600,
        base_rate=0.5,
        welcome_bonus=25,
        reward_program="Cashback",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# TANGERINE CARDS
# ============================================================================

def get_tangerine_cards() -> List[CreditCard]:
    cards = []

    # 1. Tangerine Money-Back Credit Card
    cards.append(CreditCard(
        id="tangerine_money_back",
        name="Tangerine Money-Back Credit Card",
        issuer="Tangerine",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.95,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=0.5,
        welcome_bonus=50,
        reward_program="Cashback",
        reward_categories=[
            # 2% on 3 chosen categories — using most popular defaults
            RewardCategory("groceries", 2.0),
            RewardCategory("restaurants", 2.0),
            RewardCategory("gas", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# ROGERS / FIDO CARDS
# ============================================================================

def get_rogers_cards() -> List[CreditCard]:
    cards = []

    # 1. Rogers World Elite Mastercard (no FX fees effectively)
    cards.append(CreditCard(
        id="rogers_world_elite_mc",
        name="Rogers World Elite Mastercard",
        issuer="Rogers Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.5,
        welcome_bonus=25,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("subscriptions", 3.0),  # Rogers/Shaw/Fido
            RewardCategory("groceries", 2.0),
            RewardCategory("gas", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. Rogers Red Mastercard
    cards.append(CreditCard(
        id="rogers_red_mc",
        name="Rogers Red Mastercard",
        issuer="Rogers Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=20,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("subscriptions", 2.0),  # Rogers/Shaw/Fido
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 3. Fido Mastercard
    cards.append(CreditCard(
        id="fido_mc",
        name="Fido Mastercard",
        issuer="Rogers Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=20,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("subscriptions", 2.0),  # Fido charges
            RewardCategory("restaurants", 1.5),
            RewardCategory("gas", 1.5),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# PC FINANCIAL CARDS
# ============================================================================

def get_pc_cards() -> List[CreditCard]:
    cards = []

    # Note: 10,000 PC Optimum pts = $10 (0.1 cent/pt)
    # So 45 pts/$ = 4.5%, 30 pts/$ = 3%, 25 pts/$ = 2.5%, 10 pts/$ = 1%

    # 1. PC World Elite Mastercard
    cards.append(CreditCard(
        id="pc_world_elite_mc",
        name="PC World Elite Mastercard",
        issuer="PC Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.97,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=200,
        reward_program="PC Optimum",
        reward_categories=[
            RewardCategory("groceries", 4.5),  # Loblaws, Real Canadian Superstore
            RewardCategory("pharmacy", 3.0),   # Shoppers Drug Mart
            RewardCategory("gas", 1.0),        # Esso/Mobil
            RewardCategory("transport", 2.5),  # PC Travel
        ],
        grocery_stores=["Loblaws", "Real Canadian Superstore", "No Frills", "Provigo", "Maxi", "Extra Foods"],
        gas_stations=["Esso", "Mobil"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. PC World Mastercard
    cards.append(CreditCard(
        id="pc_world_mc",
        name="PC World Mastercard",
        issuer="PC Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.97,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="PC Optimum",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("pharmacy", 2.5),
            RewardCategory("gas", 1.0),
        ],
        grocery_stores=["Loblaws", "Real Canadian Superstore", "No Frills", "Provigo", "Maxi"],
        gas_stations=["Esso", "Mobil"],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 3. PC Mastercard (basic)
    cards.append(CreditCard(
        id="pc_mc",
        name="PC Mastercard",
        issuer="PC Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.97,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="PC Optimum",
        reward_categories=[
            RewardCategory("groceries", 2.5),
            RewardCategory("gas", 1.0),
        ],
        grocery_stores=["Loblaws", "Real Canadian Superstore", "No Frills", "Provigo", "Maxi"],
        gas_stations=["Esso", "Mobil"],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# NEO FINANCIAL CARDS
# ============================================================================

def get_neo_cards() -> List[CreditCard]:
    cards = []

    # 1. Neo Mastercard (no fee)
    cards.append(CreditCard(
        id="neo_mc",
        name="Neo Mastercard",
        issuer="Neo Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=600,
        base_rate=0.5,
        welcome_bonus=25,
        reward_program="Cashback",
        reward_categories=[
            # 5%+ at Neo partner merchants (average)
            RewardCategory("groceries", 5.0),
            RewardCategory("restaurants", 5.0),
            RewardCategory("gas", 5.0),
            RewardCategory("online", 5.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. Neo World Elite Mastercard
    cards.append(CreditCard(
        id="neo_world_elite_mc",
        name="Neo World Elite Mastercard",
        issuer="Neo Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=99.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=150,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 7.0),
            RewardCategory("restaurants", 7.0),
            RewardCategory("gas", 5.0),
            RewardCategory("online", 5.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# AMAZON (MBNA) CARDS
# ============================================================================

def get_amazon_cards() -> List[CreditCard]:
    cards = []

    # 1. Amazon.ca Rewards Mastercard (Prime members)
    cards.append(CreditCard(
        id="amazon_rewards_mc",
        name="Amazon.ca Rewards Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("online", 2.5),  # Amazon.ca
            RewardCategory("groceries", 1.5),
            RewardCategory("gas", 1.5),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. Amazon.ca Mastercard (basic)
    cards.append(CreditCard(
        id="amazon_mc",
        name="Amazon.ca Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=30,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("online", 1.5),  # Amazon.ca
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# MBNA CARDS
# ============================================================================

def get_mbna_cards() -> List[CreditCard]:
    cards = []

    # 1. MBNA True Line Mastercard (low rate, no rewards)
    cards.append(CreditCard(
        id="mbna_true_line_mc",
        name="MBNA True Line Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=12.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. MBNA True Line Gold Mastercard (very low rate)
    cards.append(CreditCard(
        id="mbna_true_line_gold_mc",
        name="MBNA True Line Gold Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.NO_FEE,
        annual_fee=39.0,
        first_year_free=False,
        interest_rate=8.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 3. MBNA Rewards World Elite Mastercard
    cards.append(CreditCard(
        id="mbna_rewards_we_mc",
        name="MBNA Rewards World Elite Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=120.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,
        welcome_bonus=300,
        reward_program="MBNA Rewards",
        reward_categories=[
            RewardCategory("restaurants", 5.0),
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False, nexus_credit=True),
    ))

    # 4. MBNA Rewards Platinum Plus Mastercard (no fee)
    cards.append(CreditCard(
        id="mbna_rewards_pp_mc",
        name="MBNA Rewards Platinum Plus Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="MBNA Rewards",
        reward_categories=[
            RewardCategory("restaurants", 2.0),
            RewardCategory("groceries", 2.0),
            RewardCategory("pharmacy", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 5. MBNA Smart Cash Platinum Plus Mastercard (no fee)
    cards.append(CreditCard(
        id="mbna_smart_cash_mc",
        name="MBNA Smart Cash Platinum Plus Mastercard",
        issuer="MBNA",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.0,
        welcome_bonus=75,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries", 2.0, cap_monthly=500),
            RewardCategory("gas", 2.0, cap_monthly=500),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# CAPITAL ONE CARDS
# ============================================================================

def get_capital_one_cards() -> List[CreditCard]:
    cards = []

    # 1. Capital One Quicksilver Mastercard
    cards.append(CreditCard(
        id="capital_one_quicksilver",
        name="Capital One Quicksilver Mastercard",
        issuer="Capital One",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.8,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=1.5,
        welcome_bonus=25,
        reward_program="Cashback",
        reward_categories=[],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. Capital One Platinum Mastercard (credit building)
    cards.append(CreditCard(
        id="capital_one_platinum",
        name="Capital One Platinum Mastercard",
        issuer="Capital One",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.NO_FEE,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.8,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=580,
        base_rate=0.0,
        welcome_bonus=0,
        reward_program="None",
        reward_categories=[],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# TRIANGLE (CANADIAN TIRE) CARDS
# ============================================================================

def get_triangle_cards() -> List[CreditCard]:
    cards = []

    # 1. Triangle World Elite Mastercard
    cards.append(CreditCard(
        id="triangle_world_elite_mc",
        name="Triangle World Elite Mastercard",
        issuer="Canadian Tire Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.5,
        welcome_bonus=75,
        reward_program="CT Money",
        reward_categories=[
            RewardCategory("groceries", 4.0),   # Canadian Tire stores + groceries
            RewardCategory("gas", 3.0),          # Canadian Tire Gas+/Gas stations
            RewardCategory("pharmacy", 2.0),
        ],
        gas_stations=["Canadian Tire", "Gas+"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 2. Triangle World Mastercard
    cards.append(CreditCard(
        id="triangle_world_mc",
        name="Triangle World Mastercard",
        issuer="Canadian Tire Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=0.5,
        welcome_bonus=50,
        reward_program="CT Money",
        reward_categories=[
            RewardCategory("groceries", 3.0),
            RewardCategory("gas", 2.0),
        ],
        gas_stations=["Canadian Tire", "Gas+"],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=False,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # 3. Triangle Mastercard (basic)
    cards.append(CreditCard(
        id="triangle_mc",
        name="Triangle Mastercard",
        issuer="Canadian Tire Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.REWARDS,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=25,
        reward_program="CT Money",
        reward_categories=[
            RewardCategory("groceries", 2.0),
            RewardCategory("gas", 1.5),
        ],
        gas_stations=["Canadian Tire", "Gas+"],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# HOME TRUST CARDS
# ============================================================================

def get_home_trust_cards() -> List[CreditCard]:
    cards = []

    # 1. Home Trust Preferred Visa (no FX fees)
    cards.append(CreditCard(
        id="home_trust_preferred_visa",
        name="Home Trust Preferred Visa",
        issuer="Home Trust",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=1.0,
        welcome_bonus=25,
        reward_program="Cashback",
        reward_categories=[],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# SIMPLII FINANCIAL CARDS
# ============================================================================

def get_simplii_cards() -> List[CreditCard]:
    cards = []

    # 1. Simplii Financial Cash Back Visa Card
    cards.append(CreditCard(
        id="simplii_cashback_visa",
        name="Simplii Financial Cash Back Visa Card",
        issuer="Simplii Financial",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=0.5,
        welcome_bonus=75,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("restaurants", 4.0, cap_annual=5000),
            RewardCategory("gas", 1.5),
            RewardCategory("pharmacy", 1.5),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# NOUVELLES CARTES (ajoutées mars 2026)
# Sources: sites officiels banques, ratehub.ca, milesopedia.com, finlywealth.com
# ============================================================================

def get_new_cards() -> List[CreditCard]:
    """Cartes manquantes ajoutées pour compléter la couverture FinlyWealth."""
    cards = []

    # ── SCOTIABANK ─────────────────────────────────────────────────────────

    # Scotia Momentum Visa Infinite — carte cashback la plus populaire de Scotia
    # 4% épicerie+récurrents (cap 25K$), 2% essence+transit, 1% autre
    cards.append(CreditCard(
        id="scotia_momentum_infinite",
        name="Scotia Momentum Visa Infinite",
        issuer="Banque Scotia",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=200,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     4.0, cap_monthly=2083),  # 25K$/an
            RewardCategory("subscriptions", 4.0, cap_monthly=2083),  # récurrents
            RewardCategory("gas",           2.0),
            RewardCategory("transport",     2.0),
            RewardCategory("restaurants",   2.0),  # food delivery = 2%
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=False,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    # Scotia Momentum No-Fee Visa — entrée de gamme cashback sans frais
    cards.append(CreditCard(
        id="scotia_momentum_nofee",
        name="Scotia Momentum No-Fee Visa",
        issuer="Banque Scotia",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     1.0),
            RewardCategory("gas",           1.0),
            RewardCategory("pharmacy",      1.0),
            RewardCategory("subscriptions", 1.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(),
    ))

    # ── TANGERINE ───────────────────────────────────────────────────────────

    # Tangerine World Mastercard — $0 frais, 2% sur 2-3 catégories au choix
    cards.append(CreditCard(
        id="tangerine_world_mc",
        name="Tangerine Money-Back World Mastercard",
        issuer="Tangerine",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.95,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=680,
        base_rate=0.5,
        welcome_bonus=120,
        reward_program="Cashback",
        reward_categories=[
            # Utilisateur choisit 2-3 catégories parmi 13 — modélisé sur les plus communes
            RewardCategory("groceries",     2.0),
            RewardCategory("restaurants",   2.0),
            RewardCategory("gas",           2.0),
            RewardCategory("pharmacy",      2.0),
            RewardCategory("subscriptions", 2.0),
            RewardCategory("transport",     2.0),
            RewardCategory("entertainment", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(),
    ))

    # ── WEALTHSIMPLE ────────────────────────────────────────────────────────

    # Wealthsimple Visa Infinite — 2% flat partout, $240/an (waivable)
    cards.append(CreditCard(
        id="wealthsimple_infinite",
        name="Wealthsimple Visa Infinite",
        issuer="Wealthsimple",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=240.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        no_fx_fee=True,
        base_rate=2.0,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[],  # Flat 2% partout, pas de catégories bonus
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            purchase_protection=True,
            extended_warranty=True,
            mobile_device=True,
        ),
        travel_perks=TravelPerks(),
    ))

    # ── ROGERS ──────────────────────────────────────────────────────────────

    # Rogers Red World Elite Mastercard — $0 frais, 1.5-2% partout
    cards.append(CreditCard(
        id="rogers_red_world_elite_mc",
        name="Rogers Red World Elite Mastercard",
        issuer="Rogers Bank",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=700,
        base_rate=1.5,   # 1.5% si non-client Rogers, 2% si client Rogers/Fido
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("online", 3.0),  # 3% USD
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(),
    ))

    # ── CIBC ────────────────────────────────────────────────────────────────

    # CIBC Aeroplan Visa — carte Aéroplan sans frais, entrée de gamme
    cards.append(CreditCard(
        id="cibc_aeroplan_visa",
        name="CIBC Aeroplan Visa",
        issuer="CIBC",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=660,
        base_rate=0.67,  # 1pt per $1.50 = ~0.67pt/$ × 1.2¢ = 0.8%
        welcome_bonus=160,  # 10 000 pts Aéroplan ≈ $120-160 valeur
        reward_program="Aéroplan",
        reward_categories=[
            RewardCategory("groceries", 1.0),   # 1pt/$
            RewardCategory("gas",       1.0),   # 1pt/$
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(),
    ))

    # ── NEO FINANCIAL ───────────────────────────────────────────────────────

    # Neo World Mastercard — $0 frais, 2% groceries/gas/récurrents
    cards.append(CreditCard(
        id="neo_world_mc",
        name="Neo World Mastercard",
        issuer="Neo Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=650,
        base_rate=0.5,
        welcome_bonus=25,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     2.0),
            RewardCategory("gas",           2.0),
            RewardCategory("subscriptions", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(),
    ))

    # Neo Cathay World Elite Mastercard — 1 Asia Mile/$, prime Cathay Pacific
    cards.append(CreditCard(
        id="neo_cathay_world_elite",
        name="Cathay World Elite Mastercard",
        issuer="Neo Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=180.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,   # 1 Asia Mile/$ (CPP ~1.2-1.5¢)
        welcome_bonus=750,  # ~60 000 Asia Miles ≈ $600-900 selon rachat
        reward_program="Asia Miles",
        reward_categories=[
            RewardCategory("online", 2.0),  # 2x en devises étrangères
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=True, lounge_visits_per_year=4),
    ))

    # ── KOHO ────────────────────────────────────────────────────────────────
    # Note: KOHO est une carte prépayée/de débit Mastercard, pas un crédit traditionnel.
    # Inclus car FinlyWealth les liste et ils sont très populaires.
    # Interest rate N/A (prépayé), mais on utilise 0 pour signifier pas d'intérêt.

    # KOHO Essential — entrée de gamme, 1% épicerie+dining+transport
    cards.append(CreditCard(
        id="koho_essential",
        name="KOHO Essential Mastercard",
        issuer="KOHO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,   # Gratuit avec dépôt direct, sinon ~$48
        first_year_free=False,
        interest_rate=0.0,  # Prépayé = pas d'intérêt
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=0,   # Approbation garantie (prépayé)
        no_fx_fee=True,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     1.0),
            RewardCategory("restaurants",   1.0),
            RewardCategory("transport",     1.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(),
        travel_perks=TravelPerks(),
    ))

    # KOHO Extra — 1.5% épicerie+dining+transport + 0.25% autre
    cards.append(CreditCard(
        id="koho_extra",
        name="KOHO Extra Mastercard",
        issuer="KOHO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=144.0,  # $12/mois ou $144/an
        first_year_free=False,
        interest_rate=0.0,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=0,
        no_fx_fee=True,
        base_rate=0.25,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     1.5),
            RewardCategory("restaurants",   1.5),
            RewardCategory("transport",     1.5),
        ],
        compatible_with_costco=True,
        insurance=Insurance(),
        travel_perks=TravelPerks(),
    ))

    # KOHO Everything — 2% catégories principales, sans frais FX
    cards.append(CreditCard(
        id="koho_everything",
        name="KOHO Everything Mastercard",
        issuer="KOHO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=228.0,  # ~$19/mois ou $228/an
        first_year_free=False,
        interest_rate=0.0,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=0,
        no_fx_fee=True,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     2.0),
            RewardCategory("restaurants",   2.0),
            RewardCategory("transport",     2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(),
        travel_perks=TravelPerks(),
    ))

    # ── BRIM FINANCIAL ──────────────────────────────────────────────────────

    # Brim Mastercard — $0, 1% flat, frais FX 1.5% (anciennement 0%)
    cards.append(CreditCard(
        id="brim_mc",
        name="BRIM Mastercard",
        issuer="Brim Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=1.0,
        welcome_bonus=50,
        reward_program="Cashback",
        reward_categories=[],  # Flat 1% partout
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(),
    ))

    # Brim World Elite Mastercard — $89, 2% flat, $80K revenu
    cards.append(CreditCard(
        id="brim_world_elite",
        name="BRIM World Elite Mastercard",
        issuer="Brim Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=89.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=700,
        base_rate=2.0,
        welcome_bonus=100,
        reward_program="Cashback",
        reward_categories=[],  # Flat 2% partout
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=True, lounge_visits_per_year=4),
    ))

    # ── BMO VIPorter ────────────────────────────────────────────────────────

    # BMO VIPorter Mastercard — $89 (1re année gratuite), Porter Airlines
    cards.append(CreditCard(
        id="bmo_viporter_mc",
        name="BMO VIPorter Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=89.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=660,
        base_rate=0.5,   # 0.5pt/$ × 1.0¢ = 0.5%
        welcome_bonus=320,  # ~40 000 VIPorter pts ≈ $320
        reward_program="VIPorter Points",
        reward_categories=[
            RewardCategory("transport",     1.0),  # 1pt/$ transports
            RewardCategory("gas",           1.0),
            RewardCategory("groceries",     1.0),
            RewardCategory("restaurants",   1.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(first_bag_free=False),
    ))

    # BMO VIPorter World Elite Mastercard — $199 (1re année gratuite), premium Porter
    cards.append(CreditCard(
        id="bmo_viporter_world_elite",
        name="BMO VIPorter World Elite Mastercard",
        issuer="BMO",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=199.0,
        first_year_free=True,
        interest_rate=20.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=1.0,   # 1pt/$ × 1.0¢ = 1%
        welcome_bonus=560,  # ~70 000 VIPorter pts ≈ $560
        reward_program="VIPorter Points",
        reward_categories=[
            RewardCategory("groceries",     2.0, cap_monthly=833),   # cap $10K/an combiné dining
            RewardCategory("restaurants",   2.0, cap_monthly=833),
            RewardCategory("gas",           2.0, cap_monthly=417),   # cap $5K/an combiné transport
            RewardCategory("transport",     2.0, cap_monthly=417),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(
            lounge_access=True,
            lounge_visits_per_year=6,
            companion_pass=True,
        ),
    ))

    # ── TIM HORTONS ─────────────────────────────────────────────────────────

    # Tims Mastercard — $0 frais, Tims Rewards
    # 5pts/$ épicerie+essence+transit (cap $20K), 1pt/$2 autre
    # 5pts × 0.4¢ = 2% effectif sur épicerie/essence/transit
    cards.append(CreditCard(
        id="tims_mc",
        name="Tims Mastercard",
        issuer="Tims Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.2,   # 1pt/$2 × 0.4¢ = 0.2%
        welcome_bonus=0,
        reward_program="Tims Rewards",
        reward_categories=[
            RewardCategory("groceries",  2.0, cap_monthly=1667),  # cap $20K/an
            RewardCategory("gas",        2.0, cap_monthly=1667),
            RewardCategory("transport",  2.0, cap_monthly=1667),
            RewardCategory("restaurants", 6.0),  # 15pts/$ Tim Hortons ≈ 6% effectif
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(),
    ))

    # ── ATB FINANCIAL (Alberta seulement) ───────────────────────────────────

    # ATB Gold Cash Rewards Mastercard — $0, 2% épicerie+dining+streaming
    cards.append(CreditCard(
        id="atb_gold_cash_rewards",
        name="ATB Gold Cash Rewards Mastercard",
        issuer="ATB Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     2.0),
            RewardCategory("restaurants",   2.0),
            RewardCategory("subscriptions", 2.0),  # digital streaming
            RewardCategory("gas",           1.0),
            RewardCategory("online",        1.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True, extended_warranty=True),
        travel_perks=TravelPerks(),
    ))

    # ATB Gold My Rewards Mastercard — $0, points ATB My Rewards
    cards.append(CreditCard(
        id="atb_gold_my_rewards",
        name="ATB Gold My Rewards Mastercard",
        issuer="ATB Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=1.0,   # 1pt/$ × 1.0¢
        welcome_bonus=0,
        reward_program="ATB My Rewards",
        reward_categories=[
            RewardCategory("groceries",   2.0),
            RewardCategory("restaurants", 2.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(),
    ))

    # ATB World Elite Mastercard — $120, 8pts voyage, 6pts épicerie+essence+stream+divert
    # 8pts × ~0.01¢/pt = 8% voyage, 6pts = 6% épicerie/essence/streaming/entertainment
    cards.append(CreditCard(
        id="atb_world_elite",
        name="ATB World Elite Mastercard",
        issuer="ATB Financial",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.TRAVEL,
        annual_fee=120.0,
        first_year_free=False,
        interest_rate=19.99,
        min_income_personal=80000,
        min_income_household=150000,
        min_credit_score=720,
        base_rate=2.0,   # 2pts/$ × 1.0¢
        welcome_bonus=200,
        reward_program="ATB My Rewards",
        reward_categories=[
            RewardCategory("groceries",     6.0),
            RewardCategory("gas",           6.0),
            RewardCategory("subscriptions", 6.0),
            RewardCategory("entertainment", 6.0),
            RewardCategory("transport",     8.0),  # airline/hotel/car rental
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=True, lounge_visits_per_year=6),
    ))

    # ── MERIDIAN CREDIT UNION (Ontario seulement) ────────────────────────────

    # Meridian Visa Infinite Cash Back — $99 (1re année gratuite), 4% épicerie+essence
    cards.append(CreditCard(
        id="meridian_cashback_infinite",
        name="Meridian Visa Infinite Cash Back",
        issuer="Meridian Credit Union",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=99.0,
        first_year_free=True,
        interest_rate=19.50,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.0,
        welcome_bonus=100,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",     4.0, cap_monthly=2083),  # cap $25K/an combiné
            RewardCategory("gas",           4.0, cap_monthly=2083),
            RewardCategory("pharmacy",      2.0, cap_monthly=2083),
            RewardCategory("subscriptions", 2.0, cap_monthly=2083),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            purchase_protection=True,
            extended_warranty=True,
            car_rental=True,
        ),
        travel_perks=TravelPerks(),
    ))

    # ── BANQUE NATIONALE ────────────────────────────────────────────────────

    # National Bank Platinum Mastercard — ~$115, 2pts épicerie+restaurants
    cards.append(CreditCard(
        id="bnc_platinum_mc",
        name="National Bank Platinum Mastercard",
        issuer="Banque Nationale",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=115.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=680,
        base_rate=1.0,   # 1pt/$
        welcome_bonus=100,
        reward_program="À la carte Rewards",
        reward_categories=[
            RewardCategory("groceries",     2.0),
            RewardCategory("restaurants",   2.0),
            RewardCategory("gas",           1.5),
            RewardCategory("subscriptions", 1.5),
        ],
        compatible_with_costco=True,
        insurance=Insurance(
            travel_medical=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(),
    ))

    # National Bank mycredit Mastercard — $0, 1% restaurants+préautorisés
    cards.append(CreditCard(
        id="bnc_mycredit_mc",
        name="National Bank mycredit Mastercard",
        issuer="Banque Nationale",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=20.99,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("restaurants",   1.0),
            RewardCategory("subscriptions", 1.0),  # paiements préautorisés
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(),
    ))

    # ── DESJARDINS (cartes manquantes) ──────────────────────────────────────

    # Desjardins Bonus Visa — $0, cashback de base
    cards.append(CreditCard(
        id="desjardins_bonus_visa",
        name="Desjardins Bonus Visa",
        issuer="Desjardins",
        network=CardNetwork.VISA,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.90,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="BONUSDOLLARS",
        reward_categories=[
            RewardCategory("groceries", 1.0),
            RewardCategory("gas",       1.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(),
    ))

    # Desjardins Cash Back Mastercard — $0, 1% partout
    cards.append(CreditCard(
        id="desjardins_cashback_mc",
        name="Desjardins Cash Back Mastercard",
        issuer="Desjardins",
        network=CardNetwork.MASTERCARD,
        tier=CardTier.CASHBACK,
        annual_fee=0.0,
        first_year_free=False,
        interest_rate=19.90,
        min_income_personal=0,
        min_income_household=0,
        min_credit_score=640,
        base_rate=0.5,
        welcome_bonus=0,
        reward_program="Cashback",
        reward_categories=[
            RewardCategory("groceries",   1.0),
            RewardCategory("gas",         1.0),
            RewardCategory("restaurants", 1.0),
        ],
        compatible_with_costco=True,
        insurance=Insurance(purchase_protection=True),
        travel_perks=TravelPerks(),
    ))

    # Desjardins Odyssey Visa Infinite — tier entre Gold et World Elite
    # ~$130/an, 2.5% voyage + 2% épicerie, couverture 60 jours médicale
    cards.append(CreditCard(
        id="desjardins_odyssey_infinite",
        name="Desjardins Odyssey Visa Infinite",
        issuer="Desjardins",
        network=CardNetwork.VISA,
        tier=CardTier.TRAVEL,
        annual_fee=130.0,
        first_year_free=False,
        interest_rate=20.90,
        min_income_personal=60000,
        min_income_household=100000,
        min_credit_score=700,
        base_rate=1.5,
        welcome_bonus=150,
        reward_program="BONUSDOLLARS",
        reward_categories=[
            RewardCategory("transport",     2.5),   # voyage/transport
            RewardCategory("groceries",     2.0),
            RewardCategory("restaurants",   2.0),
            RewardCategory("entertainment", 2.0),
        ],
        compatible_with_costco=False,
        insurance=Insurance(
            travel_medical=True,
            travel_cancellation=True,
            travel_interruption=True,
            baggage=True,
            car_rental=True,
            purchase_protection=True,
            extended_warranty=True,
        ),
        travel_perks=TravelPerks(lounge_access=False),
    ))

    return cards


# ============================================================================
# MAIN FUNCTION
# ============================================================================

# Durées réelles d'assurance médicale voyage par carte (jours).
# Sources: guides officiels des émetteurs, ratehub.ca, milesopedia.com (2025).
# Les cartes non listées ont travel_medical_days = 0 (pas de couverture).
TRAVEL_MEDICAL_DAYS_MAP = {
    # American Express
    "amex_cobalt":              15,
    "amex_gold":                15,
    "amex_platinum":            31,   # Platinum = couverture la plus longue chez Amex
    "amex_simplycash_preferred": 15,
    "amex_aeroplan":            15,
    "amex_aeroplan_reserve":    15,
    # RBC
    "rbc_avion_infinite":       15,
    "rbc_avion_platinum":       15,
    "rbc_avion_privilege":      31,   # Privilege = carte ultra-premium
    "rbc_ba_infinite":          15,
    "rbc_us_gold":              15,
    "rbc_westjet_we":           15,
    # TD
    "td_aeroplan_infinite":     21,
    "td_aeroplan_infinite_privilege": 31,
    "td_aeroplan_platinum":     10,
    "td_first_class_travel":    21,
    "td_cashback_infinite":     10,
    "td_platinum_travel":       10,
    # BMO
    "bmo_world_elite_mc":       21,
    "bmo_cashback_we_mc":       21,
    "bmo_eclipse_infinite":     10,
    "bmo_ascend_we_mc":         21,
    "bmo_air_miles_we_mc":      15,
    # CIBC
    "cibc_aeroplan_infinite":   15,
    "cibc_aeroplan_infinite_privilege": 31,
    "cibc_aventura_infinite":   10,
    "cibc_dividend_infinite":   10,
    "cibc_dividend_platinum":   10,
    # Scotiabank
    "scotia_passport_infinite": 25,
    "scotia_gold_amex":         25,
    "scotia_platinum_amex":     25,
    # Desjardins (couvertures exceptionnellement longues — meilleure au Canada)
    "desjardins_odyssey_we_mc": 60,
    "desjardins_cashback_we_mc": 60,
    "desjardins_odyssey_gold_visa": 60,
    # Banque Nationale
    "bnc_world_elite_mc":       60,   # BNC = aussi 60j comme Desjardins
    "bnc_platine_mc":           15,
    # Rogers / Fido / PC / Neo
    "rogers_world_elite_mc":    10,
    "pc_world_elite_mc":        15,
    "neo_world_elite_mc":       15,
    # MBNA
    "mbna_rewards_we_mc":       15,
    # Canadian Tire Triangle
    "triangle_world_elite_mc":  10,
    "triangle_world_mc":        10,
    # Nouvelles cartes ajoutées mars 2026
    "scotia_momentum_infinite":     25,
    "wealthsimple_infinite":        15,
    "brim_world_elite":             10,
    "bmo_viporter_mc":              10,
    "bmo_viporter_world_elite":     21,
    "atb_world_elite":              15,
    "meridian_cashback_infinite":   15,
    "rogers_red_world_elite_mc":    10,
    "bnc_platinum_mc":              15,
    "neo_cathay_world_elite":       15,
    "desjardins_odyssey_infinite":  60,
}


def get_all_cards() -> List[CreditCard]:
    """Retourne toutes les cartes de crédit dans la base de données."""
    all_cards = (
        get_amex_cards() +
        get_rbc_cards() +
        get_td_cards() +
        get_bmo_cards() +
        get_cibc_cards() +
        get_scotia_cards() +
        get_desjardins_cards() +
        get_bnc_cards() +
        get_tangerine_cards() +
        get_rogers_cards() +
        get_pc_cards() +
        get_neo_cards() +
        get_amazon_cards() +
        get_mbna_cards() +
        get_capital_one_cards() +
        get_triangle_cards() +
        get_home_trust_cards() +
        get_simplii_cards() +
        get_new_cards()
    )
    # Appliquer les durées d'assurance médicale voyage connues
    for card in all_cards:
        if card.id in TRAVEL_MEDICAL_DAYS_MAP:
            card.insurance.travel_medical_days = TRAVEL_MEDICAL_DAYS_MAP[card.id]
    return all_cards


def get_card_by_id(card_id: str) -> Optional[CreditCard]:
    """Retourne une carte spécifique par son ID"""
    for card in get_all_cards():
        if card.id == card_id:
            return card
    return None


def get_cards_by_network(network: CardNetwork) -> List[CreditCard]:
    """Retourne toutes les cartes d'un réseau donné"""
    return [card for card in get_all_cards() if card.network == network]


def get_cards_by_tier(tier: CardTier) -> List[CreditCard]:
    """Retourne toutes les cartes d'une catégorie donnée"""
    return [card for card in get_all_cards() if card.tier == tier]


if __name__ == "__main__":
    # Test rapide
    cards = get_all_cards()
    amex_cards = get_amex_cards()

    print(f"Nombre total de cartes: {len(cards)}")
    print(f"Nombre de cartes Amex: {len(amex_cards)}")

    print("\n=== CARTES AMERICAN EXPRESS ===\n")
    for card in amex_cards:
        print(f"• {card.name}")
        print(f"  Frais: {card.annual_fee}$ | Taux de base: {card.base_rate}%")
        print(f"  Programme: {card.reward_program}")
        print(f"  Bonus: {card.welcome_bonus}$")
        if card.reward_categories:
            print(f"  Catégories bonus:")
            for cat in card.reward_categories:
                cap = f" (max {cat.cap_monthly}$/mois)" if cat.cap_monthly else ""
                print(f"    - {cat.category}: {cat.rate}%{cap}")
        print()
