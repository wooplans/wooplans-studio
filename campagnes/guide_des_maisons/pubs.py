"""Pubs Facebook du « Guide WooPlans des maisons » (lead magnet payant, 1 900 FCFA).

Tout texte passe par wooplans.guardrails.check_copy (tests/test_guide_ads.py). Chiffres des exemples :
données publiques des fiches sur wooplans.com (vérifiées le 14 nov. 2026) ; à revérifier si une fiche change.
Rien n'est mis en ligne sans l'accord de Tao, qui relit et tourne lui-même les vidéos (face caméra, guide sur le téléphone).
Le livre imprimé (Catalogue Premium) n'apparaît JAMAIS dans ces pubs : il est réservé à la page de remerciement.
"""
from urllib.parse import urlencode

GUIDE_PRICE_FCFA = 1900
GUIDE_URL = "https://wooplans.com/guide-des-maisons"
ANNOUNCED_MODELS = 100
CTA_LINE = "Le guide est à 1 900 FCFA sur wooplans.com."

# Montants autorisés en plus du prix du catalogue (settings.OFFER_PRICE_FCFA).
ALLOWED_AMOUNTS = (GUIDE_PRICE_FCFA,)


def ad_link(angle: str) -> str:
    """Lien de destination d'une pub (UTM lisibles dans le tableau de bord du site)."""
    params = {"utm_source": "facebook", "utm_medium": "paid", "utm_campaign": "guide_maisons", "utm_content": angle}
    return f"{GUIDE_URL}?{urlencode(params)}"


# Scripts vidéo (9:16, 20 à 35 s). « plan » = ce que Tao montre à l'image.
VIDEOS = [
    {
        "id": "budget",
        "angle": "Budget",
        "hook": "Avec votre budget, quelle maison pouvez-vous vraiment construire ? J'ai fait la liste.",
        "script": [
            ("Tao face caméra, téléphone en main", "Avec votre budget, quelle maison pouvez-vous vraiment construire ? J'ai fait la liste."),
            ("Défilement du guide : page « Dans ce guide »", f"Dans ce guide, j'ai rangé {ANNOUNCED_MODELS} villas et duplex par budget de construction : moins de 15 millions, 15 à 25, 25 à 40, et au-dessus."),
            ("Zoom sur la fiche V3-027", "Par exemple, cette villa de 3 chambres : 69 mètres carrés, un terrain de 250 mètres carrés, et un budget estimé entre 9,9 et 12,1 millions."),
            ("Défilement rapide de plusieurs fiches", "Pour chaque maison : les chambres, la surface, le terrain qu'il faut et le budget estimé."),
            ("Tao face caméra", f"Vous allez directement à votre tranche de budget, et vous savez ce qui est à votre portée. {CTA_LINE}"),
        ],
        "on_screen": ["Quelle maison pour votre budget ?", f"{ANNOUNCED_MODELS} maisons classées par budget", "Guide PDF · 1 900 FCFA"],
    },
    {
        "id": "terrain",
        "angle": "Terrain",
        "hook": "Vous avez un terrain de 300 mètres carrés ? Voici ce que vous pouvez construire dessus.",
        "script": [
            ("Tao face caméra", "Vous avez un terrain de 300 mètres carrés ? Voici ce que vous pouvez construire dessus."),
            ("Défilement : tableau « Quel modèle pour mon terrain ? »", "Dans mon guide, il y a un tableau qui range toutes les maisons par taille de terrain, de 200 à 750 mètres carrés."),
            ("Zoom sur la fiche D4-002", "Sur 300 mètres carrés, vous pouvez même faire ce duplex de 4 chambres : 204 mètres carrés habitables."),
            ("Tao face caméra", "Avant de choisir une maison, vérifiez qu'elle tient sur votre terrain. Ce guide vous le dit en un coup d'œil."),
            ("Tao face caméra", CTA_LINE),
        ],
        "on_screen": ["Terrain de 300 m² ?", "Les maisons qui tiennent dessus", "Guide PDF · 1 900 FCFA"],
    },
    {
        "id": "telephone",
        "angle": "Guide sur le téléphone",
        "hook": f"J'ai mis {ANNOUNCED_MODELS} maisons dans ce guide, avec le budget de chacune.",
        "script": [
            ("Tao face caméra, il fait défiler le PDF sur son téléphone", f"J'ai mis {ANNOUNCED_MODELS} maisons dans ce guide, avec le budget de chacune."),
            ("Défilement continu des fiches, plein écran", "Des villas de plain-pied, des duplex, de 2 à 5 chambres. Pour chaque maison : la surface, le terrain qu'il faut et le budget de construction estimé."),
            ("Page « Les 5 décisions »", "Et au début, les 5 décisions à prendre avant de construire : le terrain, le budget réel, villa ou duplex, les chambres et le calendrier."),
            ("Tao face caméra", f"C'est un PDF, vous le lisez sur votre téléphone. {CTA_LINE}"),
        ],
        "on_screen": [f"{ANNOUNCED_MODELS} maisons + leur budget", "PDF sur votre téléphone", "1 900 FCFA · wooplans.com"],
    },
    {
        "id": "avant_architecte",
        "angle": "Avant l'architecte",
        "hook": "Avant de payer un architecte, faites ceci : choisissez votre modèle et connaissez votre budget.",
        "script": [
            ("Tao face caméra", "Avant de payer un architecte, faites ceci : choisissez votre modèle et connaissez votre budget."),
            ("Tao face caméra", "Beaucoup de gens arrivent chez l'architecte sans savoir ce qu'ils veulent ni ce que ça coûte. Ils perdent du temps et de l'argent."),
            ("Défilement du guide", f"Dans ce guide, vous comparez {ANNOUNCED_MODELS} maisons avec leur surface, leur terrain et leur budget estimé, et vous notez vos 3 favoris."),
            ("Tao face caméra", f"Vous arrivez avec une idée claire. {CTA_LINE}"),
        ],
        "on_screen": ["Avant l'architecte :", "1. Choisissez votre modèle", "2. Connaissez votre budget"],
    },
    {
        "id": "villa_duplex",
        "angle": "Villa ou duplex",
        "hook": "Même budget : une villa de 5 chambres ou un duplex de 4 chambres ? Regardez la différence.",
        "script": [
            ("Tao face caméra", "Même budget : une villa de 5 chambres ou un duplex de 4 chambres ? Regardez la différence."),
            ("Zoom sur la fiche V5-006", "Cette villa de plain-pied : 5 chambres, 253 mètres carrés, budget estimé entre 36,4 et 44,5 millions. Mais il lui faut un terrain de 600 mètres carrés."),
            ("Zoom sur la fiche D4-002", "Ce duplex : 4 chambres, 204 mètres carrés, budget estimé entre 39,7 et 48,5 millions. Et un terrain de 300 mètres carrés suffit."),
            ("Tao face caméra", f"Tout dépend de votre terrain. Dans le guide, vous voyez les deux côte à côte. {CTA_LINE}"),
        ],
        "on_screen": ["Villa ou duplex ?", "Même budget, terrain différent", "Guide PDF · 1 900 FCFA"],
    },
]

