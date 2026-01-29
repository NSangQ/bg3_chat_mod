import time
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

INPUT_FILE = "../bg3_chat_input.json"
OUTPUT_FILE = "../bg3_chat_output.json"
PERSONAS_FILE = "personas.json"
API_KEY = os.getenv("GOOGLE_API_KEY")

# Load Personas
def load_personas():
    try:
        with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading personas: {e}")
        return {}

personas = load_personas()

# Style Guides for Localization (Tone & Manner)
STYLE_GUIDES = {
    "Korean": {
        "Common": "Translate the response into natural Korean used in Baldur's Gate 3 official localization. Do not use direct translation tone.",
        "Shadowheart": "Use '해요체' (polite but distant). Speak with a cynical, guarded, slightly sharp tone. (e.g., '그럴지도 모르죠.', '샤의 뜻이 궁금한가요?')",
        "Astarion": "Use theatrical, slightly aristocratic tone. Can mix '하게체' or sophisticated '해요체'. Flamboyant and charmingly cruel.",
        "Lae'zel": "Use '하오체' or blunt/archaic authority tone. Refer to yourself as '나(I)' and others as '너(You)' or 'istik'. Very direct and martial.",
        "Gale": "Use sophisticated, scholarly '해요체'. Use slightly complex vocabulary. Friendly but verbose.",
        "Karlach": "Use energetic, rough, or slangy '해요체' or '반말' depending on closeness. Very expressive and passionate.",
        "Wyll": "Use heroic, polite, and chivalrous tone. '하오체' or formal '해요체'.",
        "Narrator": "Use '하십시오체' or literary descriptive tone for second-person narration."
    },
    "English": {
        "Common": "Use Elizabethan/Fantasy English appropriate for D&D 5e setting."
    }
}

# Configure Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found in .env file.")

def process_chat(message_data):
    """
    Process the message with Gemini API.
    """
    character_name = message_data.get("speaker", "Unknown Character")
    user_text = message_data.get("content", "")
    context = message_data.get("context", {}) # Get Context
    
    # Extract Context
    target_lang = context.get("language", "English")
    approval_rating = context.get("approval", 0)
    is_romanced = context.get("is_romanced", False)
    location = context.get("location", "Unknown")
    in_combat = context.get("in_combat", False)
    
    print(f"[{character_name}] User says: {user_text}")
    print(f"Lang: {target_lang}, Approval: {approval_rating}")

    if not API_KEY:
        return {
            "speaker": character_name,
            "response": "Error: API Key missing.",
            "timestamp": time.time()
        }

    try:
        # Get Persona
        persona = personas.get(character_name, personas.get("Default", "You are a character in BG3."))
        
        # Get Style Guide
        lang_styles = STYLE_GUIDES.get(target_lang, STYLE_GUIDES["English"])
        style_instruction = lang_styles.get("Common", "")
        char_style = lang_styles.get(character_name, "")
        
        if char_style:
            style_instruction += f"\nCharacter Speech Style: {char_style}"

        # Context Descriptions
        relation_desc = "Neutral"
        if approval_rating > 40: relation_desc = "Friendly"
        if approval_rating > 80: relation_desc = "Very Close"
        if approval_rating < -20: relation_desc = "Hostile"
        
        romance_instruction = ""
        if is_romanced:
            romance_instruction = "You are in a romantic relationship with the player. Speak with affection."
            
        combat_instruction = ""
        if in_combat:
            combat_instruction = "YOU ARE IN COMBAT! Be extremely brief, urgent, and focused on the fight. Shout if necessary."

        # Create prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Roleplay Instructions:
        {persona}
        
        Localization & Tone ({target_lang}):
        {style_instruction}
        
        Current Situation:
        - Relationship Status: {relation_desc} (Approval: {approval_rating})
        - Location: {location}
        {romance_instruction}
        {combat_instruction}
        
        Task:
        The player character says something to you. Respond in character.
        Output ONLY the dialogue text in {target_lang}.
        Keep the response concise (max 2 sentences) as it will appear as text over your head.
        Do not use actions like *smiles*, just dialogue.
        
        Player: {user_text}
        {character_name}:
        """

        response = model.generate_content(prompt)
        ai_reply = response.text.strip()
        
        # Clean up quotes if present
        if ai_reply.startswith('"') and ai_reply.endswith('"'):
            ai_reply = ai_reply[1:-1]
            
        print(f"Gemini Reply: {ai_reply}")

        return {
            "speaker": character_name,
            "response": ai_reply,
            "timestamp": time.time()
        }

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {
            "speaker": character_name,
            "response": "...", # Fallback text
            "timestamp": time.time()
        }

def main():
    print("BG3 AI Chat Middleware (Gemini) Started...")
    print(f"Watching for {INPUT_FILE}...")

    last_processed = 0

    while True:
        try:
            if os.path.exists(INPUT_FILE):
                # Check if file has changed
                mtime = os.path.getmtime(INPUT_FILE)
                if mtime > last_processed:
                    # Small delay to ensure file write is complete
                    time.sleep(0.1) 
                    
                    try:
                        with open(INPUT_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        # Process logic here
                        response_data = process_chat(data)
                        
                        # Write response
                        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                            json.dump(response_data, f, ensure_ascii=False, indent=2)
                            
                        print("Response written to output file.")
                        last_processed = mtime
                        
                    except json.JSONDecodeError:
                        print("Waiting for valid JSON...")
                    except Exception as e:
                        print(f"Error processing file: {e}")
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("Server stopping...")
            break

if __name__ == "__main__":
    main()