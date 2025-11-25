import requests

STEAM_URL = "https://store.steampowered.com/api/featuredcategories/"

def get_steam_deals():
    deals = []
    try:
        r = requests.get(STEAM_URL).json()
        for game in r.get("specials", {}).get("items", []):
            deal_id = str(game["id"])
            title = game["name"]
            discount = game["discount_percent"]
            original_price = game.get("original_price", 0)/100
            final_price = game.get("final_price", 0)/100
            url = f"https://store.steampowered.com/app/{game['id']}"
            image = game.get("capsule_image", "")
            deals.append({
                "id": deal_id,
                "title": title,
                "discount": discount,
                "original_price": original_price,
                "final_price": final_price,
                "url": url,
                "image": image
            })
    except Exception as e:
        print("Steam parser error:", e)
    return deals
