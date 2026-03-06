"""
Moteur de recommandation de cartes de crédit
Calcule le ROI et recommande les meilleures cartes selon le profil
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from card_database import CreditCard, CardNetwork, CardTier, get_all_cards
from questionnaire import UserProfile


@dataclass
class CardRecommendation:
    """Résultat d'une recommandation"""
    card: CreditCard
    score: float  # Score de 0-100
    annual_roi: float  # ROI annuel estimé en $
    match_percentage: float  # Pourcentage de match avec le profil
    reasons: List[str]  # Pourquoi cette carte est recommandée
    warnings: List[str]  # Avertissements spécifiques
    already_has_benefits: List[str]  # Avantages déjà possédés


class RecommendationEngine:
    """Moteur de recommandation"""

    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.cards = get_all_cards()

    def recommend(self, num_results: int = 3) -> List[CardRecommendation]:
        """Génère les meilleures recommandations"""

        # Filtrer les cartes éligibles
        eligible_cards = self._filter_eligible_cards()

        # Calculer le ROI et le score pour chaque carte
        scored_cards = []
        for card in eligible_cards:
            roi = self._calculate_roi(card)
            score = self._calculate_score(card, roi)
            match_pct = self._calculate_match_percentage(card)
            reasons = self._get_reasons(card)
            warnings = self._get_warnings(card)
            already_has = self._get_already_has_benefits(card)

            scored_cards.append(CardRecommendation(
                card=card,
                score=score,
                annual_roi=roi,
                match_percentage=match_pct,
                reasons=reasons,
                warnings=warnings,
                already_has_benefits=already_has
            ))

        # Trier par score décroissant
        scored_cards.sort(key=lambda x: x.score, reverse=True)

        return scored_cards[:num_results]

    def _filter_eligible_cards(self) -> List[CreditCard]:
        """Filtre les cartes selon les critères d'éligibilité"""

        eligible = []
        credit_score = self._parse_credit_score()
        income_personal = self._parse_income(self.profile.income_personal)
        income_household = self._parse_income(self.profile.income_household)

        for card in self.cards:
            # Vérifier le score de crédit
            if credit_score < card.min_credit_score:
                continue

            # Vérifier le revenu personnel
            if income_personal > 0 and income_personal < card.min_income_personal:
                # Sauf si le revenu du ménage est suffisant
                if income_household < card.min_income_household:
                    continue

            # Vérifier si étudiant seulement
            if card.student_only and "Étudiant" not in self.profile.status:
                continue

            # Vérifier la préférence de réseau
            if self.profile.network_preference == "Visa" and card.network != CardNetwork.VISA:
                continue
            if self.profile.network_preference == "Mastercard" and card.network != CardNetwork.MASTERCARD:
                continue
            if self.profile.network_preference == "American Express" and card.network != CardNetwork.AMEX:
                continue

            # Vérifier Costco
            if self.profile.uses_costco in ["Oui, régulièrement", "Oui, occasionnellement"]:
                if not card.compatible_with_costco:
                    continue

            # Vérifier les institutions exclues
            if self.profile.excluded_institutions:
                if card.issuer.lower() in self.profile.excluded_institutions.lower():
                    continue

            eligible.append(card)

        return eligible

    def _calculate_roi(self, card: CreditCard) -> float:
        """
        Calcule le ROI annuel estimé pour une carte avec logique actuarielle avancée.

        Implémente:
        - Valeur CPP dynamique (1-2 cents par point selon usage)
        - Synergie RBC + Petro-Canada (3 sous/litre)
        - Valeur voyage proportionnelle aux voyages réels
        - Annulation assurances redondantes (employer_insurance)
        - Pénalité FX 2.5% sur dépenses en devises
        - Amortissement bonus selon stratégie de garde
        - Contrainte Loblaws/Amex (épicerie = 1x max)
        """

        spending = self._get_spending_dict()

        # A. Valeur des récompenses avec CPP dynamique
        rewards_value = self._calculate_rewards_value_dynamic(card, spending)

        # B. Bonus de bienvenue amorti selon stratégie
        welcome_bonus = self._amortize_welcome_bonus(card)

        # C. Avantages voyage (proportionnel aux voyages réels)
        travel_value = self._calculate_travel_value(card)

        # D. Assurances (avec annulation si redondant)
        insurance_value = self._calculate_insurance_value(card)

        # E. Crédits voyage
        travel_credit = card.travel_perks.travel_credit_annual

        # F. Synergie RBC + Petro-Canada
        petro_canada_synergy = self._calculate_petro_canada_synergy(card)

        # G. Pénalité FX (2.5% sur dépenses en devises)
        fx_penalty = self._calculate_fx_penalty(card)

        # H. Frais annuels
        annual_fee = card.annual_fee if not card.first_year_free else 0

        # Calcul final du ROI
        roi = (rewards_value + welcome_bonus + travel_value + insurance_value +
               travel_credit + petro_canada_synergy - fx_penalty - annual_fee)

        return round(roi, 2)

    def _calculate_rewards_value_dynamic(self, card: CreditCard, spending: Dict[str, float]) -> float:
        """
        Calcule la valeur des récompenses avec CPP dynamique.

        - Si points_valuation = "Transfert vers partenaires": multiplicateur 1.5-2.0x
        - Si Amex ET épicerie = Maxi/Provigo/Loblaws: taux épicerie tombe à 1x (base)
        """
        total_value = 0.0

        # Déterminer le multiplicateur CPP selon la préférence de points
        cpp_multiplier = self._get_cpp_multiplier(card)

        # Vérifier contrainte Loblaws/Amex
        amex_loblaws_constraint = self._check_amex_loblaws_constraint(card)

        for category, amount in spending.items():
            if amount <= 0:
                continue

            rate = card.get_reward_rate(category)

            # Appliquer contrainte Amex/Loblaws pour l'épicerie
            if category == "groceries" and amex_loblaws_constraint:
                rate = min(rate, 1.0)  # Tombe au taux de base 1x

            # Calculer la valeur annuelle avec CPP dynamique
            annual_spend = amount * 12
            base_reward = annual_spend * (rate / 100)

            # Appliquer CPP multiplier pour cartes de points (Amex MR, RBC Avion)
            if card.reward_program and ("MR" in card.reward_program or "Avion" in card.reward_program or
                                        "points" in card.reward_program.lower()):
                base_reward *= cpp_multiplier

            total_value += base_reward

        return total_value

    def _get_cpp_multiplier(self, card: CreditCard) -> float:
        """
        Retourne le multiplicateur CPP (Cents Per Point) selon la préférence utilisateur.

        - Crédit au compte / Cashback: 1.0x (1 cent/point)
        - Transfert vers partenaires aériens: 1.5-2.0x (1.5-2 cents/point)
        """
        if self.profile.points_valuation == "Transfert vers partenaires aériens comme Aéroplan/Avios (valeur = 1.5-2 cpp)":
            # Les points transférés valent typiquement 1.5-2 cents chacun
            return 1.75  # Valeur moyenne réaliste
        else:
            # Valeur de base (crédit au compte, cashback)
            return 1.0

    def _check_amex_loblaws_constraint(self, card: CreditCard) -> bool:
        """
        Vérifie si la contrainte Amex/Loblaws s'applique.

        Amex N'EST PAS accepté chez Maxi, Provigo, Loblaws.
        Si l'utilisateur magasine SEULEMENT chez ces commerces, le taux épicerie tombe à 1x.
        """
        if card.network != CardNetwork.AMEX:
            return False

        # Vérifier si l'utilisateur magasine exclusivement chez Loblaws/Maxi/Provigo
        grocery_stores_lower = [s.lower() for s in self.profile.grocery_stores]

        # Magasins où Amex n'est pas accepté
        amex_incompatible = ["maxi", "provigo", "loblaws", "real canadian superstore"]

        # Si TOUS les magasins fréquentés sont incompatibles avec Amex
        if grocery_stores_lower:
            all_incompatible = all(
                any(incompatible in store for incompatible in amex_incompatible)
                for store in grocery_stores_lower
            )
            return all_incompatible

        return False

    def _amortize_welcome_bonus(self, card: CreditCard) -> float:
        """
        Amortit le bonus de bienvenue selon la stratégie de garde de carte.

        - Churning (< 1 an): 100% du bonus
        - 1-2 ans: 75% du bonus
        - Long terme (3+ ans): 50% du bonus (amorti sur 3 ans)
        """
        if self.profile.card_strategy == "Moins d'un an (Churning)":
            return card.welcome_bonus * 1.0
        elif self.profile.card_strategy == "1-2 ans":
            return card.welcome_bonus * 0.75
        else:  # Long terme ou non spécifié
            return card.welcome_bonus * 0.50  # Amorti sur 2-3 ans

    def _calculate_petro_canada_synergy(self, card: CreditCard) -> float:
        """
        Calcule la synergie RBC + Petro-Canada.

        Si Carte = RBC ET stations = Petro-Canada:
        Ajoute ((spending_gas * 12) / 1.50) * 0.03
        (3 sous/litre économisés, avec prix moyen 1.50$/litre)
        """
        if "RBC" not in card.name and "Banque Royale" not in card.issuer:
            return 0.0

        gas_stations_lower = [s.lower() for s in self.profile.gas_stations]
        if "petro-canada" not in gas_stations_lower and "petro canada" not in gas_stations_lower:
            return 0.0

        spending_gas = self.profile.spending_gas
        if spending_gas <= 0:
            return 0.0

        # Calcul: (dépenses annuelles / 1.50$/litre) * 0.03$/litre
        annual_gas_spend = spending_gas * 12
        litres_per_year = annual_gas_spend / 1.50
        savings = litres_per_year * 0.03

        return savings

    def _calculate_travel_value(self, card: CreditCard) -> float:
        """
        Calcule la valeur des avantages voyage de manière proportionnelle.

        - Accès salon: trips_per_year * 50$ (valeur d'une entrée), plafonné au max de la carte
        - Premier bagage: nombre de vols * 30$
        - NEXUS/Global Entry: crédit amorti
        """
        value = 0.0

        # A. Accès salon - VALEUR PROPORTIONNELLE (trips * 50$, pas valeur statique)
        if card.travel_perks.lounge_access:
            trips = self.profile.trips_per_year
            if trips <= 0:
                trips = self._estimate_trips_from_frequency()

            # Valeur réelle = nombre de voyages * 50$ (prix d'une entrée Day Pass)
            lounge_value = trips * 50

            # Plafonner au maximum d'accès de la carte
            if card.travel_perks.lounge_visits_per_year > 0:
                max_lounge_value = card.travel_perks.lounge_visits_per_year * 50
                lounge_value = min(lounge_value, max_lounge_value)

            value += lounge_value

        # B. Premier bagage gratuit
        if card.travel_perks.first_bag_free and self._flies_air_canada():
            num_flights = self._estimate_num_flights()
            value += num_flights * 30  # ~30$ par bagage

        # C. NEXUS/Global Entry
        if card.travel_perks.nexus_credit or card.travel_perks.global_entry_credit:
            if self.profile.nexus_interest in ["Oui", "Je suis intéressé(e)"]:
                value += 50  # Amorti sur 5 ans

        # D. Crédits de voyage non-utilisés (ex: crédit hôtel)
        if card.travel_perks.travel_credit_annual > 0:
            value += card.travel_perks.travel_credit_annual

        return value

    def _estimate_trips_from_frequency(self) -> int:
        """Estime le nombre de voyages par an selon la fréquence"""
        mapping = {
            "Jamais ou presque": 0,
            "1 fois par an": 1,
            "2–3 fois par an": 2,
            "4–5 fois par an": 4,
            "6 fois et plus par an": 6,
        }
        return mapping.get(self.profile.travel_frequency, 1)

    def _calculate_insurance_value(self, card: CreditCard) -> float:
        """
        Calcule la valeur des assurances avec annulation des assurances redondantes.

        Si employer_insurance = Oui, alors assurance médicale de la carte = 0$
        (car elle ne lui sert à rien - déjà couvert)
        """
        value = 0.0
        insurance = card.insurance

        # A. Assurance médicale voyage - ANNULATION SI REDONDANTE
        if insurance.travel_medical and self._travels_frequently():
            # Si l'utilisateur a déjà une assurance via employeur, cette valeur = 0$
            if self.profile.employer_insurance == "Oui":
                # Valeur nulle car déjà couvert
                pass
            else:
                value += 100

        # B. Assurance annulation
        if insurance.travel_cancellation and self._travels_frequently():
            value += 50

        # C. Protection achats
        if insurance.purchase_protection:
            if self.profile.spending_electronics > 100:
                value += 30

        # D. Assurance appareils mobiles
        if insurance.mobile_device:
            if self.profile.device_insurance == "Non":
                value += 100

        # E. Location de voiture
        if insurance.car_rental and self.profile.car_rental in ["Oui, à chaque voyage", "Oui, parfois"]:
            value += 50

        return value

    def _calculate_fx_penalty(self, card: CreditCard) -> float:
        """
        Calcule la pénalité de frais de change (FX Fee).

        Soustrait TOUJOURS (spending_foreign * 12) * 0.025
        pour toutes les cartes Amex et RBC (et généralement toutes les cartes canadiennes)
        qui chargent 2.5% de frais de conversion.

        Exception: cartes sans frais FX (ex: carte USD, certaines cartes voyage)
        """
        spending_foreign = self.profile.spending_foreign

        if spending_foreign <= 0:
            return 0.0

        # Vérifier si la carte a des frais FX (par défaut, toutes les cartes standard ont 2.5%)
        # Certaines cartes premium n'ont pas de frais FX sur les achats voyage
        has_no_fx_fee = (
            "US Dollar" in card.name or
            "USD" in card.name or
            "no foreign transaction fee" in card.name.lower()
        )

        if has_no_fx_fee:
            return 0.0

        # Pénalité FX = dépenses étrangères annuelles * 2.5%
        annual_foreign_spend = spending_foreign * 12
        fx_penalty = annual_foreign_spend * 0.025

        return fx_penalty

    def _calculate_score(self, card: CreditCard, roi: float) -> float:
        """
        Calcule un score de 0-100 pour une carte avec courbe logistique.

        Arrête le calcul linéaire `40 * (roi / max_roi)` qui favorise excessivement
        les cartes avec bonus absurdes.

        Utilise une courbe logistique avec plafond:
        - ROI > 500$ = 40 pts max (plafond)
        - Courbe sigmoïde pour progression naturelle
        """
        score = 0.0

        # A. ROI avec courbe logistique (40% du score)
        # Plutôt que linéaire, utilise une fonction sigmoïde avec plafond à 500$
        roi_component = self._logistic_roi_score(roi, max_roi_cap=500)
        score += 40 * roi_component

        # B. Correspondance frais annuels (20%)
        max_fee = self._parse_max_fee()
        if card.annual_fee <= max_fee:
            score += 20
        elif card.annual_fee <= max_fee * 1.5:
            score += 10

        # C. Correspondance programme de récompenses (15%)
        if self._prefers_cashback() and card.base_rate >= 1.0:
            score += 15
        elif self._prefers_points() and card.reward_program:
            score += 15

        # D. Avantages voyage si pertinent (15%)
        if self._travels_frequently() and card.travel_perks.lounge_access:
            score += 15
        elif not self._travels_frequently():
            score += 10  # Pas de pénalité si ne voyage pas

        # E. Assurances (10%)
        if card.insurance.travel_medical or card.insurance.purchase_protection:
            score += 10

        return min(100, score)

    def _logistic_roi_score(self, roi: float, max_roi_cap: float = 500) -> float:
        """
        Fonction logistique pour scorer le ROI avec plafond.

        Utilise une courbe en S (sigmoïde) pour éviter qu'un ROI absurde
        (ex: 1000$ de bonus) écrase toutes les autres cartes.

        Formule: f(x) = x / (x + k) où k = point d'inflexion
        - ROI = 0$ → score = 0
        - ROI = 250$ → score ≈ 0.5
        - ROI = 500$ → score ≈ 0.83
        - ROI = 1000$ → score ≈ 0.91 (plafonné)
        """
        if roi <= 0:
            return 0.0

        # Point d'inflexion à 250$ (moitié du plafond)
        k = max_roi_cap / 2

        # Fonction sigmoïde: score = roi / (roi + k)
        # Normalisé pour que ROI=500$ donne ~0.83 (proche de 1)
        raw_score = roi / (roi + k)

        # Normaliser pour que le max soit 1.0
        max_raw = max_roi_cap / (max_roi_cap + k)
        normalized_score = raw_score / max_raw

        return min(1.0, normalized_score)

    def _calculate_match_percentage(self, card: CardNetwork) -> float:
        """
        Calcule le pourcentage de match avec le profil avec facteur éliminatoire.

        Ajoute un facteur éliminatoire discret:
        - Si l'utilisateur magasine SEULEMENT chez Costco et Maxi/Provigo/Loblaws,
          le Match % d'une carte Amex chute de 50%, même si le ROI a l'air bon.
        """
        match = 0.0
        factors = 0

        # A. Frais annuels
        factors += 1
        max_fee = self._parse_max_fee()
        if card.annual_fee <= max_fee:
            match += 1

        # B. Réseau
        factors += 1
        if self.profile.network_preference == "Aucune préférence":
            match += 1
        elif (self.profile.network_preference == "Visa" and card.network == CardNetwork.VISA) or \
             (self.profile.network_preference == "Mastercard" and card.network == CardNetwork.MASTERCARD) or \
             (self.profile.network_preference == "American Express" and card.network == CardNetwork.AMEX):
            match += 1

        # C. Programme de récompenses
        factors += 1
        if self._prefers_cashback() and card.tier in [CardTier.CASHBACK, CardTier.NO_FEE]:
            match += 1
        elif self._prefers_points() and card.tier in [CardTier.TRAVEL, CardTier.PREMIUM]:
            match += 1

        # D. Voyage
        if self._travels_frequently():
            factors += 1
            if card.travel_perks.lounge_access or card.insurance.travel_medical:
                match += 1

        # E. Institutions
        factors += 1
        if not self.profile.excluded_institutions or card.issuer not in self.profile.excluded_institutions:
            match += 1

        # Calcul de base du match percentage
        base_match_pct = (match / factors) * 100 if factors > 0 else 0

        # F. FACTEUR ÉLIMINATOIRE - Incompatibilité commerces
        penalty_multiplier = self._calculate_commerce_incompatibility_penalty(card)

        return round(base_match_pct * penalty_multiplier, 1)

    def _calculate_commerce_incompatibility_penalty(self, card: CreditCard) -> float:
        """
        Calcule un multiplicateur de pénalité pour incompatibilité commerces.

        - Si utilisateur magasine SEULEMENT chez Costco → pénalité Visa (Costco = Mastercard seulement)
        - Si utilisateur magasine SEULEMENT chez Maxi/Provigo/Loblaws → pénalité Amex (-50%)
        """
        penalty = 1.0

        grocery_stores_lower = [s.lower() for s in self.profile.grocery_stores]

        if not grocery_stores_lower:
            return penalty

        # A. Pénalité Amex si seulement Loblaws/Maxi/Provigo
        amex_incompatible = ["maxi", "provigo", "loblaws", "real canadian superstore"]
        all_amex_incompatible = all(
            any(incompatible in store for incompatible in amex_incompatible)
            for store in grocery_stores_lower
        )

        if card.network == CardNetwork.AMEX and all_amex_incompatible:
            penalty *= 0.5  # -50% de match

        # B. Pénalité Visa si seulement Costco (Costco accepte seulement Mastercard)
        if "costco" in grocery_stores_lower and len(grocery_stores_lower) == 1:
            if card.network == CardNetwork.VISA:
                penalty *= 0.5  # -50% de match

        return penalty

    def _get_reasons(self, card: CreditCard) -> List[str]:
        """Génère les raisons de recommandation"""

        reasons = []
        spending = self._get_spending_dict()

        # Cashback élevé sur catégories
        best_category = max(spending.items(), key=lambda x: x[1]) if spending else None
        if best_category:
            rate = card.get_reward_rate(best_category[0])
            if rate >= 2.0:
                reasons.append(f"{rate}% de récompenses sur {best_category[0]}")

        # Avantages spécifiques
        if card.travel_perks.lounge_access and self._travels_frequently():
            reasons.append("Accès aux salons d'aéroport inclus")

        if card.insurance.travel_medical and self._travels_frequently():
            reasons.append("Assurance médicale voyage incluse")

        if card.insurance.mobile_device and self.profile.device_insurance == "Non":
            reasons.append("Assurance appareils mobiles incluse")

        if card.first_year_free:
            reasons.append("Première année gratuite")

        if card.annual_fee == 0:
            reasons.append("Aucun frais annuel")

        if card.welcome_bonus > 0:
            reasons.append(f"Bonus de bienvenue: {card.welcome_bonus}$ estimé")

        # Partenaires
        grocery_stores_lower = [s.lower() for s in self.profile.grocery_stores]
        gas_stations_lower = [s.lower() for s in self.profile.gas_stations]
        telecom_lower = [t.lower() for t in self.profile.telecom_services]

        if "costco" in grocery_stores_lower and "Costco" in card.name:
            reasons.append("Compatible avec Costco")

        if any("esso" in g or "mobil" in g for g in gas_stations_lower) and "PC Optimum" in card.reward_program:
            reasons.append("Points PC Optimum chez Esso/Mobil")

        if "petro-canada" in gas_stations_lower and "Scène+" in card.reward_program:
            reasons.append("Points Scène+ chez Petro-Canada")

        if any("rogers" in t or "fido" in t for t in telecom_lower):
            if "Rogers" in card.name or "Fido" in card.name:
                reasons.append("Avantages exclusifs avec votre fournisseur téléphonique")

        if "amazon" in self.profile.amazon_usage.lower():
            if "Amazon" in card.name:
                reasons.append("Récompenses accrues sur Amazon")

        return reasons if reasons else ["Bon rapport récompenses/frais"]

    def _get_warnings(self, card: CreditCard) -> List[str]:
        """Génère les avertissements"""

        warnings = []

        # Costco
        if self.profile.uses_costco in ["Oui, régulièrement", "Oui, occasionnellement"]:
            if card.network == CardNetwork.VISA:
                warnings.append("⚠️ Costco accepte seulement Mastercard au Canada")
            elif card.network == CardNetwork.AMEX:
                warnings.append("⚠️ Costco n'accepte pas American Express")

        # Revenu
        if card.min_income_personal > 0:
            warnings.append(f"Revenu personnel minimum requis: {card.min_income_personal:,}000$")

        # Score de crédit
        if card.min_credit_score >= 720:
            warnings.append("Nécessite un excellent crédit (720+)")

        # Âge
        if "65 ans et plus" in self.profile.age_range and card.insurance.travel_medical:
            warnings.append("⚠️ La couverture médicale voyage peut être réduite après 65 ans")

        # Solde impayé
        if self.profile.pays_balance_full in ["Rarement", "Jamais"]:
            if card.annual_fee > 100:
                warnings.append("⚠️ Les intérêts dépasseront les bénéfices si vous ne payez pas votre solde en entier")

        return warnings

    def _get_already_has_benefits(self, card: CreditCard) -> List[str]:
        """Retourne les avantages déjà possédés"""

        already_has = []

        for current_card in self.profile.current_cards:
            # Vérifier les assurances
            if current_card.get("travel_medical") and card.insurance.travel_medical:
                already_has.append("Assurance médicale voyage")

            if current_card.get("lounge_access") and card.travel_perks.lounge_access:
                already_has.append("Accès salon d'aéroport")

        return already_has

    # ==================== MÉTHODES UTILITAIRES ====================

    def _get_spending_dict(self) -> Dict[str, float]:
        """Retourne un dict des dépenses mensuelles"""
        return {
            "groceries": self.profile.spending_groceries,
            "gas": self.profile.spending_gas,
            "restaurants": self.profile.spending_restaurants,
            "pharmacy": self.profile.spending_pharmacy,
            "transport": self.profile.spending_transport,
            "subscriptions": self.profile.spending_subscriptions,
            "entertainment": self.profile.spending_entertainment,
            "online": self.profile.spending_online,
        }

    def _parse_credit_score(self) -> int:
        """Parse le score de crédit en valeur numérique"""
        mapping = {
            "Excellent (760+)": 760,
            "Très bon (720–759)": 740,
            "Bon (680–719)": 700,
            "Acceptable (640–679)": 660,
            "Passable (600–639)": 620,
            "Faible (moins de 600)": 580,
        }
        return mapping.get(self.profile.credit_score, 650)

    def _parse_income(self, income_str: str) -> float:
        """Parse le revenu en valeur numérique (milliers)"""
        if "Préfère" in income_str or "Je ne sais pas" in income_str:
            return 0
        if "150 000" in income_str or "200 000" in income_str:
            return 150000
        if "100 000" in income_str:
            return 100000
        if "80 000" in income_str:
            return 80000
        if "60 000" in income_str:
            return 60000
        if "40 000" in income_str:
            return 40000
        if "20 000" in income_str:
            return 20000
        return 0

    def _parse_max_fee(self) -> float:
        """Parse les frais annuels maximum acceptés"""
        mapping = {
            "0 $ (sans frais seulement)": 0,
            "Jusqu'à 50 $": 50,
            "Jusqu'à 100 $": 100,
            "Jusqu'à 150 $": 150,
            "Jusqu'à 200 $": 200,
            "Jusqu'à 300 $": 300,
            "Jusqu'à 500 $": 500,
            "Plus de 500 $ si le ROI est démontré": 1000,
        }
        return mapping.get(self.profile.max_annual_fee, 150)

    def _prefers_cashback(self) -> bool:
        """Vérifie si l'utilisateur préfère le cashback"""
        return self.profile.points_comfort in [
            "Je préfère nettement le cashback — simple et direct",
            "Je connais les bases mais sans complexité"
        ]

    def _prefers_points(self) -> bool:
        """Vérifie si l'utilisateur préfère les points"""
        return self.profile.points_comfort in [
            "Je suis à l'aise et j'aime optimiser mes points"
        ]

    def _travels_frequently(self) -> bool:
        """Vérifie si l'utilisateur voyage fréquemment"""
        return self.profile.travel_frequency not in [
            "Jamais ou presque", ""
        ]

    def _flies_air_canada(self) -> bool:
        """Vérifie si l'utilisateur utilise Air Canada"""
        return "Air Canada" in self.profile.airlines

    def _estimate_num_flights(self) -> int:
        """Estime le nombre de vols par an"""
        mapping = {
            "1 fois par an": 2,
            "2–3 fois par an": 5,
            "4–5 fois par an": 10,
            "6 fois et plus par an": 15,
        }
        return mapping.get(self.profile.travel_frequency, 2)


