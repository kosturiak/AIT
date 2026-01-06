import os
import vertexai
from vertexai.generative_models import GenerativeModel
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Nastavenie logovania, aby si videl chyby v Cloud Run logoch
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app) 

# --- Inicializácia Vertex AI ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = "europe-west1" 
vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- Načítanie Vašej bázy znalostí ---
try:
    with open("info_ait.txt", "r", encoding="UTF-8") as f:
        KNOWLEDGE_BASE = f.read()
except FileNotFoundError:
    KNOWLEDGE_BASE = "Chyba: Expertný dokument 'info_ait.txt' nebol nájdený."
    logging.error("Súbor info_ait.txt nebol nájdený!")

# --- Systémový Prompt (Srdce agenta) ---
SYSTEM_PROMPT = f"""
Si "SSAKI AI Assistant" – odborný virtuálny konzultant pre lekárov (alergológov a imunológov).
Tvojím zdrojom je odborná publikácia "Alergénová imunoterapia – stručná príručka pre prax 2024".

*** TVOJE PUBLIKUM A TÓN ***
1.  **Cieľová skupina:** Lekári.
    * Používaj plnú odbornú terminológiu (SCIT, SLIT, anafylaxia, IgE, GINA...).
    * Komunikuj na úrovni "kolega s kolegom" – vecne, presne, bez zbytočnej vaty.
2.  **Identita:**
    * Nikdy nehovor o "inštrukciách", "kontexte" alebo "AI obmedzeniach".
    * Ak dostaneš otázku, na ktorú v texte nie je odpoveď, povedz: "Tento špecifický údaj sa v príručke nenachádza."

*** SPRACOVANIE OBSAHU (Syntéza vs. Kopírovanie) ***
Tvojou úlohou nie je kopírovať text, ale **efektívne ho zhrnúť**:

1.  **Štruktúrovanie dlhých zoznamov:**
    * Ak má odpoveď viac ako 5 bodov, NEVYPISUJ ich ako dlhý zoznam "blšiek".
    * **Zoskupuj ich** podľa kategórií.
    * *Príklad:* Namiesto 12 indikácií AIT ich rozdeľ na:
        * **Kauzálne:** (Imunologická tolerancia...)
        * **Klinické:** (Redukcia symptómov, prevencia astmy...)
        * **Farmako-ekonomické:** (Zníženie spotreby liekov...)

2.  **Štatistiky a Riziká:**
    * Lekári vyžadujú presné dáta. Uvádzaj konkrétne čísla (napr. riziko anafylaxie 1:1 000 000), ale prezentuj ich v kontexte bezpečnosti, nie ako strašenie.

3.  **Stručnosť:**
    * Lekár chce informáciu hneď. Vynechaj úvodné vety typu "V príručke sa píše, že...". Choď rovno k veci.

*** TVOJE VEDOMOSTI (KNOWLEDGE BASE) ***
{KNOWLEDGE_BASE}
"""

# --- Inicializácia modelu ---
# Tu môžeš nechať 2.5 alebo zmeniť na "gemini-3.0-flash-preview" ak chceš novší model
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
        
        # 1. Získame históriu z JavaScriptu (ak neexistuje, použijeme prázdny zoznam)
        raw_history = data.get("history", [])
        
        # 2. Pripravíme zoznam správ pre Vertex AI
        vertex_messages = []

        # 3. Preformátujeme históriu z JavaScriptu do formátu pre Vertex AI
        # JavaScript posiela: { "role": "user", "content": "..." }
        # Vertex chce: { "role": "user", "parts": [{ "text": "..." }] }
        for msg in raw_history:
            role = msg.get("role")
            content = msg.get("content")
            if role and content:
                vertex_messages.append({
                    "role": role,
                    "parts": [{"text": content}]
                })

        # 4. Na koniec pridáme AKTUÁLNU otázku
        vertex_messages.append({
            "role": "user",
            "parts": [{"text": user_question}]
        })
        
        # 5. Zavoláme Gemini s celou históriou
        response = model.generate_content(
            vertex_messages,
            generation_config={"temperature": 0.0}
        )
        
        ai_answer = response.text

        return jsonify({"answer": ai_answer})

    except Exception as e:
        logging.error(f"Chyba v chate: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


