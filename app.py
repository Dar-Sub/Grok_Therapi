from flask import Flask, request, jsonify, session, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
import re
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from dotenv import load_dotenv
import time
try:
    from googletrans import Translator
except ImportError:
    Translator = None

# Ensure consistent language detection with langdetect
DetectorFactory.seed = 0

# Initialize Translator (default to translating to English for processing)
translator_to_en = GoogleTranslator(source='auto', target='en')

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

limiter = Limiter(get_remote_address, app=app, default_limits=["800 per day", "10 per minute"])

USERS_FILE = "users.json"
HISTORY_FILE = "history.json"

for file in [USERS_FILE, HISTORY_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# Language code mapping for deep-translator compatibility
LANGUAGE_CODE_MAP = {
    'zh': 'zh-CN',  # Map 'zh' to 'zh-CN' (Simplified Chinese)
    'zh-Hant': 'zh-TW',  # Traditional Chinese
    'de': 'de',  # German
    'fr': 'fr',  # French
    # Add more mappings as needed
}

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        app.logger.error(f"Error loading {file}: {str(e)}")
        return {}

def save_json(file, data):
    try:
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
        app.logger.info(f"Successfully saved data to {file}")
    except Exception as e:
        app.logger.error(f"Error saving to {file}: {str(e)}")

def is_therapy_related(message):
    therapy_keywords = [
        "therapy", "therapist", "therapeutic", "counseling", "counselor", "psychotherapy",
        "mental health", "mental illness", "mental wellness", "psychologist", "psychiatrist",
        "psychiatric", "psychology", "wellbeing", "well-being", "emotional health", "emotional wellness",
        "depression", "depressed", "depressing", "anxiety", "anxious", "stress", "stressed", "trauma", "ptsd",
        "post-traumatic", "bipolar", "schizophrenia", "ocd", "obsessive-compulsive", "adhd", "attention deficit",
        "borderline", "bpd", "eating disorder", "anorexia", "bulimia", "binge eating", "panic disorder",
        "social anxiety", "generalized anxiety", "phobia", "insomnia", "sleep disorder", "mood disorder",
        "personality disorder", "dissociation", "derealization", "depersonalization", "hypomania", "mania",
        "psychosis", "delusion", "hallucination", "sad", "sadness", "anxious", "stressed", "overwhelmed",
        "angry", "anger", "frustrated", "lonely", "loneliness", "isolated", "isolation", "guilt", "guilty",
        "shame", "ashamed", "fear", "fearful", "scared", "worried", "not", "worry", "hopeless", "helpless", "despair",
        "grief", "grieving", "mourning", "loss", "jealous", "jealousy", "envy", "irritable", "irritation",
        "nervous", "tense", "restless", "empty", "numb", "feeling", "fine","hurt", "pain", "emotional pain", "heartbroken",
        "betrayed", "trust issues", "cbt", "cognitive behavioral therapy", "dbt", "dialectical behavior therapy",
        "emdr", "eye movement", "mindfulness", "meditation", "psychodynamic", "humanistic", "gestalt",
        "family therapy", "group therapy", "art therapy", "music therapy", "play therapy", "exposure therapy",
        "narrative therapy", "solution-focused", "acceptance and commitment", "act therapy", "behavioral therapy",
        "interpersonal therapy", "ipt", "trauma-focused", "somatic", "body-based", "grounding",
        "breathing exercises", "relaxation techniques", "coping", "self-care", "self-compassion", "self-love",
        "self-acceptance", "resilience", "self-esteem", "confidence", "motivation", "self-worth", "self-image",
        "body image", "journaling", "gratitude", "positive thinking", "affirmations", "visualization",
        "stress management", "time management", "problem-solving", "emotional regulation", "self-soothing",
        "distraction", "self-awareness", "self-reflection", "boundaries", "assertiveness", "communication skills",
        "conflict resolution", "sleep", "sleep hygiene", "diet", "nutrition", "exercise", "physical activity",
        "yoga", "fitness", "health", "healthy habits", "routine", "structure", "balance", "work-life balance",
        "hydration", "caffeine", "alcohol", "substance use", "smoking", "screen time", "social media",
        "digital detox", "relationship", "relationships", "family", "feelings", "family issues", "parenting", "marriage",
        "divorce", "breakup", "separation", "friendship", "friends", "social support", "support system",
        "community", "connection", "intimacy", "attachment", "codependency", "abandonment", "rejection",
        "bullying", "harassment", "abuse", "emotional abuse", "physical abuse", "sexual abuse", "neglect",
        "toxic relationship", "gaslighting", "manipulation", "trust", "betrayal", "infidelity", "cheating",
        "loneliness in relationships", "addiction", "substance abuse", "alcoholism", "drug use", "recovery",
        "sobriety", "relapse", "withdrawal", "detox", "rehab", "rehabilitation", "12-step", "aa", "na",
        "gambling", "pornography", "internet addiction", "gaming addiction", "shopping addiction", "overeating",
        "compulsion", "suicidal", "suicide", "self-harm", "cutting", "crisis", "emergency", "hotline", "helpline",
        "panic attack", "breakdown", "meltdown", "overdose", "danger", "safety plan", "urgent", "immediate help",
        "happiness", "joy", "peace", "calm", "relaxation", "contentment", "fulfillment", "purpose", "meaning",
        "hope", "optimism", "positivity", "growth", "personal growth", "self-improvement", "self-development",
        "healing", "closure", "forgiveness", "letting go", "acceptance", "inner peace", "balance", "harmony",
        "spirituality", "faith", "beliefs", "values", "identity", "self-discovery", "authenticity", "burnout",
        "work stress", "job stress", "career", "workplace", "productivity", "procrastination", "overwork",
        "job loss", "unemployment", "not feeling well", "performance anxiety", "imposter syndrome", "perfectionism",
        "life transition", "change", "adjustment", "midlife crisis", "quarter-life crisis", "aging", "retirement",
        "pregnancy", "postpartum", "menopause", "chronic illness", "disability", "caregiving", "loss of loved one",
        "moving", "relocation", "culture shock", "immigration", "acculturation", "identity crisis", "empathy",
        "compassion", "validation", "support", "encouragement", "motivation", "inspiration", "mental clarity",
        "focus", "concentration", "memory", "brain fog", "decision-making", "overthinking", "rumination",
        "intrusive thoughts", "flashbacks", "nightmares", "triggers", "trauma response", "fight or flight",
        "freeze response", "fawn response", "hypervigilance", "dissociative", "numbing",
        "emotional intelligence", "eq", "self-regulation", "social skills", "interpersonal skills"
    ]

    # Convert message to lowercase for case-insensitive matching
    message_lower = message.lower()

    # Check if any keyword is a substring of the message
    return any(keyword in message_lower for keyword in therapy_keywords)

def format_api_response(response_text):
    lines = response_text.split("\n")
    formatted_lines = []
    in_list = False
    step_counter = 0
    current_description = []

    for line in lines:
        line = line.strip()
        if not line:
            if in_list and current_description:
                formatted_lines.extend([f"   {desc}" for desc in current_description])
                current_description = []
            formatted_lines.append("")
            continue

        step_match_markdown = re.match(r"\*\*(.+?)\*\*", line)
        step_match_numbered = re.match(r"(\d+)\.\s*(.+)", line)

        if step_match_markdown or step_match_numbered:
            if in_list and current_description:
                formatted_lines.extend([f"   {desc}" for desc in current_description])
                current_description = []

            in_list = True
            step_counter += 1
            if step_match_markdown:
                step_title = step_match_markdown.group(1).strip()
            else:
                step_title = step_match_numbered.group(2).strip()
            formatted_lines.append(f"{step_counter}. {step_title}")
        else:
            if in_list:
                current_description.append(line)
            else:
                formatted_lines.append(line)

    if in_list and current_description:
        formatted_lines.extend([f"   {desc}" for desc in current_description])

    return "\n".join(formatted_lines)

@app.route("/")
def index():
    if "username" in session:
        return render_template("chat.html")
    return render_template("login.html")

@app.route("/signup", methods=["POST"])
@limiter.limit("5 per minute")
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    users = load_json(USERS_FILE)
    if username in users:
        return jsonify({"error": "User already exists"}), 400
    users[username] = generate_password_hash(password)
    save_json(USERS_FILE, users)
    return jsonify({"message": "Sign up successful"}), 201

@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    users = load_json(USERS_FILE)
    if username in users and check_password_hash(users[username], password):
        session["username"] = username
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out"}), 200

@app.route("/models", methods=["GET"])
def get_models():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
    available_models = ["grok", "grok-mini"]
    return jsonify({"models": available_models})

@app.route("/create_session", methods=["POST"])
@limiter.limit("10 per minute")
def create_session():
    if "username" not in session:
        app.logger.error("User not logged in for /create_session")
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    session_title = data.get("session_title")
    if not session_title:
        app.logger.error("Session title missing in /create_session")
        return jsonify({"error": "Session title required"}), 400

    history = load_json(HISTORY_FILE)
    app.logger.info(f"Loaded history in /create_session: {history}")
    user_history = history.get(session["username"], [])

    for entry in user_history:
        if entry.get("title") == session_title:
            app.logger.error(f"Session '{session_title}' already exists for user {session['username']}")
            return jsonify({"error": "Session title already exists"}), 400

    user_history.append({
        "title": session_title,
        "messages": []
    })
    history[session["username"]] = user_history
    app.logger.info(f"Updated history before saving in /create_session: {history}")
    save_json(HISTORY_FILE, history)

    return jsonify({"message": "Session created successfully"}), 200

@app.route("/chat", methods=["POST"])
@limiter.limit("50 per day")
def chat():
    if "username" not in session:
        app.logger.error("User not logged in")
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    message = data.get("message")
    session_title = data.get("session_title")
    model = data.get("model", "grok")
    app.logger.info(f"Received chat request: message='{message}', session_title='{session_title}', model='{model}'")
    if not message:
        app.logger.error("Empty message received")
        return jsonify({"error": "Empty message"}), 400
    if not session_title:
        app.logger.error("Session title missing")
        return jsonify({"error": "Session title required"}), 400

    # Step 1: Detect the language of the user's message using langdetect
    detected_lang = None
    # Preprocess the message: replace newlines and ensure it's not empty
    message_cleaned = message.replace("\n", " ").strip()
    if not message_cleaned:
        app.logger.error("Message is empty after preprocessing")
        return jsonify({"error": "Message cannot be empty"}), 400

    # Retry language detection up to 3 times
    for attempt in range(3):
        try:
            detected_lang = detect(message_cleaned)
            app.logger.info(f"Detected language (langdetect, attempt {attempt + 1}): {detected_lang}")
            # If the message contains English-like words, default to English
            if any(word.lower() in message_cleaned.lower() for word in ["i", "am", "feel", "not", "well", "depressed", "anxious"]):
                detected_lang = 'en'
                app.logger.info(f"Defaulting to English ('en') due to English-like words")
            break
        except Exception as e:
            app.logger.warning(f"langdetect attempt {attempt + 1} failed: {str(e)}")
            if attempt < 2:
                time.sleep(0.5)  # Wait 0.5 seconds before retrying
            else:
                app.logger.error("Language detection failed after 3 attempts")
                detected_lang = 'en'  # Default to English if detection fails

    # Map the detected language code to a deep-translator compatible code
    original_detected_lang = detected_lang
    detected_lang = LANGUAGE_CODE_MAP.get(detected_lang, detected_lang)
    app.logger.info(f"Mapped language: {original_detected_lang} -> {detected_lang}")

    # Step 2: Translate the message to English if it's not already in English
    message_en = message
    if detected_lang != 'en':
        # Try deep-translator first
        for attempt in range(3):  # Retry up to 3 times
            try:
                message_en = translator_to_en.translate(message)
                app.logger.info(f"Translated message to English (deep-translator): {message_en}")
                break
            except Exception as e:
                app.logger.warning(f"deep-translator to English failed (attempt {attempt + 1}/3): {str(e)}")
                if attempt < 2:
                    time.sleep(1)  # Wait 1 second before retrying
                else:
                    app.logger.error(f"deep-translator to English failed after 3 attempts: {str(e)}. Trying googletrans.")
                    # Fallback to googletrans if available
                    if Translator:
                        try:
                            google_translator = Translator()
                            translation = google_translator.translate(message, dest='en')
                            message_en = translation.text
                            app.logger.info(f"Translated message to English (googletrans): {message_en}")
                        except Exception as e:
                            app.logger.error(f"googletrans to English failed: {str(e)}")
                            return jsonify({"error": "Translation to English failed after multiple attempts. Please try again later."}), 500
                    else:
                        app.logger.error("googletrans not available")
                        return jsonify({"error": "Translation to English failed after multiple attempts. Please try again later."}), 500

    # Step 3: Check if the message is therapy-related (using the English translation)
    if not is_therapy_related(message_en):
        app.logger.info(f"Message '{message_en}' is not therapy-related")
        # Translate the rejection message back to the original language
        rejection_message_en = "I'm sorry, I can only answer questions related to therapy and mental health. Please ask a therapy-related question."
        if detected_lang != 'en':
            for attempt in range(3):  # Retry up to 3 times
                try:
                    translator_to_original = GoogleTranslator(source='en', target=detected_lang)
                    rejection_message = translator_to_original.translate(rejection_message_en)
                    app.logger.info(f"Translated rejection message to {detected_lang} (deep-translator): {rejection_message}")
                    break
                except Exception as e:
                    app.logger.warning(f"deep-translator of rejection message failed (attempt {attempt + 1}/3): {str(e)}")
                    if attempt < 2:
                        time.sleep(1)  # Wait 1 second before retrying
                    else:
                        app.logger.error(f"deep-translator of rejection message failed after 3 attempts: {str(e)}. Trying googletrans.")
                        if Translator:
                            try:
                                google_translator = Translator()
                                translation = google_translator.translate(rejection_message_en, dest=detected_lang)
                                rejection_message = translation.text
                                app.logger.info(f"Translated rejection message to {detected_lang} (googletrans): {rejection_message}")
                            except Exception as e:
                                app.logger.error(f"googletrans of rejection message failed: {str(e)}")
                                rejection_message = rejection_message_en
                                rejection_message += f"\n\n(Note: Translation to {detected_lang} failed, so the response is in English.)"
                        else:
                            app.logger.error("googletrans not available")
                            rejection_message = rejection_message_en
                            rejection_message += f"\n\n(Note: Translation to {detected_lang} failed, so the response is in English.)"
        else:
            rejection_message = rejection_message_en
        return jsonify({"response": rejection_message})

    # Step 4: Process the therapy-related message with the xAI API
    system_prompt = (
        "You are a professional therapy doctor specializing in mental health. "
        "Only answer questions related to therapy, mental health, emotional wellbeing, and related topics. "
        "If a question is not related to therapy, politely decline to answer and ask the user to ask a therapy-related question."
    )

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_en}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9
    }
    try:
        app.logger.info("Sending request to xAI API")
        response = requests.post(url, headers=headers, json=payload)
        app.logger.info(f"API response: {response.status_code} - {response.text}")
        if response.status_code != 200:
            return jsonify({"error": f"API error: {response.status_code} - {response.text}"}), 500
        reply_en = response.json()["choices"][0]["message"]["content"]
        app.logger.info(f"API reply (raw, English): {reply_en}")
        
        # Format the API response
        reply_en = format_api_response(reply_en)
        app.logger.info(f"API reply (formatted, English): {reply_en}")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request failed: {str(e)}")
        return jsonify({"error": "API request failed: {str(e)}"}), 500

    # Step 5: Translate the response back to the original language
    reply = reply_en
    if detected_lang != 'en':
        for attempt in range(3):  # Retry up to 3 times
            try:
                translator_to_original = GoogleTranslator(source='en', target=detected_lang)
                # Split the response into smaller chunks to avoid translation limits
                lines = reply_en.split("\n")
                translated_lines = []
                for line in lines:
                    if line.strip():
                        translated_line = translator_to_original.translate(line)
                        translated_lines.append(translated_line)
                    else:
                        translated_lines.append("")
                reply = "\n".join(translated_lines)
                app.logger.info(f"Translated response to {detected_lang} (deep-translator): {reply}")
                break
            except Exception as e:
                app.logger.warning(f"deep-translator of response failed (attempt {attempt + 1}/3): {str(e)}")
                if attempt < 2:
                    time.sleep(1)  # Wait 1 second before retrying
                else:
                    app.logger.error(f"deep-translator of response failed after 3 attempts: {str(e)}. Trying googletrans.")
                    if Translator:
                        try:
                            google_translator = Translator()
                            # Split the response into smaller chunks
                            lines = reply_en.split("\n")
                            translated_lines = []
                            for line in lines:
                                if line.strip():
                                    translation = google_translator.translate(line, dest=detected_lang)
                                    translated_lines.append(translation.text)
                                else:
                                    translated_lines.append("")
                            reply = "\n".join(translated_lines)
                            app.logger.info(f"Translated response to {detected_lang} (googletrans): {reply}")
                        except Exception as e:
                            app.logger.error(f"googletrans of response failed: {str(e)}")
                            reply = reply_en  # Fallback to English if translation fails
                            reply += f"\n\n(Note: Translation to {detected_lang} is not supported, so the response is in English. Please try another language or contact support.)"
                    else:
                        app.logger.error("googletrans not available")
                        reply = reply_en
                        reply += f"\n\n(Note: Translation to {detected_lang} is not supported, so the response is in English. Please try another language or contact support.)"

    # Step 6: Save the message and response in the history (store both original and English versions)
    history = load_json(HISTORY_FILE)
    app.logger.info(f"Loaded history: {history}")
    user_history = history.get(session["username"], [])
    session_index = -1
    for i, entry in enumerate(user_history):
        if entry.get("title") == session_title:
            session_index = i
            break

    if session_index == -1:
        user_history.append({
            "title": session_title,
            "messages": [{"user": message, "user_en": message_en, "grok": reply, "grok_en": reply_en}]
        })
        app.logger.info(f"Created new session: {session_title}")
    else:
        user_history[session_index]["messages"].append({
            "user": message,
            "user_en": message_en,
            "grok": reply,
            "grok_en": reply_en
        })
        app.logger.info(f"Appended to existing session: {session_title}")

    history[session["username"]] = user_history
    app.logger.info(f"Updated history before saving: {history}")
    save_json(HISTORY_FILE, history)

    return jsonify({"response": reply})

@app.route("/history", methods=["GET"])
def get_history():
    if "username" not in session:
        app.logger.error("User not logged in for /history")
        return jsonify({"error": "Not logged in"}), 401
    history = load_json(HISTORY_FILE)
    app.logger.info(f"Returning history for user {session['username']}: {history.get(session['username'], [])}")
    return jsonify(history.get(session['username'], []))

@app.route("/clear_history", methods=["POST"])
def clear_history():
    if "username" not in session:
        app.logger.error("User not logged in for /clear_history")
        return jsonify({"error": "Not logged in"}), 401
    history = load_json(HISTORY_FILE)
    history[session["username"]] = []
    save_json(HISTORY_FILE, history)
    app.logger.info(f"Cleared history for user {session['username']}")
    return jsonify({"message": "History cleared"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)))