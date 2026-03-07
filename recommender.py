"""
Moteur de recommandation de cartes de crédit
Calcule le ROI et recommande les meilleures cartes selon le profil
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from card_database import CreditCard, CardNetwork, CardTier, get_all_cards
from questionnaire import UserProfile

# Mapping banque (réponse questionnaire) -> mots-clés dans card.issuer
BANK_ISSUER_MAP = {
    "RBC":                  ["RBC", "Royal Bank", "Banque Royale"],
    "TD":                   ["TD", "Toronto-Dominion"],
    "BMO":                  ["BMO", "Bank of Montreal"],
    "CIBC":                 ["CIBC", "Simplii"],   # Simplii = filiale CIBC
    "Banque Scotia":        ["Scotia", "Scotiabank"],
    "Banque Nationale":     ["Banque Nationale", "National Bank"],
    "Desjardins":           ["Desjardins"],
    "Tangerine":            ["Tangerine"],
    "Simplii Financial":    ["Simplii", "CIBC"],
    "EQ Bank":              ["EQ Bank", "Equitable"],
    "Motus Bank":           ["Motus"],
    "Banque Laurentienne":  ["Laurentienne", "Laurentian"],
    "ATB Financial":        ["ATB"],
    "Coast Capital":        ["Coast Capital"],
    "Manulife Bank":        ["Manulife"],
}


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


@dataclass
class DuoRecommendation:
    """Résultat d'une recommandation duo (deux cartes complémentaires)"""
    card_primary: CreditCard
    card_secondary: CreditCard
    combined_roi: float        # ROI annuel combiné des deux cartes
    best_single_roi: float     # ROI de la meilleure carte seule
    extra_gain: float          # Gain additionnel vs meilleure carte seule
    category_split: Dict[str, str]  # catégorie -> nom de la carte optimale


