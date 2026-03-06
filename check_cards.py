#!/usr/bin/env python3
"""
Script pour vérifier les cartes disponibles dans la base de données
"""

from card_database import get_all_cards

def main():
    cards = get_all_cards()
    print(f"Nombre total de cartes: {len(cards)}")

    print("\n=== LISTE DES CARTES ===")
    for card in cards:
        print(f"- {card.name}")
        print(f"  Émetteur: {card.issuer}")
        print(f"  Réseau: {card.network.value}")
        print(f"  Frais annuels: {card.annual_fee}$")
        print(f"  Score de crédit minimum: {card.min_credit_score}")
        print()

if __name__ == "__main__":
    main()