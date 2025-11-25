import json
import os

USERS_FILE = "users.json"
DEALS_FILE = "deals.json"

def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def add_user(user_id):
    users = load_json(USERS_FILE, [])
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)

def get_users():
    return load_json(USERS_FILE, [])

def save_deal(deal_id):
    deals = load_json(DEALS_FILE, [])
    if deal_id not in deals:
        deals.append(deal_id)
        save_json(DEALS_FILE, deals)

def is_new_deal(deal_id):
    deals = load_json(DEALS_FILE, [])
    return deal_id not in deals
