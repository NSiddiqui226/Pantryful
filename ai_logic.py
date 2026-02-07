import google.generativeai as genai

# 1. Setup
API_KEY = "AIzaSyAmJdoiPkyKYs6xDgnqLPpmpHqdv_h5cxU"
genai.configure(api_key=API_KEY)

# 2. Automated Model Picker (The 404 Killer)
# Instead of guessing the name, we ask the server what is available
print("Searching for available models...")
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # We prefer 1.5-flash, but we'll take whatever is first if flash is missing
    model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)
    print(f"✅ Connected to: {model_name}")
except Exception as e:
    print(f"⚠️ Search failed, falling back to default. Error: {e}")
    model = genai.GenerativeModel('gemini-1.5-flash')

print("\n--- 🤖 AUTO-PILOT PANTRY AI IS LIVE ---")
print("Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["quit", "exit", "bye"]:
        break

    try:
        # 3. Standard generate call
        response = model.generate_content(user_input)
        print(f"\nAI: {response.text}\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")