class RecommendationEngine:
    """Moteur de recommandation"""

    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.cards = get_all_cards()

    def recommend(self, num_results: int = 3) -> List[CardRecommendation]:
        """Genere les meilleures recommandations."""

        eligible_cards = self._filter_eligible_cards()

        scored_cards = []
        for card in eligible_cards:
            roi = self._calculate_roi(card)
            match_pct = self._calculate_match_percentage(card)
            # Score final : 60% match profil + 40% ROI financier (normalisé)
            roi_normalized = self._logistic_roi_score(roi, max_roi_cap=600) * 100
            score = match_pct * 0.60 + roi_normalized * 0.40
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

            # Filtrage par province (cartes à disponibilité restreinte)
            province = self.profile.province
            if province:
                # ATB Financial = Alberta seulement
                if "ATB" in card.issuer and province != "Alberta":
                    continue
                # Meridian Credit Union = Ontario seulement
                if "Meridian" in card.issuer and province not in ["Ontario", ""]:
                    continue
                # Certaines cartes Desjardins = Quebec/Ontario principalement
                # (on les garde mais on les note moins - géré dans red flags)

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

        spending = dict(self._get_spending_dict_no_alias())

        # Ajout des dépenses publicitaires (Google Ads / Meta Ads) aux dépenses business
        if self.profile.ad_spending == "Oui, plus de 1 000 $/mois":
            spending["business"] = spending.get("business", 0) + 1200
        elif self.profile.ad_spending == "Oui, moins de 1 000 $/mois":
            spending["business"] = spending.get("business", 0) + 400

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
            cap  = card.get_reward_cap(category)   # plafond mensuel ($)

            # Appliquer contrainte Amex/Loblaws pour l'épicerie
            if category == "groceries" and amex_loblaws_constraint:
                rate = min(rate, 1.0)

            # Appliquer le cap mensuel : montant au-dessus du cap => taux de base
            if cap and amount > cap:
                bonus_annual   = cap * 12 * (rate / 100)
                overflow_annual = (amount - cap) * 12 * (card.base_rate / 100)
                base_reward = bonus_annual + overflow_annual
            else:
                base_reward = amount * 12 * (rate / 100)

            # Appliquer CPP multiplier pour cartes de points
            if card.reward_program and ("MR" in card.reward_program or "Avion" in card.reward_program or
                                        "points" in card.reward_program.lower()):
                base_reward *= cpp_multiplier

            total_value += base_reward

        return total_value

    def _get_cpp_multiplier(self, card: CreditCard) -> float:
        """
        Retourne le multiplicateur CPP pour le calcul ROI (utilise _get_card_cpp_value).
        Maintenu pour compatibilite avec _calculate_rewards_value_dynamic.
        """
        return self._get_card_cpp_value(card)

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
        Amortit le bonus de bienvenue en tenant compte de :
        1. La strategie de garde (churning vs long terme)
        2. La capacite reelle a atteindre le minimum de depense
           (la plupart des cartes premium exigent $3000-$5000 en 3 mois)
        """
        if card.welcome_bonus <= 0:
            return 0.0

        # Estimer le minimum de depense requis selon la valeur du bonus et le tier
        welcome = card.welcome_bonus
        if welcome >= 500:
            estimated_min_spend = 4000   # Cartes premium : ~$4000 en 3 mois
        elif welcome >= 200:
            estimated_min_spend = 3000   # Cartes mid-range
        elif welcome >= 100:
            estimated_min_spend = 1500
        else:
            estimated_min_spend = 500    # Petits bonus, peu d'exigence

        # Depenses mensuelles reelles de l'utilisateur
        spending = self._get_spending_dict_no_alias()
        total_monthly = sum(v for v in spending.values() if v > 0)
        total_monthly += self.profile.spending_foreign
        spend_in_3_months = total_monthly * 3

        # Probabilite d'atteindre le minimum (0.0 a 1.0)
        if estimated_min_spend <= 0 or spend_in_3_months >= estimated_min_spend:
            eligibility = 1.0
        elif spend_in_3_months <= 0:
            eligibility = 0.10
        else:
            eligibility = min(1.0, spend_in_3_months / estimated_min_spend)

        # Amortissement selon strategie de garde
        if self.profile.card_strategy == "Moins d'un an (Churning)":
            amort = 1.0    # Churner : objectif = avoir le bonus 100%
        elif self.profile.card_strategy == "1-2 ans":
            amort = 0.75
        else:
            amort = 0.50   # Long terme : amorti sur 2-3 ans

        # Ajustement selon l'horizon de demande (timeline)
        timeline = self.profile.timeline
        if timeline == "Je planifie seulement pour l'instant":
            amort *= 0.85  # Planification future : les offres changent, bonus moins tangible
        elif timeline == "Immédiatement":
            amort = min(1.0, amort * 1.05)  # Demande immédiate : bonus pleinement réalisable

        return card.welcome_bonus * amort * eligibility

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

        # E. Location de voiture (valeur augmentée si pas de véhicule personnel)
        if insurance.car_rental and self.profile.car_rental in ["Oui, à chaque voyage", "Oui, parfois"]:
            car_rental_base = 80 if self.profile.has_vehicle == "Non" else 50
            value += car_rental_base

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

        # Cartes sans frais FX (champ explicite ou nom de carte USD)
        has_no_fx_fee = (
            card.no_fx_fee or
            "US Dollar" in card.name or
            "USD" in card.name
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

    def _calculate_match_percentage(self, card: CreditCard) -> float:
        """
        Calcule le pourcentage de match avec un systeme de scoring a 8 dimensions et poids dynamiques.

        Architecture:
        1. Derivation des poids selon le profil (recherche JD Power 2025 + preferences utilisateur)
        2. Scoring de 8 dimensions (0.0 a 1.0 chacune)
        3. Score pondere => pourcentage brut
        4. Multiplicateurs red flags (penalites critiques)
        5. Normalisation finale entre 5% et 99%

        Dimensions:
        - rewards_earning:       Adequation taux/depenses (toujours base prioritaire)
        - fee_value:             Rapport frais annuels / valeur recue
        - reward_type_fit:       Cashback vs points selon preference declaree
        - insurance_coverage:    Couverture assurances selon besoins reels
        - travel_perks:          Avantages voyage selon frequence et priorites
        - network_store_fit:     Compatibilite reseau avec commerces habituels
        - points_program_quality: Valeur CPP et flexibilite du programme
        - eligibility:           Probabilite d'approbation (revenu, credit)
        """
        # 1. Poids dynamiques selon profil
        weights = self._derive_priority_weights()

        # 2. Scorer chaque dimension
        scores = {
            'rewards_earning':       self._score_rewards_earning(card),
            'fee_value':             self._score_fee_value(card),
            'reward_type_fit':       self._score_reward_type(card),
            'insurance_coverage':    self._score_insurance_coverage(card),
            'travel_perks':          self._score_travel_perks(card),
            'network_store_fit':     self._score_network_store_fit(card),
            'points_program_quality': self._score_points_quality(card),
            'eligibility':           self._score_eligibility(card),
            'interest_rate_fit':     self._score_interest_rate(card),
        }

        # 3. Score pondere
        total_weighted = sum(scores[dim] * weights[dim] for dim in scores)
        max_possible = sum(weights.values())
        base_pct = (total_weighted / max_possible) * 100 if max_possible > 0 else 0

        # 4. Multiplicateurs red flags
        red_flag_multiplier = self._calculate_red_flags(card)

        # 5. Normalisation : 5% minimum, 99% maximum (pas de 100% parfait)
        final_pct = max(5.0, min(99.0, base_pct * red_flag_multiplier))

        return round(final_pct, 1)

    def _derive_priority_weights(self) -> dict:
        """
        Calcule les poids dynamiques selon le profil utilisateur.

        Poids de base inspires par la recherche canadienne:
        - 46% des Canadiens priorisent cashback/credits (JD Power + NerdWallet 2025)
        - 29% priorisent les recompenses epicerie/quotidien
        - 22% priorisent les avantages voyage
        Les frais annuels sont un facteur tres important (coupure directe)
        """
        weights = {
            'rewards_earning':        5.0,   # Toujours tres important (ROI direct sur depenses)
            'fee_value':              4.0,   # Tres important (frais = cout direct annuel)
            'reward_type_fit':        3.5,   # Important (alignement cashback vs points)
            'eligibility':            3.0,   # Important (carte inaccessible = score 0)
            'insurance_coverage':     2.5,   # Modere par defaut, booste si priorite
            'points_program_quality': 2.0,   # Modere (matiere si points)
            'travel_perks':           1.5,   # Faible par defaut (seulement si voyageur)
            'network_store_fit':      1.5,   # Faible (compatibilite commerces)
        }

        priorities = self.profile.priorities if self.profile.priorities else []

        # === BOOST selon priorites explicitement declarees ===
        if "Maximiser les recompenses sur les achats du quotidien" in priorities or \
           "Maximiser les récompenses sur les achats du quotidien" in priorities:
            weights['rewards_earning'] += 3.0       # 5.0 => 8.0
            weights['points_program_quality'] += 1.0

        if "Avantages voyage (assurances, salons, miles)" in priorities:
            weights['travel_perks'] += 3.0          # 1.5 => 4.5
            weights['insurance_coverage'] += 1.0

        if "Cashback simple sans gerer des points" in priorities or \
           "Cashback simple sans gérer des points" in priorities:
            weights['reward_type_fit'] += 2.5       # 3.5 => 6.0
            weights['points_program_quality'] *= 0.3 # Peu importe si cashback voulu

        if "Frais annuels les plus bas possible" in priorities:
            weights['fee_value'] += 3.0             # 4.0 => 7.0

        if "Assurances (achats, appareils, voyage)" in priorities:
            weights['insurance_coverage'] += 3.5    # 2.5 => 6.0

        if "Accumulation rapide pour un voyage specifique" in priorities or \
           "Accumulation rapide pour un voyage spécifique" in priorities:
            weights['travel_perks'] += 2.0
            weights['points_program_quality'] += 2.0
            weights['rewards_earning'] += 1.0

        if "Avantages dans des commerces specifiques" in priorities or \
           "Avantages dans des commerces spécifiques" in priorities:
            weights['network_store_fit'] += 2.0

        # === BOOST selon champs de nuances de priorites ===
        everyday_imp = self.profile.everyday_rewards_importance
        if everyday_imp == "Tres importantes — c'est ma priorite #1" or \
           everyday_imp == "Très importantes — c'est ma priorité #1":
            weights['rewards_earning'] += 2.0
        elif everyday_imp == "Importantes — j'y tiens beaucoup":
            weights['rewards_earning'] += 1.0
        elif everyday_imp in ["Peu importantes — j'ai d'autres priorites",
                               "Peu importantes — j'ai d'autres priorités"]:
            weights['rewards_earning'] = max(2.0, weights['rewards_earning'] - 1.5)

        ins_imp = self.profile.insurance_importance
        if ins_imp in ["Tres importante — c'est une priorite essentielle pour moi",
                       "Très importante — c'est une priorité essentielle pour moi"]:
            weights['insurance_coverage'] += 3.0
        elif ins_imp == "Importante — j'y tiens si c'est inclus":
            weights['insurance_coverage'] += 1.5
        elif ins_imp in ["Peu importante — je suis deja bien couvert(e) ou m'en fous",
                         "Peu importante — je suis déjà bien couvert(e) ou m'en fous"]:
            weights['insurance_coverage'] = max(0.5, weights['insurance_coverage'] - 1.5)

        travel_imp = self.profile.travel_perks_importance
        if travel_imp in ["Tres importants — je voyage souvent et j'en profite pleinement",
                          "Très importants — je voyage souvent et j'en profite pleinement"]:
            weights['travel_perks'] += 2.0
        elif travel_imp in ["Peu importants — je prefere maximiser les recompenses directes",
                            "Peu importants — je préfère maximiser les récompenses directes"]:
            weights['travel_perks'] = max(0.3, weights['travel_perks'] - 1.0)

        # === AJUSTEMENTS selon preferences cashback/points ===
        if self._prefers_cashback():
            weights['reward_type_fit'] += 1.5
            weights['points_program_quality'] = max(0.3, weights['points_program_quality'] * 0.4)
        elif self._prefers_points():
            weights['reward_type_fit'] += 1.0
            weights['points_program_quality'] += 1.5

        # === AJUSTEMENTS selon frequence de voyage ===
        if not self._travels_frequently():
            # Si ne voyage pas, avantages voyage = tres peu important
            weights['travel_perks'] = min(weights['travel_perks'], 0.5)
        elif self.profile.travel_frequency in ["4-5 fois par an", "4–5 fois par an",
                                                "6 fois et plus par an"]:
            weights['travel_perks'] += 2.0
            weights['insurance_coverage'] += 1.0

        # === AJUSTEMENTS selon Costco ===
        if self.profile.uses_costco == "Oui, regulierement" or \
           self.profile.uses_costco == "Oui, régulièrement":
            weights['network_store_fit'] += 3.0   # Compatibilite reseau = critique
        elif self.profile.uses_costco in ["Oui, occasionnellement"]:
            weights['network_store_fit'] += 1.5

        # === AJUSTEMENTS selon epicieries incompatibles Amex ===
        grocery_stores_lower = [s.lower() for s in self.profile.grocery_stores]
        amex_incompatible = ["maxi", "provigo", "loblaws", "real canadian superstore"]
        if any(any(inc in s for inc in amex_incompatible) for s in grocery_stores_lower):
            weights['network_store_fit'] += 1.0

        # === AJUSTEMENTS selon strategie de garde (churning) ===
        if self.profile.card_strategy == "Moins d'un an (Churning)":
            # Churner : le bonus de bienvenue est TOUT. Les rewards recurrents importent moins.
            weights['rewards_earning'] = max(2.0, weights['rewards_earning'] * 0.60)
            weights['fee_value'] += 1.0          # Frais annuels encore plus importants
            # Le bonus est deja pris en compte dans le ROI, pas dans le match%
            # Mais on booste l'eligibilite car le churner veut maximiser les approbations
            weights['eligibility'] += 1.5

        # === AJUSTEMENTS selon depenses etrangeres ===
        if self.profile.spending_foreign > 200 or \
           self.profile.foreign_purchases in ["Tres souvent", "Très souvent",
                                               "Souvent (plusieurs fois/mois)"]:
            weights['network_store_fit'] += 1.5   # Compatibilite FX devient importante

        # === AJUSTEMENTS si travailleur autonome avec grosses depenses business ===
        if self.profile.business_registered in ["Oui, incorporated",
                                                  "Oui, enregistrée non incorporée"]:
            if self.profile.spending_business > 500:
                weights['rewards_earning'] += 1.0   # Deductions + rewards = double avantage

        # Simplicity preference adjustment
        simplicity = self.profile.simplicity_preference
        if simplicity in ["Je veux la simplicite absolue — une carte, pas de gestion",
                          "Je veux la simplicité absolue — une carte, pas de gestion"]:
            weights['reward_type_fit'] += 1.0
            weights['points_program_quality'] *= 0.5
        elif simplicity in ["Je suis un(e) expert(e) en points — j'optimise au maximum"]:
            weights['points_program_quality'] += 1.5
            weights['reward_type_fit'] += 0.5

        # === AJUSTEMENTS selon budget voyage déclaré ===
        travel_budget = self.profile.travel_budget
        if travel_budget in ["10 000–19 999 $", "20 000 $ et plus"]:
            weights['travel_perks'] += 2.0
            weights['insurance_coverage'] += 1.0
        elif travel_budget == "5 000–9 999 $":
            weights['travel_perks'] += 1.0

        # === AJUSTEMENTS selon préférence de récompenses voyage ===
        reward_pref = self.profile.reward_preference
        if reward_pref:
            if "transférables" in reward_pref or "transferables" in reward_pref:
                weights['points_program_quality'] += 2.0
                weights['travel_perks'] += 0.5
            elif "remise directe" in reward_pref or "cashback voyage" in reward_pref.lower():
                weights['reward_type_fit'] += 1.0
            elif "pas intéressé" in reward_pref or "pas interesse" in reward_pref:
                weights['travel_perks'] = max(0.2, weights['travel_perks'] - 1.0)
                weights['points_program_quality'] = max(0.5, weights['points_program_quality'] - 0.5)

        # === AJUSTEMENTS selon fréquence de livraison de repas ===
        food_del = self.profile.food_delivery
        if food_del in ["1–2 fois par semaine", "Presque tous les jours"]:
            weights['rewards_earning'] += 1.0  # Dépenses resto élevées = earning compte

        # === AJUSTEMENTS selon statut de propriétaire ===
        if self.profile.home_owner == "Propriétaire":
            weights['insurance_coverage'] += 0.5  # Protège des biens de plus grande valeur

        # === AJUSTEMENTS si pas de véhicule ===
        if self.profile.has_vehicle == "Non":
            weights['insurance_coverage'] += 0.5  # Assurance location voiture = précieuse

        # === AJUSTEMENTS pour premier cardholder ===
        if not self.profile.has_cards:
            weights['eligibility'] += 1.0    # Critique d'obtenir une carte accessible
            weights['fee_value'] += 0.5      # Cartes sans frais préférables en début

        # === AJUSTEMENTS selon type d'établissement scolaire ===
        school = self.profile.school_type
        if school in ["Oui, université", "Oui, CEGEP", "Oui, collège ou école technique"]:
            weights['fee_value'] += 1.0      # Étudiants préfèrent les cartes sans frais
            weights['eligibility'] += 0.5

        # === AJUSTEMENTS selon dépenses publicitaires (travailleur autonome) ===
        if self.profile.ad_spending == "Oui, plus de 1 000 $/mois":
            weights['rewards_earning'] += 1.5   # Très hautes dépenses business = maximiser gains

        # === POIDS du taux d'intérêt selon comportement de paiement ===
        payment = self.profile.pays_balance_full
        if payment in ["Toujours", "Presque toujours", ""]:
            weights['interest_rate_fit'] = 0.0   # Taux irrelevant pour les payeurs intégraux
        elif payment == "Parfois":
            weights['interest_rate_fit'] = 3.0   # Modéré — porte parfois un solde
        elif payment in ["Rarement", "Jamais"]:
            weights['interest_rate_fit'] = 8.0   # Critique — les intérêts peuvent effacer tous les gains
        else:
            weights['interest_rate_fit'] = 0.0

        return weights

    def _score_rewards_earning(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : adequation des taux de recompenses aux depenses reelles.

        Applique les caps de depenses (cap_monthly) pour calculer le taux effectif
        reel plutot que le taux affiche. Inclut toutes les categories de depenses.

        Benchmarks effectifs (CPP-adjusted) :
          - 0.5% => 0.17  (carte de base)
          - 1.0% => 0.33  (correct)
          - 1.5% => 0.50  (moyen canadien)
          - 2.5% => 0.83  (excellent)
          - 3.0%+ => 1.0  (top performer)
        """
        spending = self._get_spending_dict_no_alias()
        # Ajouter les depenses en devises etrangeres comme categorie "online/travel"
        if self.profile.spending_foreign > 0:
            spending["foreign"] = self.profile.spending_foreign

        total_spending = sum(v for v in spending.values() if v > 0)

        if total_spending == 0:
            base = card.base_rate * self._get_card_cpp_value(card)
            return min(1.0, base / 3.0)

        cpp = self._get_card_cpp_value(card)
        amex_loblaws = self._check_amex_loblaws_constraint(card)

        weighted_rate = 0.0
        for cat, amount in spending.items():
            if amount <= 0:
                continue

            rate = card.get_reward_rate(cat)
            cap  = card.get_reward_cap(cat)

            # Penalite Amex/Loblaws sur epicerie
            if cat == "groceries" and amex_loblaws:
                rate = min(rate, 1.0)

            # Taux effectif reel apres cap mensuel
            if cap and amount > cap:
                # Partie capee au taux bonus, surplus au taux de base
                effective_rate = (cap * rate + (amount - cap) * card.base_rate) / amount
            else:
                effective_rate = rate

            # Penalite FX : carte avec frais de change sur depenses etrangeres
            if cat == "foreign":
                has_no_fx = ("US Dollar" in card.name or "USD" in card.name)
                if not has_no_fx:
                    effective_rate = max(0, effective_rate - 2.5)  # FX 2.5% efface les gains

            weighted_rate += effective_rate * cpp * (amount / total_spending)

        # Score normalise : 3% effectif = score parfait
        return min(1.0, weighted_rate / 3.0)

    def _get_card_cpp_value(self, card: CreditCard) -> float:
        """
        Retourne la valeur CPP (Cents Per Point) du programme de la carte.

        Basé sur les valuations Milesopedia + Prince of Travel (2025):
        - Amex MR Points:       2.0 cpp (transfert vers Aéroplan/Avios)
        - Aéroplan:             1.6 cpp (valeur moyenne réelle)
        - RBC Avion Elite:      1.5 cpp (transfert partenaires)
        - RBC Avion Premium:    1.0 cpp (rachat voyage standard)
        - Scene+ Travel:        1.0 cpp (rachat voyage 1:1)
        - WestJet Dollars:      1.0 cpp (dollar pour dollar)
        - PC Optimum:           1.0 cpp (epicerie = valeur fixe)
        - TD Points:            0.8 cpp (rachat voyage standard)
        - BMO/CIBC Rewards:     0.8 cpp (variable selon rachat)
        - Cashback (direct):    1.0 cpp (par definition)
        """
        if not card.reward_program:
            return 1.0  # Cashback implicite ou base

        prog = card.reward_program.lower()

        # Ordre de priorite : du plus specifique au plus general
        if "mr points" in prog or "membership rewards" in prog:
            # Amex MR : valeur plus haute si l'utilisateur optimise les points
            if self.profile.points_comfort in [
                "Je suis a l'aise et j'aime optimiser mes points",
                "Je suis à l'aise et j'aime optimiser mes points"
            ]:
                return 2.0
            elif self.profile.points_valuation == \
                    "Transfert vers partenaires aeriens comme Aeroplan/Avios (valeur = 1.5-2 cpp)" or \
                 self.profile.points_valuation == \
                    "Transfert vers partenaires aériens comme Aéroplan/Avios (valeur = 1.5-2 cpp)":
                return 1.75
            else:
                return 1.2  # Valeur conservative si cashback ou rachat direct

        if "aeroplan" in prog or "aéroplan" in prog:
            if self.profile.points_comfort in [
                "Je suis a l'aise et j'aime optimiser mes points",
                "Je suis à l'aise et j'aime optimiser mes points"
            ]:
                return 1.6
            return 1.2

        if "avion" in prog:
            if self.profile.points_comfort in [
                "Je suis a l'aise et j'aime optimiser mes points",
                "Je suis à l'aise et j'aime optimiser mes points"
            ]:
                return 1.5
            return 1.0

        if "scene+" in prog or "scene plus" in prog:
            return 1.0  # 1cpp pour voyages, 0.5cpp epicerie (moyenne: 1.0)

        if "westjet" in prog:
            return 1.0  # WestJet dollars = valeur fixe 1:1

        if "pc optimum" in prog:
            return 1.0  # ~1cpp en epicerie

        if "td rewards" in prog or "td points" in prog:
            return 0.8  # Valeur conservative (0.5-1.5 selon rachat)

        if "bmo rewards" in prog or "bmo" in prog:
            return 0.8

        if "cibc rewards" in prog:
            return 0.8

        if "viporter" in prog or "vi porter" in prog:
            return 1.0  # VIPorter Points ~1¢/pt pour vols Porter

        if "asia miles" in prog or "cathay" in prog:
            if self.profile.points_comfort in [
                "Je suis à l'aise et j'aime optimiser mes points",
                "Je suis a l'aise et j'aime optimiser mes points"
            ]:
                return 1.5  # ~1.5¢/pt en Business class Cathay Pacific
            return 1.2  # ~1.2¢/pt en economy

        if "atb my rewards" in prog or "atb rewards" in prog:
            return 1.0  # ~1¢/pt en rachat voyage ou crédit de relevé

        if "tims rewards" in prog or "tim hortons" in prog:
            return 1.0  # Converti en cashback équivalent (1250pts = 5$)

        if "bonusdollars" in prog or "bonus dollars" in prog:
            return 1.0  # BONUSDOLLARS Desjardins = 1¢ par point

        if "cashback" in prog or "cash back" in prog:
            return 1.0

        return 1.0  # Default

    def _score_fee_value(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : rapport entre les frais annuels et le budget accepte.

        - Frais = 0 => 1.0 (toujours parfait)
        - Frais <= max_fee => degradation douce (0.65-1.0)
        - Frais entre max_fee et 1.3x => 0.30 (trop cher)
        - Frais > 1.3x max_fee => 0.0 (hors budget)
        Note: premiere annee gratuite bonifie le score
        """
        max_fee = self._parse_max_fee()
        fee = card.annual_fee

        if fee == 0:
            return 1.0

        # Premiere annee gratuite : baisser le fee effectif de 50% (amortissement)
        if card.first_year_free:
            # Sur une strategie de 2 ans, ca reduit le cout de 50%
            # Pour l'utilisateur qui veut churner, c'est encore mieux
            if self.profile.card_strategy == "Moins d'un an (Churning)":
                fee = 0  # Annee gratuite => frais effectifs = 0
                return 1.0
            else:
                fee = fee * 0.5  # Amortissement partiel

        if fee <= max_fee:
            if max_fee == 0:
                return 1.0
            ratio = fee / max_fee
            # Score de 1.0 (gratuit) a 0.65 (utilise tout le budget)
            return max(0.65, 1.0 - ratio * 0.35)
        elif fee <= max_fee * 1.3:
            # Legerement au-dessus du budget
            return 0.30
        else:
            # Trop cher : score tres bas mais pas 0 (on peut quand meme afficher)
            return max(0.0, 0.10 - (fee - max_fee * 1.3) / 500)

    def _score_reward_type(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : adequation cashback vs points selon la preference.

        Logique:
        - Preference cashback + carte cashback => 1.0
        - Preference cashback + carte points => 0.15 (forte incompatibilite)
        - Preference points + carte points => 1.0
        - Preference points + carte cashback => 0.45 (incompatibilite moderee)
        - Neutre/indifferent => 0.70 (la plupart des cartes conviennent)
        """
        prefers_cashback = self._prefers_cashback()
        prefers_points = self._prefers_points()

        is_cashback = card.tier in [CardTier.CASHBACK, CardTier.NO_FEE] and \
                      ("cashback" in (card.reward_program or "").lower() or
                       "cash back" in (card.reward_program or "").lower() or
                       card.base_rate > 0 and not card.reward_program)
        is_points = card.tier in [CardTier.TRAVEL, CardTier.PREMIUM, CardTier.REWARDS] or \
                    bool(card.reward_program) and \
                    not ("cashback" in (card.reward_program or "").lower())

        # Cas particulier : carte avec recompenses en cashback ET programme de points
        # (ex: Scotia Scene+ qui peut etre rachetee en cashback)
        is_flexible = card.reward_program and (
            "scene+" in card.reward_program.lower() or
            "westjet" in card.reward_program.lower() or
            "cashback" in card.reward_program.lower()
        )

        if prefers_cashback:
            if is_cashback or is_flexible:
                return 1.0
            elif is_points:
                return 0.15   # Forte inadéquation : l'utilisateur veut la simplicité
            else:
                return 0.6

        elif prefers_points:
            if is_points and not is_cashback:
                return 1.0
            elif is_flexible:
                return 0.75   # Flexible = acceptable pour un optimiseur de points
            elif is_cashback:
                return 0.45   # Moins ideal mais pas eliminatoire
            else:
                return 0.7

        else:
            # Neutre ou indifferent => favoriser les cartes flexibles
            if is_flexible:
                return 0.85
            else:
                return 0.70

    def _score_insurance_coverage(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : adequation des assurances aux besoins reels.

        Chaque type d'assurance a un poids selon son importance typique.
        On retire la valeur des assurances redondantes (employer_insurance).
        """
        score = 0.0
        max_score = 0.0

        travels = self._travels_frequently()

        # --- Assurance medicale voyage (tres precieuse si voyageur sans couverture) ---
        is_senior = self.profile.age_range in ["65 ans et plus"]
        long_stays = self.profile.long_stays in [
            "Oui, regulierement", "Oui, régulièrement", "Oui, parfois"
        ]

        # Durée de voyage typique → jours de couverture nécessaires
        duration_to_days = {
            "Moins de 7 jours":  7,
            "7 à 14 jours":     14,
            "15 à 21 jours":    21,
            "22 à 30 jours":    30,
            "Plus de 30 jours": 40,
        }
        needed_days = duration_to_days.get(self.profile.typical_trip_duration, 14)

        if travels:
            max_score += 0.40
            if card.insurance.travel_medical:
                # Jours de couverture réels (0 = non connu, on suppose 15 jours)
                card_days = card.insurance.travel_medical_days if card.insurance.travel_medical_days > 0 else 15
                days_ratio = min(1.0, card_days / needed_days)

                if self.profile.employer_insurance == "Oui":
                    score += 0.08   # Redondant, valeur faible
                elif is_senior:
                    # 65+ : couverture médicale souvent limitée / avec exclusions
                    if long_stays:
                        score += 0.15 * days_ratio   # Couverture partielle, gaps importants
                    else:
                        score += 0.28 * days_ratio   # Utile mais moins fiable qu'à 40 ans
                else:
                    # Score proportionnel à l'adéquation de la durée
                    # Ex: besoin 21 jours, carte couvre 15 → 15/21 = 0.71 → 0.71 × 0.40 = 0.28
                    score += 0.40 * days_ratio

        # --- Assurance annulation/interruption voyage ---
        if travels:
            max_score += 0.15
            if card.insurance.travel_cancellation or card.insurance.travel_interruption:
                score += 0.15

        # --- Protection des achats (toujours utile) ---
        max_score += 0.20
        if card.insurance.purchase_protection:
            score += 0.20

        # --- Garantie prolongee (toujours utile) ---
        max_score += 0.12
        if card.insurance.extended_warranty:
            score += 0.12

        # --- Assurance appareils mobiles ---
        max_score += 0.13
        if card.insurance.mobile_device:
            if self.profile.device_insurance == "Non":
                score += 0.13
            else:
                score += 0.03   # Redondant si deja couvert

        # --- Location de voiture ---
        rents_cars = getattr(self.profile, 'car_rental', '') in \
                     ["Oui, a chaque voyage", "Oui, à chaque voyage",
                      "Oui, parfois", "Oui, quelquefois"]
        if rents_cars or travels:
            max_score += 0.08
            if card.insurance.car_rental:
                score += 0.08

        # --- Assurance bagages ---
        if travels:
            max_score += 0.05
            if card.insurance.baggage:
                score += 0.05

        if max_score == 0:
            return 0.50   # Neutre si aucun critere pertinent

        result = min(1.0, score / max_score)

        # Bonus propriétaire : protection des achats / garantie prolongée plus précieuse
        if self.profile.home_owner == "Propriétaire":
            if card.insurance.extended_warranty or card.insurance.purchase_protection:
                result = min(1.0, result * 1.08)

        # Bonus sans véhicule : assurance location voiture = nécessité réelle
        if self.profile.has_vehicle == "Non" and travels:
            if card.insurance.car_rental:
                result = min(1.0, result * 1.06)

        return result

    def _score_travel_perks(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : adequation des avantages voyage a la situation reelle.

        Si l'utilisateur ne voyage pas => score neutre (0.50) car
        cette dimension sera presque eliminee par les poids dynamiques.
        """
        if not self._travels_frequently():
            return 0.50   # Neutre, dimension quasi-inactive via les poids

        trips = self._estimate_trips_from_frequency()
        score = 0.0
        max_score = 0.0

        # Pré-calcul : budget voyage et préférence de programme
        travel_budget = self.profile.travel_budget
        budget_bonus = 0.0
        if travel_budget == "20 000 $ et plus":
            budget_bonus = 0.12
        elif travel_budget == "10 000–19 999 $":
            budget_bonus = 0.08
        elif travel_budget == "5 000–9 999 $":
            budget_bonus = 0.04

        reward_pref = self.profile.reward_preference

        # --- Acces aux salons ---
        max_score += 0.35
        if card.travel_perks.lounge_access:
            lounge_interest = self.profile.lounge_interest
            if lounge_interest == "Oui, c'est tres important pour moi" or \
               lounge_interest == "Oui, c'est très important pour moi":
                score += 0.35
            elif lounge_interest in ["Oui, si c'est inclus dans les avantages"]:
                score += 0.25
            else:
                score += 0.10   # Pas intéresse mais inclus quand meme

        # --- Credit voyage annuel ---
        max_score += 0.25
        if card.travel_perks.travel_credit_annual > 0:
            # Score base sur le ratio credit/frais (idealement > 50% des frais)
            fee = max(card.annual_fee, 1)
            credit_ratio = min(1.0, card.travel_perks.travel_credit_annual / fee)
            score += 0.25 * credit_ratio

        # --- Premier bagage gratuit (seulement si vole Air Canada) ---
        if self._flies_air_canada():
            max_score += 0.15
            if card.travel_perks.first_bag_free:
                # Valeur proportionnelle au nombre de vols
                flight_value = min(1.0, trips / 4.0)
                score += 0.15 * flight_value

        # --- Credit NEXUS/Global Entry ---
        nexus_interest = self.profile.nexus_interest if hasattr(self.profile, 'nexus_interest') else ""
        if nexus_interest in ["Oui", "Je suis interesse(e)", "Je suis intéressé(e)"]:
            max_score += 0.10
            if card.travel_perks.nexus_credit or card.travel_perks.global_entry_credit:
                score += 0.10

        # --- Match programme aerien prefere ---
        max_score += 0.15
        airlines = self.profile.airlines if self.profile.airlines else []
        prog = (card.reward_program or "").lower()
        card_name_lower = card.name.lower()

        ac_spending = self.profile.air_canada_spending  # "Beaucoup", "Souvent", etc.
        wj_spending = self.profile.westjet_spending

        if "Air Canada" in airlines or ac_spending in ["Beaucoup", "Souvent", "Oui"]:
            if "aeroplan" in prog or "aéroplan" in prog:
                score += 0.15
            elif card.travel_perks.lounge_access:
                score += 0.06
        elif "WestJet" in airlines or wj_spending in ["Beaucoup", "Souvent", "Oui"]:
            if "westjet" in prog or "westjet" in card_name_lower:
                score += 0.15
            elif card.travel_perks.lounge_access:
                score += 0.06
        elif card.travel_perks.lounge_access or card.travel_perks.travel_credit_annual > 0:
            score += 0.08   # Avantages generiques voyage

        # --- Preference type hotel (statut hotel via carte) ---
        max_score += 0.10
        hotel_type = self.profile.hotel_type
        if hotel_type in ["Hôtel de luxe / 5 étoiles", "Hotel de luxe / 5 etoiles",
                           "Chaîne hôtelière avec programme fidélité"]:
            # Cartes avec statut hotel (Amex Plat = Marriott Gold + Hilton Gold)
            if card.travel_perks.hotel_status:
                score += 0.10
            elif card.travel_perks.travel_credit_annual >= 100:
                score += 0.05
        else:
            score += 0.05   # Neutre pour les autres types

        # --- Location de voiture ---
        max_score += 0.10
        car_rental_use = self.profile.car_rental
        rents_regularly = car_rental_use in [
            "Oui, a chaque voyage", "Oui, à chaque voyage",
            "Oui, souvent", "Oui, parfois"
        ]
        if rents_regularly:
            if card.insurance.car_rental:
                score += 0.10   # Couverture CDW = valeur directe
        else:
            score += 0.05       # Neutre si loue rarement

        if max_score == 0:
            return 0.50

        result = min(1.0, score / max_score)

        # Bonus budget voyage : gros budget justifie les avantages premium
        result = min(1.0, result + budget_bonus * result)

        # Bonus préférence programme de récompenses voyage
        if reward_pref:
            prog = (card.reward_program or "").lower()
            if "transférables" in reward_pref or "transferables" in reward_pref:
                transferable = ["mr points", "aeroplan", "aéroplan", "avion"]
                if any(t in prog for t in transferable):
                    result = min(1.0, result + 0.08)
            elif "remise directe" in reward_pref or "cashback voyage" in reward_pref.lower():
                if "scene+" in prog or "westjet" in prog:
                    result = min(1.0, result + 0.06)
            elif "pas intéressé" in reward_pref or "pas interesse" in reward_pref:
                result *= 0.80  # Ne veut pas de récompenses voyage : avantages voyage moins utiles

        return result

    def _score_network_store_fit(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : compatibilite du reseau avec les commerces habituels.

        Commence a 1.0 et retire des points selon les incompatibilites.
        """
        score = 1.0

        grocery_stores_lower = [s.lower() for s in self.profile.grocery_stores]
        gas_stations_lower = [s.lower() for s in self.profile.gas_stations]

        # --- Incompatibilite Costco ---
        uses_costco = self.profile.uses_costco
        if uses_costco in ["Oui, regulierement", "Oui, régulièrement"]:
            if card.network in [CardNetwork.VISA, CardNetwork.AMEX]:
                score -= 0.80   # Critique : Costco = Mastercard seulement au Canada
        elif uses_costco == "Oui, occasionnellement":
            if card.network in [CardNetwork.VISA, CardNetwork.AMEX]:
                score -= 0.45
        elif uses_costco == "Rarement":
            if card.network in [CardNetwork.VISA, CardNetwork.AMEX]:
                score -= 0.15

        # --- Incompatibilite Amex/Maxi/Provigo/Loblaws ---
        if card.network == CardNetwork.AMEX and grocery_stores_lower:
            amex_incompatible = ["maxi", "provigo", "loblaws", "real canadian superstore"]
            incompatible_count = sum(
                1 for s in grocery_stores_lower
                if any(inc in s for inc in amex_incompatible)
            )
            if incompatible_count > 0:
                ratio = incompatible_count / len(grocery_stores_lower)
                score -= ratio * 0.45   # Penalite proportionnelle

        # --- Preference reseau explicite ---
        if self.profile.network_preference and \
           self.profile.network_preference != "Aucune preference" and \
           self.profile.network_preference != "Aucune préférence":
            pref_map = {
                "Visa": CardNetwork.VISA,
                "Mastercard": CardNetwork.MASTERCARD,
                "American Express": CardNetwork.AMEX
            }
            preferred = pref_map.get(self.profile.network_preference)
            if preferred and card.network != preferred:
                score -= 0.35

        # --- Synergie partenaire station essence ---
        gas_stations_lower = [s.lower() for s in self.profile.gas_stations]
        issuer_lower = card.issuer.lower()
        prog_lower = (card.reward_program or "").lower()

        # RBC + Petro-Canada => 3 sous/litre (synergie connue)
        if "petro-canada" in gas_stations_lower or "petro canada" in gas_stations_lower:
            if "rbc" in issuer_lower:
                score = min(1.0, score + 0.10)

        # PC Mastercard + Esso/Mobil => points PC Optimum supplementaires
        if any(s in gas_stations_lower for s in ["esso", "mobil"]):
            if "pc optimum" in prog_lower:
                score = min(1.0, score + 0.08)

        # Scotiabank Scene+ + Petro-Canada => points Sc¸ene+ chez Petro
        if "petro-canada" in gas_stations_lower or "petro canada" in gas_stations_lower:
            if "scene+" in prog_lower:
                score = min(1.0, score + 0.06)

        # --- Synergie telecom ---
        telecom_lower = [t.lower() for t in self.profile.telecom_services]
        if any(t in telecom_lower for t in ["rogers", "fido"]):
            if "rogers" in card.name.lower() or "fido" in card.name.lower():
                score = min(1.0, score + 0.12)

        # --- Synergie Amazon ---
        amazon = self.profile.amazon_usage
        if amazon in ["Oui, je fais la majorité de mes achats en ligne via Amazon",
                      "Oui, mais c'est un parmi plusieurs sites"]:
            if "amazon" in card.name.lower():
                score = min(1.0, score + 0.12)
            # Les cartes avec bon taux "online" beneficient aussi
            if card.get_reward_rate("online") >= 3.0:
                score = min(1.0, score + 0.05)

        # --- Bonus Amex presale (billets d'evenements) ---
        presale = self.profile.presale_interest
        event_tickets = self.profile.event_tickets
        if presale in ["Oui, je l'utilise souvent", "Oui, c'est important pour moi"] or \
           event_tickets in ["Oui, regulierement", "Oui, régulièrement"]:
            if card.network == CardNetwork.AMEX:
                score = min(1.0, score + 0.10)   # Presale Amex = avantage reel

        # --- Destinations de voyage (frais FX sur achat international) ---
        travel_dest = self.profile.travel_destinations
        if travel_dest in ["En Europe principalement", "En Asie principalement",
                           "Partout dans le monde", "Aux États-Unis principalement"]:
            if card.no_fx_fee:
                score = min(1.0, score + 0.12)  # Pas de frais FX = avantage majeur
            elif travel_dest in ["En Europe principalement", "En Asie principalement",
                                 "Partout dans le monde"]:
                score -= 0.08  # FX 2.5% sur voyages hors Amérique du Nord = pénalité

        # --- Amazon Prime : achats Amazon fréquents ---
        if self.profile.amazon_prime == "Oui":
            if "amazon" in card.name.lower():
                score = min(1.0, score + 0.10)  # Carte Amazon = match parfait pour membre Prime
            elif card.get_reward_rate("online") >= 3.0:
                score = min(1.0, score + 0.05)  # Bon taux online = 2e meilleur choix

        # --- Walmart : atténue la pénalité Amex si épiceries incompatibles ---
        if self.profile.uses_walmart in ["Oui, régulièrement", "Oui, occasionnellement"]:
            if card.network == CardNetwork.AMEX:
                grocery_lower = [s.lower() for s in self.profile.grocery_stores]
                loblaws_stores = ["maxi", "provigo", "loblaws", "real canadian superstore"]
                has_incompatible = any(any(l in g for l in loblaws_stores) for g in grocery_lower)
                if has_incompatible:
                    score = min(1.0, score + 0.08)  # Walmart accepte Amex → compense partiellement

        return max(0.0, min(1.0, score))

    def _score_points_quality(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : qualite du programme de points (CPP + flexibilite).

        Benchmarks 2025 (Milesopedia / Prince of Travel):
        - Amex MR: 2.0 cpp (transferable Aeroplan/Avios) => score 1.0
        - Aeroplan: 1.6 cpp => score 0.80
        - RBC Avion Elite: 1.5 cpp => score 0.75
        - Scene+ Travel: 1.0 cpp => score 0.50
        - TD/BMO/CIBC: 0.8 cpp => score 0.40
        - Cashback pur: 1.0 cpp avec bonus de simplicite => score 0.60
        """
        if not card.reward_program:
            # Carte sans programme => probablement cashback direct
            if card.tier in [CardTier.CASHBACK, CardTier.NO_FEE]:
                return 0.55   # Cashback simple = bonne valeur
            return 0.40

        prog = card.reward_program.lower()
        cpp = self._get_card_cpp_value(card)

        # Score de base base sur CPP (2.0 cpp = 1.0)
        base_score = min(1.0, cpp / 2.0)

        # Bonus flexibilite (programmes transferables = plus de valeur potentielle)
        flexibility_bonus = 0.0
        transferable = ["mr points", "membership rewards", "aeroplan", "aéroplan",
                        "avion", "scene+"]
        if any(t in prog for t in transferable):
            flexibility_bonus = 0.15

        # Bonus cashback (simplicite = valeur pour certains profils)
        if "cashback" in prog or "cash back" in prog:
            flexibility_bonus = 0.10  # Simplicite = avantage pour certains

        # Penalite si programme de mauvaise repute ou valeur faible
        low_value = ["td rewards", "bmo rewards", "cibc rewards"]
        if any(lv in prog for lv in low_value):
            base_score = max(0.30, base_score - 0.10)

        return min(1.0, base_score + flexibility_bonus)

    def _score_eligibility(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : probabilite d'approbation (revenu + credit).
        """
        income = self._parse_income(self.profile.income_personal)
        credit = self._parse_credit_score()

        # Score de revenu
        if card.min_income_personal > 0 and income > 0:
            if income >= card.min_income_personal * 1.1:
                income_score = 1.0    # Bien au-dessus du minimum
            elif income >= card.min_income_personal:
                income_score = 0.85   # Juste au minimum
            elif income >= card.min_income_personal * 0.85:
                income_score = 0.50   # Legerement en dessous (approbation possible)
            elif income >= card.min_income_personal * 0.70:
                income_score = 0.25
            else:
                income_score = 0.05   # Peu probable d'etre approuve
        else:
            income_score = 1.0        # Pas de minimum, ou revenu non declare

        # Score de credit
        gap = credit - card.min_credit_score
        if gap >= 60:
            credit_score = 1.0
        elif gap >= 30:
            credit_score = 0.90
        elif gap >= 0:
            credit_score = 0.75
        elif gap >= -30:
            credit_score = 0.40
        else:
            credit_score = 0.05

        # Penalite si refuse recemment
        if self.profile.denied_recently == "Oui":
            credit_score *= 0.60

        # Ajustement premier cardholder (sans historique de carte de crédit)
        if not self.profile.has_cards:
            if card.annual_fee == 0 or card.tier == CardTier.STUDENT:
                credit_score = min(1.0, credit_score * 1.10)  # Cartes accessibles = meilleure chance
            elif card.annual_fee > 150:
                credit_score = max(0.0, credit_score * 0.90)  # Premium risqué sans historique

        # Ajustement selon le nombre de cartes actuelles (crédit établi)
        num_str = str(self.profile.num_cards)
        if num_str == "5 et plus" or (isinstance(self.profile.num_cards, int) and self.profile.num_cards >= 5):
            credit_score = min(1.0, credit_score * 1.05)  # Nombreuses cartes = crédit établi

        # Ajustement étudiant confirmé (établissement scolaire déclaré)
        school = self.profile.school_type
        if school in ["Oui, université", "Oui, CEGEP", "Oui, collège ou école technique"]:
            if card.tier == CardTier.STUDENT or card.annual_fee == 0:
                credit_score = min(1.0, credit_score * 1.10)  # Carte étudiant/sans frais = accessible

        # Ponderee : revenu 40%, credit 60%
        return income_score * 0.40 + credit_score * 0.60

    def _score_interest_rate(self, card: CreditCard) -> float:
        """
        Score 0.0-1.0 : adéquation du taux d'intérêt au comportement de paiement.

        Critique pour les porteurs de solde — un taux à 19.99% peut effacer des
        années de récompenses en quelques mois.

        Pour les payeurs intégraux, ce score est quasi-neutre (poids = 0.0 dans
        _derive_priority_weights, donc ne compte pas dans la moyenne pondérée).
        """
        behavior = self.profile.pays_balance_full
        rate = card.interest_rate

        if behavior in ["Toujours", "Presque toujours", ""]:
            # Taux irrelevant — ils paient avant les intérêts
            return 0.75

        if behavior == "Parfois":
            # Porte un solde occasionnellement — taux bas valorisé
            if rate <= 9.99:   return 1.00
            if rate <= 12.99:  return 0.80
            if rate <= 15.99:  return 0.60
            if rate <= 19.99:  return 0.40
            return 0.15

        if behavior in ["Rarement", "Jamais"]:
            # Porte presque toujours un solde — le taux est CRITIQUE
            if rate <= 9.99:   return 1.00
            if rate <= 12.99:  return 0.80
            if rate <= 15.99:  return 0.40
            if rate <= 19.99:  return 0.10
            return 0.02

        return 0.75

    def _calculate_red_flags(self, card: CreditCard) -> float:
        """
        Calcule un multiplicateur de penalite pour les red flags critiques.

        Multiplicateurs : de 0.0 (elimination) a 1.0 (aucune penalite).
        Les penalites sont multiplicatives entre elles.

        Red flags:
        1. Costco regulier + Visa/Amex => quasi-elimination
        2. Amex + epiceries uniquement incompatibles => forte penalite
        3. Preference cashback stricte + carte points-only => forte penalite
        4. Ne voyage pas + carte voyage premium => penalite moderee
        5. Porte un solde + frais d'interet eleves => penalite
        6. Institution exclue => elimination totale
        7. Refuse recemment + carte exigeante => penalite
        8. Dette elevee + carte premium (frais > 200$) => penalite
        9. Preference points stricte + carte cashback-only => penalite moderee
        10. Etudiant + carte sans option etudiante (si besoin) => penalite legere
        """
        multiplier = 1.0

        # 1. COSTCO + Visa/Amex (incompatibilite totale : Costco = MC seulement)
        uses_costco = self.profile.uses_costco
        if uses_costco in ["Oui, regulierement", "Oui, régulièrement"]:
            if card.network in [CardNetwork.VISA, CardNetwork.AMEX]:
                multiplier *= 0.12   # Quasi-elimination
        elif uses_costco == "Oui, occasionnellement":
            if card.network in [CardNetwork.VISA, CardNetwork.AMEX]:
                multiplier *= 0.55

        # 2. AMEX + epiceries uniquement incompatibles
        if card.network == CardNetwork.AMEX:
            grocery_stores_lower = [s.lower() for s in self.profile.grocery_stores]
            amex_incompatible = ["maxi", "provigo", "loblaws", "real canadian superstore"]
            if grocery_stores_lower:
                all_incompatible = all(
                    any(inc in s for inc in amex_incompatible)
                    for s in grocery_stores_lower
                )
                if all_incompatible:
                    multiplier *= 0.38   # L'utilisateur ne peut PAS utiliser Amex pour l'epicerie

        # 3. CASHBACK STRICT + Carte points-seulement (sans option rachat cashback)
        if self._prefers_cashback():
            prog = (card.reward_program or "").lower()
            is_points_only = card.tier in [CardTier.TRAVEL, CardTier.PREMIUM] and \
                             "cashback" not in prog and "cash back" not in prog and \
                             "scene+" not in prog and "westjet" not in prog
            if is_points_only and card.base_rate < 1.0:
                multiplier *= 0.55

        # 4. NE VOYAGE PAS + carte voyage premium a frais eleves
        if not self._travels_frequently():
            if card.annual_fee > 200 and card.tier in [CardTier.TRAVEL, CardTier.PREMIUM]:
                # Les avantages voyage ne serviront jamais
                multiplier *= 0.50

        # 5. PORTE UN SOLDE (rarement/jamais payé en entier)
        if self.profile.pays_balance_full in ["Rarement", "Jamais"]:
            if card.annual_fee > 150:
                # Les interets vont eliminer tous les benefices
                multiplier *= 0.60
            if card.interest_rate > 25:
                multiplier *= 0.70

        # 6. INSTITUTION EXCLUE => elimination totale
        if self.profile.excluded_institutions:
            if card.issuer.lower() in self.profile.excluded_institutions.lower():
                multiplier *= 0.0

        # 7. REFUSE RECEMMENT + carte a criteres eleves
        if self.profile.denied_recently == "Oui":
            if card.min_credit_score >= 720 or card.min_income_personal >= 60000:
                multiplier *= 0.40

        # 8. DETTE ELEVEE + carte premium
        if self.profile.has_debt in ["Oui, 5 000 $ et plus"] and card.annual_fee > 200:
            multiplier *= 0.50

        # 9. PREFERENCE POINTS STRICT + carte cashback seulement
        if self._prefers_points() and card.tier == CardTier.CASHBACK:
            if not card.reward_program or "cashback" in (card.reward_program or "").lower():
                multiplier *= 0.70

        # 10. EPICERIE COSTCO GAS STATION + Amex (Costco n'accepte pas Amex)
        gas_stations_lower = [s.lower() for s in self.profile.gas_stations]
        if "costco" in gas_stations_lower and card.network == CardNetwork.AMEX:
            if uses_costco not in ["Rarement", "Jamais"]:
                multiplier *= 0.65

        # 11. DEPENSES ETRANGERES ELEVEES + carte avec frais FX (2.5%)
        spending_foreign = self.profile.spending_foreign
        foreign_purchases = self.profile.foreign_purchases
        heavy_fx_user = (
            spending_foreign > 300 or
            foreign_purchases in ["Tres souvent", "Très souvent",
                                   "Souvent (plusieurs fois/mois)"]
        )
        if heavy_fx_user:
            has_no_fx = ("US Dollar" in card.name or "USD" in card.name)
            if not has_no_fx:
                # Les frais FX (2.5%) peuvent effacer tous les gains sur achats etrangers
                fx_penalty_ratio = min(0.30, (spending_foreign * 0.025 * 12) /
                                       max(1, spending_foreign * 12))
                multiplier *= max(0.65, 1.0 - fx_penalty_ratio * 3)

        # 12. BILLETS EVENEMENTS + pas Amex (presale Amex tres valorisee)
        presale_important = self.profile.presale_interest in [
            "Oui, je l'utilise souvent", "Oui, c'est important pour moi"
        ]
        event_heavy = self.profile.event_tickets in [
            "Oui, regulierement", "Oui, régulièrement"
        ]
        if (presale_important or event_heavy) and card.network != CardNetwork.AMEX:
            multiplier *= 0.88   # Penalite legere : perd l'avantage presale Amex

        # 13. TRAVAILLEUR AUTONOME + carte personnelle (devrait avoir carte affaires)
        if self.profile.business_registered in ["Oui, incorporated",
                                                  "Oui, enregistrée non incorporée",
                                                  "Oui, enregistree non incorporee"]:
            if card.tier == CardTier.BUSINESS:
                multiplier = min(1.0, multiplier * 1.0)   # Pas de penalite (booste ailleurs)
            # Si depenses d'affaires elevees + carte personnelle : sous-optimal
            biz_spending = self.profile.spending_business
            if biz_spending > 1000 and card.tier != CardTier.BUSINESS:
                multiplier *= 0.85   # Carte personnelle = pas deductible d'impot optimalement

        # 14. AGE 65+ + voyages longs + couverture medicale insuffisante
        if self.profile.age_range == "65 ans et plus":
            long_stays = self.profile.long_stays in [
                "Oui, regulierement", "Oui, régulièrement", "Oui, parfois"
            ]
            if long_stays and card.insurance.travel_medical:
                # La plupart des cartes limitent a 15-21 jours pour 65+
                # Un senior qui voyage souvent longtemps prend un risque
                multiplier *= 0.80   # Avertissement fort

        # 15. DESJARDINS HORS QUEBEC (adhesion caisse requise, difficile ailleurs)
        if "Desjardins" in card.issuer:
            province = self.profile.province
            if province and province not in ["Québec", "Quebec", "Ontario", ""]:
                multiplier *= 0.60   # Desjardins = tres difficile hors QC/ON

        # 16b. DÉPENSES PUBLICITAIRES ÉLEVÉES + carte non-business
        if self.profile.ad_spending == "Oui, plus de 1 000 $/mois":
            if card.tier != CardTier.BUSINESS:
                multiplier *= 0.90  # Légère pénalité : carte business serait plus optimale fiscalement

        # 17. MUST-HAVE FEATURE — critères non-négociables (analyse par mots-clés)
        must_have = (self.profile.must_have_feature or "").lower().strip()
        if must_have:
            kw_lounge = any(kw in must_have for kw in ["lounge", "salon"])
            kw_cashback = any(kw in must_have for kw in ["cashback", "cash back", "remboursement", "remise"])
            kw_aeroplan = any(kw in must_have for kw in ["aeroplan", "aéroplan"])
            kw_nofee = any(kw in must_have for kw in ["sans frais", "no fee", "gratuit", "frais 0"])
            kw_nexus = "nexus" in must_have

            if kw_lounge and not card.travel_perks.lounge_access:
                multiplier *= 0.35   # Critique : lounge demandé, carte sans lounge
            if kw_cashback:
                prog = (card.reward_program or "").lower()
                if card.tier not in [CardTier.CASHBACK, CardTier.NO_FEE] and \
                   "cashback" not in prog and "cash back" not in prog:
                    multiplier *= 0.55
            if kw_aeroplan:
                prog = (card.reward_program or "").lower()
                if "aeroplan" not in prog and "aéroplan" not in prog:
                    multiplier *= 0.45
            if kw_nofee and card.annual_fee > 0:
                multiplier *= 0.25   # Critique : veut absolument sans frais annuels
            if kw_nexus and not card.travel_perks.nexus_credit:
                multiplier *= 0.60

        # 16. PREFERENCE BANCAIRE — le facteur manquant
        open_to_bank = self.profile.open_to_new_bank
        from_user_bank = self._card_is_from_user_bank(card)
        requires_bank = self._card_requires_bank_relationship(card)
        is_standalone = not requires_bank  # Amex, Neo, KOHO, Capital One, etc.

        if open_to_bank == "Non, je préfère rester avec mon institution actuelle":
            # ROUGE : l'utilisateur veut absolument rester dans sa banque
            if from_user_bank:
                pass  # Pas de pénalité, c'est sa banque — avantage relatif
            elif is_standalone:
                # Amex/Neo/KOHO ne requièrent pas de changer de banque
                # => pénalité légère seulement (pas de vrai changement demandé)
                multiplier *= 0.80
            else:
                # Autre banque = vrai changement de relation bancaire
                multiplier *= 0.45

        elif open_to_bank == "Oui, mais seulement si le bénéfice est clairement supérieur":
            # JAUNE : préférence pour sa banque, mais pas un blocage absolu
            if from_user_bank:
                pass  # Pas de pénalité
            elif is_standalone:
                multiplier *= 0.92  # Quasi-neutre, Amex ne demande pas de changer
            else:
                multiplier *= 0.75  # Pénalité modérée pour les autres banques

        elif open_to_bank == "Non, je ne veux aucun compte bancaire lié à ma carte":
            # L'utilisateur veut une carte totalement indépendante de sa banque
            # => pénaliser les cartes qui requièrent une relation bancaire
            if requires_bank and not from_user_bank:
                multiplier *= 0.55  # Pas sa banque ET requiert un compte = problème
            elif requires_bank and from_user_bank:
                multiplier *= 0.80  # Sa banque mais il veut rester détaché

        # "Oui, sans problème" => aucun ajustement

        return max(0.0, multiplier)

    # ==================== DUO CARDS ====================

    def _calculate_duo_combined_rewards(
        self,
        card1: CreditCard,
        card2: CreditCard,
        spending: Dict[str, float]
    ) -> Tuple[float, Dict[str, str]]:
        """
        Calcule la valeur optimale des récompenses en utilisant deux cartes.
        Pour chaque catégorie, on utilise la carte qui rapporte le plus
        (après CPP et caps mensuels).
        """
        total = 0.0
        category_winner: Dict[str, str] = {}

        cpp1 = self._get_card_cpp_value(card1)
        cpp2 = self._get_card_cpp_value(card2)
        loblaws1 = self._check_amex_loblaws_constraint(card1)
        loblaws2 = self._check_amex_loblaws_constraint(card2)

        for category, amount in spending.items():
            if amount <= 0:
                continue

            # Effective annual value — card 1
            rate1 = card1.get_reward_rate(category)
            if category == "groceries" and loblaws1:
                rate1 = min(rate1, 1.0)
            cap1 = card1.get_reward_cap(category)
            if cap1 and amount > cap1:
                effective_rate1 = (cap1 * rate1 + (amount - cap1) * card1.base_rate) / amount
            else:
                effective_rate1 = rate1
            val1 = amount * 12 * (effective_rate1 * cpp1 / 100)

            # Effective annual value — card 2
            rate2 = card2.get_reward_rate(category)
            if category == "groceries" and loblaws2:
                rate2 = min(rate2, 1.0)
            cap2 = card2.get_reward_cap(category)
            if cap2 and amount > cap2:
                effective_rate2 = (cap2 * rate2 + (amount - cap2) * card2.base_rate) / amount
            else:
                effective_rate2 = rate2
            val2 = amount * 12 * (effective_rate2 * cpp2 / 100)

            if val1 >= val2:
                total += val1
                category_winner[category] = card1.name
            else:
                total += val2
                category_winner[category] = card2.name

        return total, category_winner

    def recommend_duo(self) -> Optional[DuoRecommendation]:
        """
        Trouve la meilleure paire de cartes complémentaires.

        Pour chaque catégorie de dépense, la carte qui rapporte le plus est
        utilisée. Le ROI combiné est comparé au meilleur ROI en carte unique.
        N'est retourné que si le gain additionnel dépasse 50$/an.
        """
        if self.profile.open_to_multiple == "Non, une seule carte":
            return None
        if self.profile.desired_num_cards == "1 seule":
            return None

        candidates = self._filter_eligible_cards()
        if len(candidates) < 2:
            return None

        spending = self._get_spending_dict_no_alias()

        # Score initial rapide par ROI seul (évite O(n²) sur 100 cartes)
        scored = [(self._calculate_roi(card), card) for card in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_single_roi = scored[0][0]
        top_n = [card for _, card in scored[:20]]

        best_duo: Optional[Tuple] = None
        best_duo_roi = -9999.0

        for i in range(len(top_n)):
            for j in range(i + 1, len(top_n)):
                c1, c2 = top_n[i], top_n[j]

                combined_rewards, split = self._calculate_duo_combined_rewards(c1, c2, spending)

                wb1 = self._amortize_welcome_bonus(c1)
                wb2 = self._amortize_welcome_bonus(c2)
                tv1 = self._calculate_travel_value(c1)
                tv2 = self._calculate_travel_value(c2)
                ins1 = self._calculate_insurance_value(c1)
                ins2 = self._calculate_insurance_value(c2)
                tc1 = c1.travel_perks.travel_credit_annual
                tc2 = c2.travel_perks.travel_credit_annual
                # FX : l'utilisateur route ses dépenses étrangères vers la meilleure carte
                fx_penalty = min(self._calculate_fx_penalty(c1), self._calculate_fx_penalty(c2))
                fee1 = 0.0 if c1.first_year_free else c1.annual_fee
                fee2 = 0.0 if c2.first_year_free else c2.annual_fee

                duo_roi = (combined_rewards + wb1 + wb2 + tv1 + tv2
                           + ins1 + ins2 + tc1 + tc2 - fx_penalty - fee1 - fee2)

                if duo_roi > best_duo_roi:
                    best_duo_roi = duo_roi
                    best_duo = (c1, c2, split)

        if best_duo is None:
            return None

        extra_gain = best_duo_roi - best_single_roi
        if extra_gain < 50.0:
            return None

        return DuoRecommendation(
            card_primary=best_duo[0],
            card_secondary=best_duo[1],
            combined_roi=round(best_duo_roi, 2),
            best_single_roi=round(best_single_roi, 2),
            extra_gain=round(extra_gain, 2),
            category_split=best_duo[2],
        )

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

    def _card_is_from_user_bank(self, card: CreditCard) -> bool:
        """
        Vérifie si la carte est émise par une des banques actuelles de l'utilisateur.
        Amex est considéré standalone (pas une banque traditionnelle).
        """
        if not self.profile.banks:
            return False
        issuer_lower = card.issuer.lower()
        for bank in self.profile.banks:
            keywords = BANK_ISSUER_MAP.get(bank, [bank])
            if any(kw.lower() in issuer_lower for kw in keywords):
                return True
        return False

    def _card_requires_bank_relationship(self, card: CreditCard) -> bool:
        """
        Certaines cartes nécessitent implicitement d'être client de la banque
        (ex: Desjardins = membership caisse obligatoire).
        Amex, Capital One, KOHO, Neo = standalone, pas de compte requis.
        """
        standalone_issuers = ["amex", "american express", "capital one",
                               "koho", "neo", "brim", "home trust",
                               "mbna", "tangerine", "simplii", "eq bank"]
        issuer_lower = card.issuer.lower()
        return not any(s in issuer_lower for s in standalone_issuers)

    # ==================== MÉTHODES UTILITAIRES ====================

    def _get_spending_dict(self) -> Dict[str, float]:
        """Retourne un dict complet des dépenses mensuelles (toutes catégories)."""
        return {
            "groceries":     self.profile.spending_groceries,
            "gas":           self.profile.spending_gas,
            "restaurants":   self.profile.spending_restaurants,
            "dining":        self.profile.spending_restaurants,  # alias
            "pharmacy":      self.profile.spending_pharmacy,
            "transport":     self.profile.spending_transport,
            "transit":       self.profile.spending_transport,    # alias
            "subscriptions": self.profile.spending_subscriptions,
            "streaming":     self.profile.spending_subscriptions, # alias
            "entertainment": self.profile.spending_entertainment,
            "online":        self.profile.spending_online,
            "electronics":   self.profile.spending_electronics,
            "clothing":      self.profile.spending_clothing,
            "healthcare":    self.profile.spending_healthcare,
            "business":      self.profile.spending_business,
        }

    def _get_spending_dict_no_alias(self) -> Dict[str, float]:
        """Dépenses sans alias (pour éviter double-comptage dans le ROI)."""
        d = {
            "groceries":     self.profile.spending_groceries,
            "gas":           self.profile.spending_gas,
            "restaurants":   self.profile.spending_restaurants,
            "pharmacy":      self.profile.spending_pharmacy,
            "transport":     self.profile.spending_transport,
            "subscriptions": self.profile.spending_subscriptions,
            "entertainment": self.profile.spending_entertainment,
            "online":        self.profile.spending_online,
            "electronics":   self.profile.spending_electronics,
            "clothing":      self.profile.spending_clothing,
            "healthcare":    self.profile.spending_healthcare,
            "business":      self.profile.spending_business,
        }
        # Dépenses non-allouées : si total_monthly déclaré > somme des postes détaillés,
        # le surplus est comptabilisé au taux de base (dépenses générales non-catégorisées)
        declared_total = self._parse_total_monthly()
        item_total = sum(v for v in d.values() if v > 0)
        unallocated = max(0.0, declared_total - item_total)
        if unallocated > 20:
            d["misc"] = unallocated
        return d

    def _parse_total_monthly(self) -> float:
        """Parse le budget mensuel total déclaré en valeur numérique."""
        mapping = {
            "Moins de 500 $": 400.0,
            "500–999 $": 750.0,
            "1 000–1 999 $": 1500.0,
            "2 000–2 999 $": 2500.0,
            "3 000–4 999 $": 4000.0,
            "5 000–7 499 $": 6000.0,
            "7 500–9 999 $": 8500.0,
            "10 000 $ et plus": 12000.0,
        }
        return mapping.get(self.profile.total_monthly, 0.0)

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
