import os
from dotenv import load_dotenv
from spoonacular import get_ingredient_price

# ✅ Load API key from .env
load_dotenv()

# ✅ Set your test case
ingredient = "chicken breast"

# ✅ Call the function
result = get_ingredient_price(ingredient)

print(f"Result for '{ingredient}':", result)
