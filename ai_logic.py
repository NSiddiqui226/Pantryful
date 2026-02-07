import google.generativeai as genai
import os
from dotenv import load_dotenv
from data_engine import get_live_details, find_best_alternative

# -----------------------------
# AI SETUP (SAFE ON IMPORT)
# -----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# CORE LOGIC FUNCTION (USED BY STREAMLIT)
# -----------------------------
def analyze_pantry(household_size, stores):
    daily_usage = household_size * 0.5
    days_left = max(1, int(10 / daily_usage))

    live_data = get_live_details("Oat Milk", stores)
    in_stock = any(v["stock"] > 0 for v in live_data.values())

    if not in_stock:
        alt = find_best_alternative("Oat Milk", stores)
        recommendation = (
            f"🚨 ALERT: Oat Milk is unavailable at your stores. "
            f"Available at {alt['store']} for ${alt['price']}."
            if alt else
            "🚨 ALERT: Oat Milk is unavailable nearby."
        )
        status = "Out of Stock"
    else:
        recommendation = "✅ You have enough oat milk for now."
        status = "In Stock"

    return {
        "days_left": days_left,
        "status": status,
        "recommendation": recommendation,
        "ai_tip": "Use smoothies or overnight oats to stretch your supply."
    }

# -----------------------------
# CLI MODE (ONLY RUNS IF DIRECTLY EXECUTED)
# -----------------------------
if __name__ == "__main__":
    print("\n--- 🤖 AUTO-PILOT PANTRY AI IS LIVE ---")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            break

        try:
            response = model.generate_content(user_input)
            print(f"\nAI: {response.text}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}")

def generate_shopping_list(household_size, stores):
    """
    Returns a simulated shopping list and recipe suggestions
    """
    # Simulate items running low based on household size
    shopping_list = [
        {"name": "Oat Milk", "quantity": max(1, household_size)},
        {"name": "Eggs", "quantity": max(6, household_size * 2)},
        {"name": "Apples", "quantity": max(4, household_size * 2)},
        {"name": "Bread", "quantity": 2}
    ]

    # Simulated recipes based on pantry
    recipes = [
        {"name": "Pancakes", "instructions": "Use eggs, milk, flour. Fry on skillet."},
        {"name": "Fruit Salad", "instructions": "Chop apples, mix with other fruits."},
        {"name": "Omelette", "instructions": "Use eggs and vegetables in fridge."}
    ]

    return {"shopping_list": shopping_list, "recipes": recipes}