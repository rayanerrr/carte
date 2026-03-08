"""
Entraînement du classifieur de marchands pour relevés de carte de crédit canadiens.
Modèle : TF-IDF (mots + caractères) + Régression Logistique multinomiale.
Exécution : python3 train_classifier.py
Produit   : merchant_classifier.pkl
"""

import random
import joblib
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import numpy as np

random.seed(42)

# ---------------------------------------------------------------------------
# Données d'entraînement — marchands canadiens réels par catégorie
# ---------------------------------------------------------------------------
RAW_DATA = {
    "spending_groceries": [
        # Québec
        "MAXI", "MAXI ET CIE", "IGA", "IGA EXTRA", "METRO", "METRO PLUS",
        "PROVIGO", "PROVIGO LE MARCHE", "SUPER C", "SUPER-C",
        "RACHELLE-BERY", "AVRIL SUPERMARCHE", "MARCHE TAU",
        "INTERMARCHE", "MARCHE RICHELIEU", "MARCHE TRADITION",
        "ALIMENTATION COUCHE-TARD EPICERIE", "FRUITERIE 440",
        "BOULANGERIE PREMIERE MOISSON", "FROMAGERIE ATWATER",
        "EPICERIE LATINA", "MARCHE DU MIDI",
        # Ontario / National
        "LOBLAWS", "LOBLAW", "REAL CANADIAN SUPERSTORE", "SUPERSTORE",
        "SAVE ON FOODS", "SAFEWAY", "SOBEYS", "FRESHCO", "NO FRILLS",
        "NOFRILLS", "FOOD BASICS", "FARM BOY", "WHOLE FOODS MARKET",
        "T&T SUPERMARKET", "FARM BOY MARKET",
        # Services épicerie
        "PC EXPRESS", "INSTACART", "GOODFOOD", "HELLO FRESH",
        "HELLOFRESH", "CHEF S PLATE", "MISS FRESH", "VERT BON",
        # Costco / Walmart alimentaire
        "COSTCO WHSE", "COSTCO WHOLESALE", "WALMART", "WALMART SUPERCENTRE",
        "WALMART GROCERY",
        # Générique
        "EPICERIE", "SUPERMARCHE", "MARCHE", "ALIMENTATION",
        "BOUCHERIE", "FROMAGERIE", "BOULANGERIE", "PATISSERIE",
        "FRUITERIE", "POISSONNERIE", "CREMERIE", "CHARCUTERIE",
    ],

    "spending_gas": [
        "PETRO-CANADA", "PETROCANADA", "PETRO CANADA", "PETRO-CAN",
        "ESSO", "ESSO EXPRESS", "ESSO STATION",
        "SHELL", "SHELL CANADA",
        "ULTRAMAR", "ULTRAMAR STATION",
        "IRVING OIL", "IRVING GAS",
        "PIONEER", "SUNOCO", "HUSKY", "PARKLAND FUEL",
        "CANADIAN TIRE GAS BAR", "CT GAS BAR", "CANADIAN TIRE ESSENCE",
        "COUCHE-TARD ESSENCE", "COUCHE TARD GAS", "STATION COUCHE-TARD",
        "ESSENCE", "CARBURANT", "GAZ STATION", "STATION SERVICE",
        "FUEL", "GASOLINE", "GAS BAR",
    ],

    "spending_restaurants": [
        # Chaînes fast food
        "MCDONALD S", "MCDONALDS", "MC DONALDS",
        "TIM HORTONS", "TIMHORTONS", "TIM HORTON",
        "SUBWAY",
        "BURGER KING", "BURGERKING",
        "KFC",
        "A W RESTAURANT", "A AND W",
        "HARVEY S", "HARVEYS",
        "WENDY S", "WENDYS",
        "POPEYES", "POPEYES LOUISIANA",
        "FIVE GUYS", "FIVE GUYS BURGERS",
        "CHIPOTLE", "CHIPOTLE MEXICAN GRILL",
        "TACO BELL", "TACOBELL",
        "DAIRY QUEEN", "ORANGE JULIUS",
        # Café / Boulangerie
        "STARBUCKS", "STARBUCKS COFFEE",
        "SECOND CUP", "SECONDCUP",
        "VAN HOUTTE", "PRESSE CAFE", "CAFE DEPOT", "CAFE JAVA",
        "WILLIAMS COFFEE PUB", "TIM S COFFEE",
        "DUNKIN DONUTS", "ROBIN S DONUTS",
        # Pizza
        "PIZZA PIZZA", "PIZZA HUT", "PIZZAHUT",
        "DOMINO S", "DOMINOS PIZZA",
        "PIZZA DELIGHT", "PIZZA NOVA", "241 PIZZA",
        "PIZZA INCOME", "PIZZA ROYALE",
        # Québec
        "ST-HUBERT", "SAINT-HUBERT", "ROTISSERIE ST-HUBERT",
        "LA BELLE PROVINCE", "BELLE PROVINCE",
        "SCORES RESTAURANT", "VALENTINS",
        "BATON ROUGE",
        "ASHTON", "CHEZ ASHTON",
        # Chaînes sit-down
        "BOSTON PIZZA", "EAST SIDE MARIO S",
        "SWISS CHALET", "SWISSCHALET",
        "KELSEYS", "KELSEY S", "MOXIES", "CACTUS CLUB",
        "JOEY RESTAURANT", "MILESTONES",
        "MONTANA S", "JACK ASTOR S",
        # Livraison repas
        "UBER EATS", "UBEREATS", "UBER EATS CA",
        "DOORDASH", "DOOR DASH",
        "SKIP THE DISHES", "SKIPTHEDISHES",
        "GRUBHUB", "FOODORA",
        # Restaurants génériques
        "RESTAURANT", "RESTO", "BISTRO", "BRASSERIE",
        "CAFE", "CAFETERIA", "CANTINE", "SNACK BAR",
        "SUSHI", "RAMEN", "PHO", "THAI", "INDIEN",
        "GREC", "ITALIAN", "MEXICAIN", "LIBANAIS",
        "PUB", "BAR", "TAVERNE",
        "BUFFET", "ROTI", "HALAL", "POUTINE",
    ],

    "spending_pharmacy": [
        "JEAN COUTU", "JEAN-COUTU",
        "PHARMAPRIX",
        "SHOPPERS DRUG MART", "SHOPPERS",
        "UNIPRIX",
        "PROXIM",
        "BRUNET", "BRUNET CLINIQUE",
        "REXALL", "PHARMA PLUS", "PHARMAPLUS",
        "CLINIQUE PHARMACIE", "PHARMACIEN PROPRIETAIRE",
        "PHARMACIE", "PHARMACY", "DRUG MART", "DRUG STORE",
    ],

    "spending_transport": [
        # Covoiturage
        "UBER", "UBER TRIP", "UBER TECHNOLOGIES",
        "LYFT", "LYFT RIDE",
        # Taxi
        "TAXI", "TAXICAB", "TAXI DIAMOND", "TAXI COOP",
        "TAXI HOCHELAGA", "CHAMPLAIN TAXI", "APITO TAXI",
        # Transit Québec
        "STM", "STM OPUS", "OPUS STM", "SOCIETE TRANSPORT MTL",
        "RTC VILLE QUEBEC", "STO OUTAOUAIS", "RTL", "EXCO",
        # Transit Ontario / National
        "PRESTO CARD", "GO TRANSIT", "GOTRANSIT",
        "TTC", "TORONTO TRANSIT", "BRAMPTON TRANSIT",
        "OCTRANSPO", "OC TRANSPO",
        "TRANSLINK", "BC TRANSIT",
        # Train
        "VIA RAIL", "VIARAIL", "VIA RAIL CANADA",
        # Autobus longue distance
        "GREYHOUND", "MEGABUS", "FLIXBUS", "ORLEANS EXPRESS",
        "GALLAND", "AUTOBUS GALLAND",
        # Stationnement
        "PARKING", "STATIONNEMENT", "PARC AUTO",
        "IMPARK", "GREEN P", "INDIGO PARKING",
        "DRIVEWAY PARKING", "STATIONNEMENT DU VIEUX",
        # Autopartage / Location
        "COMMUNAUTO",
        "ENTERPRISE RENT A CAR", "HERTZ", "AVIS", "BUDGET RENT",
        "NATIONAL CAR RENTAL", "DOLLAR RENT A CAR", "THRIFTY",
        # Vélo
        "BIXI", "BIXI MONTREAL",
    ],

    "spending_subscriptions": [
        # Vidéo
        "NETFLIX",
        "DISNEY PLUS", "DISNEY+", "DISNEYPLUS",
        "AMAZON PRIME VIDEO", "PRIME VIDEO",
        "CRAVE", "CRAVE TV",
        "APPLE TV PLUS", "APPLE TV+",
        "PARAMOUNT PLUS", "PARAMOUNT+",
        "HULU",
        "DAZN",
        "TSN DIRECT", "SPORTSNET NOW",
        "TOU.TV", "ICI TOU.TV",
        "CBC GEM",
        # Musique
        "SPOTIFY", "SPOTIFY AB",
        "APPLE MUSIC", "ITUNES",
        "YOUTUBE PREMIUM", "YOUTUBE MUSIC",
        "AMAZON MUSIC",
        "TIDAL",
        # Logiciels / Cloud
        "APPLE SUBSCRIPTIONS", "APPLE.COM BILL",
        "GOOGLE PLAY", "GOOGLE ONE",
        "MICROSOFT 365", "OFFICE 365",
        "DROPBOX",
        "ADOBE", "CREATIVE CLOUD",
        "ICLOUD",
        # Télécoms (factures mensuelles)
        "BELL CANADA", "BELL MOBILITY", "BELL FIBE", "BELL INTERNET",
        "VIDEOTRON", "VIDEOTRON LTEE",
        "TELUS", "TELUS MOBILITY", "TELUS COMMUNICATIONS",
        "ROGERS", "ROGERS WIRELESS", "ROGERS COMMUNICATIONS",
        "FIDO", "FIDO SOLUTIONS",
        "KOODO", "KOODO MOBILE",
        "VIRGIN MOBILE", "VIRGIN PLUS",
        "FREEDOM MOBILE",
        "CHATR MOBILE",
        "PUBLIC MOBILE",
        "EASTLINK",
        # Divers abonnements
        "TWITCH",
        "PATREON",
        "LINKEDIN PREMIUM",
        "DUOLINGO PLUS",
        "CALM APP",
        "AMAZON SUBSCRIBE AND SAVE",
        "ABONNEMENT",
    ],

    "spending_entertainment": [
        # Cinéma
        "CINEPLEX", "CINEPLEX ENTERTAINMENT",
        "CINEMA GUZZO", "CINEMA STAR", "CINEMA BEAUBIEN",
        "IMAX",
        # Événements
        "TICKETMASTER", "EVENKO", "EVENTBRITE",
        "ADMISSION.COM", "BILLETECH", "SPECTRA",
        # Jeux vidéo (achats ponctuels)
        "STEAM", "STEAM GAMES",
        "PLAYSTATION STORE", "PS STORE",
        "XBOX STORE", "MICROSOFT STORE GAME",
        "NINTENDO ESHOP",
        "EPIC GAMES",
        "BLIZZARD", "RIOT GAMES",
        # Sports / Fitness
        "GOODLIFE FITNESS",
        "ANYTIME FITNESS",
        "YMCA", "YWCA",
        "ENERGIE CARDIO", "NAUTILUS PLUS",
        "GYM", "FITNESS", "CROSSFIT",
        "YOGA STUDIO",
        # Culture / Livres
        "CHAPTERS INDIGO", "INDIGO", "CHAPTERS",
        "ARCHAMBAULT", "RENAUD-BRAY",
        "BIBLIOTHEQUE", "LIBRAIRIE",
        "MUSEE", "MUSEUM", "GALERIE ART",
        "THEATRE", "OPERA", "ORCHESTRE",
        # Loisirs
        "CASINO DE MONTREAL", "LOTO-QUEBEC",
        "LOTTERY", "CASINO",
        "LASER QUEST", "LASER TAG",
        "BOWLING", "GOLF CLUB",
        "KARTING", "PAINTBALL",
        "CONCERT", "FESTIVAL", "SPECTACLE",
    ],

    "spending_online": [
        # Marketplaces
        "AMAZON.CA", "AMAZON CA", "AMAZON MARKETPLACE",
        "AMAZON.COM",
        "EBAY", "EBAY.CA",
        "ETSY",
        "ALIEXPRESS",
        "WISH",
        # Mode
        "SHEIN",
        "ZARA", "ZARA.COM",
        "H AND M", "HM.COM",
        "ASOS",
        "REITMANS",
        "SIMONS",
        "DYNAMITE",
        "GARAGE",
        "ARDENE",
        "UNIQLO",
        "SSENSE",
        # Électronique / Tech
        "BEST BUY", "BESTBUY", "BESTBUY.CA",
        "CANADA COMPUTERS",
        "NEWEGG",
        "APPLE STORE ONLINE",
        # Maison
        "WAYFAIR",
        "IKEA",
        "HOMESENSE", "WINNERS",
        # Sport
        "SPORT CHEK", "SPORTCHEK",
        "SAIL",
        "MEC", "MOUNTAIN EQUIPMENT CO-OP",
        "NIKE",
        "ADIDAS",
        # Paiement en ligne (indicateur)
        "PAYPAL",
        "SHOPIFY MERCHANT",
        "STRIPE",
        # Générique
        "ONLINE PURCHASE", "WEB ACHAT",
        "INTERNET ACHAT",
    ],
}

