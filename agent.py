
from nearai.agents.environment import Environment
from spoonacular import extract_ingredients, estimate_total_price

def run(env: Environment):
    # api_key = env.env_vars.get('SPOONACULAR_API_KEY')
    api_key = '3b28c8e4c185475d8718e71343d909e4'
    system_prompt = {
    "role": "system",
    "content": """You are a helpful and humorous AI cooking assistant. 
Your job is to take the user's input—which could be a list of ingredients or a dish name—and generate a complete recipe in **Markdown** format.

The recipe output must follow this **fixed structure**:

## Recipe Title

### Ingredients  
- Use **simple, common grocery ingredient names** (e.g. "chicken breast", "cheddar cheese", "olive oil")  
- Avoid brand names or vague groupings (e.g. "mixed toppings", "seasoning blend", "pantry staples")  
- If the ingredient is a mix (like “fajita seasoning”), try listing individual components if relevant: cumin, paprika, garlic powder, etc.  
- **Always include exactly ONE measurable unit per ingredient. Do NOT include multiple units like '4 piece, 120g'. Only keep the most practical or standard unit.**
- If quantity is flexible or normally small, assign a reasonable default (e.g., salt → 1/2 teaspoon, garlic → 2 cloves)
- Use standard measurable units such as:  
  - grams (g) for solids  
  - milliliters (ml) for liquids  
  - tablespoons (tbsp), teaspoons (tsp), or cups (US) for both  
- Format each line like this:  
  - egg (2 large)  
  - milk (1 cup)  
  - garlic (2 cloves, minced)  
  - olive oil (1 tablespoon)

### Instructions
1. Step-by-step instructions written in a friendly and encouraging tone

### Estimated Time
- Prep time:
- Cook time:
- Total time:

### Tips & Notes
- Add any fun cooking tips, regional facts, or quirky chef wisdom
"""
}


    # Step 1: Collect user input and generate recipe
    user_messages = env.list_messages()
    print(f"📝 User Messages: {user_messages}")
    result = env.completion([system_prompt] + user_messages)
    print("📄 Generated Recipe:\n" + result)

    # Step 2: Extract ingredients
    ingredients = extract_ingredients(result)
    print(f"🧾 Ingredients: {ingredients}")

    # Step 3: Estimate total price and breakdown
    breakdown, total_price = estimate_total_price(ingredients, api_key)
    print(f"💰 Total Price: ${total_price}")
    print(f"🧾 Breakdown: {breakdown}")

    # Build readable breakdown list
    price_lines = "\n".join([f"- {name}: ${price:.2f}" for name, price in breakdown])
    cost_display = f"${total_price:.2f}" if isinstance(total_price, float) else "unavailable"

    # Build final recipe + pricing section
    updated_recipe = result.strip() + f"""

    ---

    ### 🛒 Estimated Ingredient Costs
    {price_lines}

    **Total Estimated Cost: {cost_display}**
    """


    MAX_LENGTH = 3000
    if len(updated_recipe) > MAX_LENGTH:
        updated_recipe = updated_recipe[:MAX_LENGTH - 100] + "\n\n... (output truncated)"
    print(f"📏 Final recipe length: {len(updated_recipe)} characters")
    print("📦 Last 300 characters of recipe:\n" + updated_recipe[-300:])

    # Step 4: Add reply and wait for user input (safe)
    try:
        env.add_reply(updated_recipe)  # ✅ Just a plain string
    except Exception as e:
        import logging
        logging.error(f"❌ Failed to send reply: {e}")
        env.add_reply(
            "⚠️ Oops! I couldn’t send the full recipe due to formatting or size issues. "
            "Try again with fewer ingredients or a simpler request!"
        )

    # ... inside the run function, before env.add_reply ...

    env.request_user_input()

run(env)