# Textes des pubs (Gestionnaire de publicités Meta) : texte principal, titre, description.
PRIMARY_TEXTS = [
    f"Quelle maison pouvez-vous construire avec votre budget ? 🏠\n\nLe Guide WooPlans des maisons réunit {ANNOUNCED_MODELS} villas et duplex, classés par budget de construction. Pour chacune : chambres, surface habitable, terrain conseillé et budget estimé.\n\n📱 PDF à lire sur votre téléphone · 1 900 FCFA · Mobile Money",
    f"Vous avez un terrain ? Avant de payer un architecte, choisissez votre modèle et connaissez votre budget.\n\nDans le guide : {ANNOUNCED_MODELS} maisons, le tableau « Quel modèle pour mon terrain ? » (de 200 à 750 m²) et les 5 décisions à prendre avant de construire.\n\n1 900 FCFA, reçu juste après le paiement.",
    f"Villa ou duplex ? Plain-pied ou étage ? 3, 4 ou 5 chambres ?\n\n{ANNOUNCED_MODELS} modèles avec leur budget de construction estimé, pour savoir en quelques minutes ce qui est à votre portée. Guide PDF à 1 900 FCFA.",
]
HEADLINES = [
    f"{ANNOUNCED_MODELS} maisons avec leur budget",
    "Quelle maison pour votre budget ?",
    "Le guide avant de construire",
]
DESCRIPTION = "Guide PDF · 1 900 FCFA · Mobile Money"


def all_texts():
    """Tous les textes destinés au public, pour les contrôles."""
    for v in VIDEOS:
        yield v["hook"]
        for _, line in v["script"]:
            yield line
        yield from v["on_screen"]
    yield from PRIMARY_TEXTS
    yield from HEADLINES
    yield DESCRIPTION