# Codes de ville canadiens apparaissant sur les relevés
_CITY_CODES = [
    "MTL", "MONTREAL", "LAVAL", "BROSSARD", "LONGUEUIL", "SAINT-LAURENT",
    "VERDUN", "ROSEMONT", "PLATEAU", "HOCHELAGA",
    "QUÉBEC", "QUEBEC CITY", "STE-FOY",
    "GATINEAU", "HULL",
    "TORONTO", "NORTH YORK", "SCARBOROUGH", "ETOBICOKE", "MISSISSAUGA",
    "BRAMPTON", "HAMILTON", "LONDON ON",
    "OTTAWA",
    "VANCOUVER", "BURNABY", "SURREY", "RICHMOND BC",
    "CALGARY", "EDMONTON",
    "WINNIPEG", "SASKATOON", "REGINA",
    "HALIFAX", "MONCTON",
]

_PROVINCES = ["QC", "ON", "BC", "AB", "MB", "SK", "NS", "NB"]


def augment(names: list, n: int = 6) -> list:
    """Génère des variations réalistes de noms de marchands (numéros de succursale, villes, etc.)."""
    result = list(names)
    for name in names:
        for _ in range(n):
            v = name
            # Numéro de succursale
            if random.random() > 0.45:
                v += f" #{random.randint(100, 9999)}"
            elif random.random() > 0.5:
                v += f" {random.randint(1000, 99999)}"
            # Code de ville
            if random.random() > 0.5:
                v += f" {random.choice(_CITY_CODES)}"
            # Province
            if random.random() > 0.65:
                v += f" {random.choice(_PROVINCES)}"
            result.append(v.strip())
    return result


def build_dataset():
    X, y = [], []
    for label, names in RAW_DATA.items():
        augmented = augment(names)
        for name in augmented:
            X.append(name.upper())
            y.append(label)
    return X, y


def train():
    print("Construction du jeu d'entraînement...")
    X, y = build_dataset()
    print(f"  {len(X)} exemples, {len(set(y))} catégories")

    model = Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                max_features=10_000,
                lowercase=True,
                sublinear_tf=True,
            )),
            ("char", TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 4),
                max_features=20_000,
                lowercase=True,
                sublinear_tf=True,
            )),
        ])),
        ("clf", LogisticRegression(
            C=3.0,
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            multi_class="multinomial",
            random_state=42,
        )),
    ])

    print("Validation croisée (5-fold)...")
    scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(f"  Précision moyenne : {scores.mean():.3f} ± {scores.std():.3f}")

    print("Entraînement final...")
    model.fit(X, y)

    out = "merchant_classifier.pkl"
    joblib.dump(model, out)
    print(f"Modèle sauvegardé → {out}")
    return model


if __name__ == "__main__":
    train()