def generate_recommendation_report(profile: UserProfile) -> str:
    """Génère un rapport de recommandation complet"""

    engine = RecommendationEngine(profile)
    recommendations = engine.recommend(num_results=3)

    report = []
    report.append("=" * 60)
    report.append("🎯 VOS RECOMMANDATIONS DE CARTES DE CRÉDIT")
    report.append("=" * 60)
    report.append("")

    for i, rec in enumerate(recommendations, 1):
        report.append(f"\n{'🥇' if i == 1 else '🥈' if i == 2 else '🥉'} RECOMMANDATION #{i}")
        report.append("-" * 40)
        report.append(f"Carte: {rec.card.name}")
        report.append(f"Émetteur: {rec.card.issuer}")
        report.append(f"Réseau: {rec.card.network.value}")
        report.append(f"Frais annuels: {rec.card.annual_fee}$" + (" (1ère année gratuite)" if rec.card.first_year_free else ""))
        report.append(f"Match: {rec.match_percentage}%")
        report.append(f"ROI annuel estimé: {rec.annual_roi}$")
        report.append("")

        if rec.reasons:
            report.append("✅ Pourquoi cette carte:")
            for reason in rec.reasons:
                report.append(f"   • {reason}")
            report.append("")

        if rec.warnings:
            report.append("⚠️ Avertissements:")
            for warning in rec.warnings:
                report.append(f"   • {warning}")
            report.append("")

        if rec.already_has_benefits:
            report.append("ℹ️  Avantages que vous avez déjà:")
            for benefit in rec.already_has_benefits:
                report.append(f"   • {benefit}")
            report.append("")

    report.append("\n" + "=" * 60)
    report.append("💡 CONSEIL: Comparez les ROI et choisissez selon vos priorités!")
    report.append("=" * 60)

    return "\n".join(report)


if __name__ == "__main__":
    # Test avec un profil exemple
    profile = UserProfile()
    profile.spending_groceries = 600
    profile.spending_gas = 200
    profile.spending_restaurants = 300
    profile.credit_score = "Excellent (760+)"
    profile.income_personal = "80 000–99 999 $"
    profile.travel_frequency = "2–3 fois par an"
    profile.max_annual_fee = "Jusqu'à 150 $"
    profile.points_comfort = "Je préfère nettement le cashback — simple et direct"

    report = generate_recommendation_report(profile)
    print(report)
