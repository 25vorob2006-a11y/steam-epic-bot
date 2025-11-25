import requests

EPIC_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"

def get_epic_free_games():
    deals = []
    try:
        r = requests.get(EPIC_URL).json()
        games = r["data"]["Catalog"]["searchStore"]["elements"]
        for game in games:
            promotions = game.get("promotions")
            if promotions and promotions.get("promotionalOffers"):
                for offer in promotions["promotionalOffers"]:
                    for promo in offer["promotionalOffers"]:
                        deal_id = game["id"]
                        title = game["title"]
                        url = f"https://www.epicgames.com/store/en-US/p/{game['productSlug']}"
                        image = game["keyImages"][0]["url"]
                        deals.append({
                            "id": deal_id,
                            "title": title,
                            "url": url,
                            "image": image
                        })
    except Exception as e:
        print("Epic parser error:", e)
    return deals
