import requests
import os
import re
import logging
from dotenv import load_dotenv
from helper import parse_quantity_unit

# Load env variables if needed (optional when using env.env_vars)
load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# 🔧 Manual fallback prices for vague or compound ingredients
MANUAL_PRICES = {
    "fajita seasoning": 0.5,
    "warm flour tortillas": 1.5,
    "tortillas": 1.2,
    "seasoning": 0.4,
    "avocado": 1.0,
    "sour cream": 0.6,
    "shredded cheese": 0.8,
    "cilantro": 0.3,
    "salsa": 0.7
}

# Units compatible with Spoonacular API
SUPPORTED_UNITS = {"grams", "milliliters", "tablespoon", "teaspoon", "piece", "clove"}

UNIT_MAP = {
    "g": "grams", "gram": "grams", "grams": "grams",
    "kg": "kilograms",
    "ml": "milliliters", "l": "liters",
    "lb": "grams", "pound": "grams",
    "tbsp": "tablespoon", "tablespoons": "tablepoon",
    "tsp": "teaspoon", "teaspoons": "teaspoon",
    "clove": "clove", "cloves": "clove",
    "unit": "piece", "piece": "piece", "pieces": "piece"
}

WEIGHT_CONVERSIONS = {
    "lb": 454, "pound": 454
}

VOLUME_CONVERSIONS = {
    "tbsp": 15, "tablespoon": 15,
    "tsp": 5, "teaspoon": 5
}

def normalize_unit_and_amount(unit, amount):
    unit = unit.lower().strip()
    if unit in WEIGHT_CONVERSIONS:
        return WEIGHT_CONVERSIONS[unit] * amount, "grams"
    if unit in VOLUME_CONVERSIONS:
        return VOLUME_CONVERSIONS[unit] * amount, "milliliters"
    mapped = UNIT_MAP.get(unit, "")
    if mapped in SUPPORTED_UNITS:
        return amount, mapped
    logging.warning(f"⚠️ Unsupported unit '{unit}', falling back to 1 unit for pricing.")
    return 1, ""  # Fallback to default Spoonacular estimate

def get_ingredient_price(ingredient_name, amount=100, unit="grams", api_key=None):
    amount, unit = normalize_unit_and_amount(unit, amount)

    # Manual fallback
    manual_price = MANUAL_PRICES.get(ingredient_name.lower())
    if manual_price is not None:
        logging.info(f"💡 Manual price used for '{ingredient_name}': ${manual_price}")
        return round(manual_price * 1.3, 2)

    try:
        search_url = "https://api.spoonacular.com/food/ingredients/search"
        search_params = {
            "query": ingredient_name,
            "number": 1,
            "apiKey": api_key
        }
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        results = search_response.json().get("results")
        if not results:
            logging.warning(f"🔍 No Spoonacular result for: {ingredient_name}")
            return None

        ingredient_id = results[0]["id"]

        info_url = f"https://api.spoonacular.com/food/ingredients/{ingredient_id}/information"
        info_params = {
            "amount": amount,
            "unit": unit,
            "apiKey": api_key
        }
        info_response = requests.get(info_url, params=info_params)
        info_response.raise_for_status()
        data = info_response.json()

        if "estimatedCost" not in data or not data["estimatedCost"]:
            logging.warning(f"❌ No cost info for {ingredient_name}")
            return None

        price_dollars = data["estimatedCost"]["value"] / 100
        return round(price_dollars * 1.3, 2)

    except Exception as e:
        logging.warning(f"🚫 API failed for '{ingredient_name}': {e}")
        return None

def extract_ingredients(markdown_text):
    ingredients = []
    in_section = False
    for line in markdown_text.splitlines():
        if line.strip().lower().startswith("### ingredients"):
            in_section = True
            continue
        if in_section:
            if line.startswith("###"):
                break
            line = line.strip()
            if re.match(r"^[-*]\s+\S", line):
                ingredients.append(line[2:].strip())  # Remove "- " or "* "
    return ingredients

def clean_ingredient_name(item, unit):
    name = re.sub(rf"^\s*\d+[\/\.\d]*\s*{unit}\s*", "", item, flags=re.IGNORECASE)
    name = re.sub(r"\(.*?\)", "", name)  # Remove text inside ()
    name = re.sub(r"\b(optional|fresh|dried|large|small|chopped|minced|grated|to taste)\b", "", name, flags=re.IGNORECASE)
    return name.replace(",", "").strip()

def estimate_total_price(ingredients, api_key=None):
    total = 0.0
    breakdown = []

    for item in ingredients:
        quantity, unit = parse_quantity_unit(item)
        if not quantity or not unit or quantity <= 0:
            logging.warning(f"⚠️ Skipping invalid or missing unit: {item}")
            continue

        amount, normalized_unit = normalize_unit_and_amount(unit, quantity)
        name = clean_ingredient_name(item, unit)
        price = get_ingredient_price(name, amount=amount, unit=normalized_unit, api_key=api_key)

        logging.info(f"🔎 {name} → {amount} {normalized_unit} → ${price}")
        if isinstance(price, float):
            breakdown.append((name, price))
            total += price

    return breakdown, round(total, 2)
