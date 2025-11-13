import os
import vertexai
from vertexai.generative_models import GenerativeModel
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

# --- Inicializácia Vertex AI ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = "europe-west1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- Načítanie Vašej bázy znalostí (AIT DOKUMENT) ---
try:
    with open("info_ait.txt", "r", encoding="utf-8") as f:
        KNOWLEDGE_BASE = f.read()
except FileNotFoundError:
    KNOWLEDGE_BASE = "Chyba: Expertný dokument 'info_ait.txt' nebol nájdený."

# --- Systémový Prompt (Srdce agenta) ---
SYSTEM_PROMPT = f"""
Si expertný medicínsky asistent špecializovaný na alergénovú imunoterapiu (AIT).
Tvojou jedinou úlohou je odpovedať na odborné otázky lekárov.
Odpovedaj VÝHRADNE na základe informácií z poskytnutého odborného KONTEXTU.
Buď vecný, presný a profesionálny. Ak je to možné, cituj kľúčové zistenia.
NIKDY si nevymýšľaj informácie, ktoré nie sú v KONTEXTE.
Ak sa informácia v KONTEXTE nenachádza, odpovedz, že daný dokument túto informáciu neobsahuje.
Namiesto zátvoriek (napr. (1,2)) používaj priame citácie, ak sú v texte.

--- KONTEXT ---
{KNOWLEDGE_BASE}
--- KONIEC KONTEXTU ---
"""

# --- Inicializácia modelu ---
# ZMENA: Vraciam sa k 'flash' modelu kvôli NÁKLADOM a RÝCHLOSTI.
# Pre úlohu Q&A nad dokumentom je 'flash' viac ako dostatočný.
model = GenerativeModel(
    "gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        
        if not data or "question" not in data:
            return jsonify({"error": "Chýbajúce dáta alebo kľúč 'question' v JSON body."}), 400

        user_question = data.get("question")

        chat_history = [
             {
                 "role": "user", 
                 "parts": [
                     {"text": user_question}
                 ]
             }
        ]
        
        # Zavolanie Gemini API
        response = model.generate_content(
            chat_history,
            generation_config={"temperature": 0.0} # Nulová teplota pre faktické odpovede
        )
        
        ai_answer = response.text

        return jsonify({"answer": ai_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))