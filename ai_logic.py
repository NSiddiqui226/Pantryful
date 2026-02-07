# ai_logic.py
import google.generativeai as genai
import os
import json
import random
from dotenv import load_dotenv
from data_engine import (
    get_live_details,
    find_cheapest_store,
    find_best_alternative,
    find_category_substitute
)

# -----------------------------
# AI SETUP (SAFE ON IMPORT)
# -----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# CORE AI CURATION ENGINE
# -----------------------------
def generate_shopping_list(
    household_size,
    grocery_freq,
    stores,
    pantry_usuals
):
    """
    Uses AI to curate a shopping list, recipes, and upsells
    based on user behavior and pantry data.
    """

    # Flatten pantry items
    flat_items = []
    for category, items in pantry_usuals.items():
        for item in items:
            flat_items.append(f"{item} ({category})")

    # Mock store availability context
    store_context = {}
    for item in flat_items:
        store_context[item] = get_live_details(item.split(" (")[0], stores)

    # -----------------------------
    # MAXIMALLY CONTEXTUAL PROMPT
    # -----------------------------
    prompt = f"""
You are an expert culinary AI and grocery recommendation engine.

User profile:
- Household size: {household_size}
- Grocery shopping frequency: {grocery_freq} times per week
- Preferred stores: {", ".join(stores)}

User's usual pantry items (categorized):
{json.dumps(pantry_usuals, indent=2)}

Store availability data (mock, may be incomplete):
{json.dumps(store_context, indent=2)}

Your tasks:
1. Generate a **personalized shopping list** based on the user's pantry, household size, and shopping habits.
   - Include realistic quantities (units, weights, or volumes).
   - Include a short reason for each item.
2. Recommend 1–2 **upsell or complementary items**.
3. Generate **3 real, authentic recipes** that:
   - Use as many items as possible from the user's pantry and shopping list.
   - Have **real-world recipe names** (e.g., "Butter Chicken," "Spaghetti Aglio e Olio," "Fettuccine Alfredo").
   - Include **step-by-step cooking instructions** suitable for a home cook.
   - Only include recipes that are feasible given the user's pantry/shopping list.
   - Be diverse in cuisine/style if possible.

**Important instructions for output:**
- Output MUST be valid JSON with these keys: "shopping_list", "recipes", "upsell_suggestions".
- Each shopping list item: item, recommended_quantity, reason.
- Each recipe: name, instructions.
- Each upsell: item, why.
- DO NOT include explanations or markdown outside of JSON.
- DO NOT hardcode quantities—estimate based on household size and shopping frequency.

Example JSON format:
{{
  "shopping_list": [
    {{
      "item": "string",
      "recommended_quantity": "string",
      "reason": "string"
    }}
  ],
  "recipes": [
    {{
      "name": "string",
      "instructions": "string"
    }}
  ],
  "upsell_suggestions": [
    {{
      "item": "string",
      "why": "string"
    }}
  ]
}}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Safety: extract JSON even if model adds noise
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        parsed = json.loads(text[json_start:json_end])

        # Ensure all keys exist
        parsed.setdefault("shopping_list", [])
        parsed.setdefault("recipes", [])
        parsed.setdefault("upsell_suggestions", [])

        return parsed

    except Exception as e:
        # Fallback: generate minimal list based on actual pantry items
        fallback_list = []
        for category, items in pantry_usuals.items():
            for item in items:
                fallback_list.append({
                    "item": item,
                    "recommended_quantity": f"{max(1, household_size)} unit(s)",
                    "reason": f"Based on your usual {category.lower()} items"
                })

        # Fallback recipes: random selection
        pantry_items_flat = [item for items in pantry_usuals.values() for item in items]
        fallback_recipes = []
        for i in range(3):
            selected_items = random.sample(pantry_items_flat, min(2, len(pantry_items_flat)))
            fallback_recipes.append({
                "name": f"Quick Recipe {i+1}",
                "instructions": f"Use {', '.join(selected_items)} together to make a simple meal."
            })

        return {
            "shopping_list": fallback_list,
            "recipes": fallback_recipes,
            "upsell_suggestions": [],
            "error": str(e)
        }