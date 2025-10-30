import os
import datetime
import random
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# IMPORTANT: Put your Bot token into the environment variable BOT_TOKEN on your host (Render/GitHub secrets)
BOT_TOKEN = os.getenv("BOT_TOKEN")  # do NOT hardcode token here for security
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # optional: for better AI replies (not required)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set. Please set it before running the bot.")

# --- Simple language detection (English, Urdu - Perso-Arabic, Roman Urdu) ---
ENG_KEYWORDS = ["what", "why", "how", "when", "where", "who", "which", "whom", "is", "are", "do", "does", "can"]
URDU_WORDS = ["کیا", "کیسے", "کیوں", "کہاں", "کون", "کونسا", "ہے", "کرتا", "کریں"]
ROMAN_URDU = ["kya", "kaise", "kyun", "kahan", "kon", "kon sa", "hai", "karta", "karo", "ka"]

# Small built-in knowledge for common queries
def canned_answer(text, lang):
    t = text.lower()
    # time
    if any(word in t for word in ["time", "what time", "abhi", "kitne", "kitna"]):
        now = datetime.datetime.now().strftime("%I:%M %p")
        if lang == "urdu":
            return f"⏰ Abhi ka waqt hai: {now}"
        elif lang == "roman":
            return f"⏰ Abhi ka waqt hai: {now}"
        else:
            return f"⏰ Current time is: {now}"
    # date
    if any(word in t for word in ["date", "today", "aaj"]):
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        if lang in ("urdu","roman"):
            return f"📅 Aaj ki tareekh: {today}"
        else:
            return f"📅 Today's date: {today}"
    # joke
    if "joke" in t or "mazak" in t or "mazaak" in t or "mazaaq" in t:
        jokes = [
            "Why did the developer go broke? Because he used up all his cache! 😄",
            "Teacher: Why are you late? Student: There was a sign — SCHOOL AHEAD, GO SLOW! 😅",
            "Ek aadmi doctor ke paas gaya. Doctor: 'Aapko toh WhatsApp fever hai!' 😂"
        ]
        return random.choice(jokes)
    # greeting
    if any(w in t for w in ["salam","assalam","hello","hi","hey","سلام","ہیلو"]):
        if lang=="urdu":
            return "وعلیکم السلام! 😊 کیسے مدد کر سکتا ہوں؟"
        if lang=="roman":
            return "Waalaikumussalam! Kaise madad karoon?"
        return "Waalaikumussalam! How can I help you?"
    return None

# Optional: if OPENAI_API_KEY is provided we can query OpenAI for better replies.
# This code does not call OpenAI by default; it's an optional extension stub.
async def call_openai_stub(user_text, language):
    # This is a stub placeholder. If you set OPENAI_API_KEY you can replace this
    # function with real OpenAI API calls to fetch better responses.
    # For safety and offline usage this bot currently uses local heuristics.
    await asyncio.sleep(0.1)
    if language == "urdu":
        return "Yeh aik example AI jawab hai (OpenAI disabled)."
    if language == "roman":
        return "Yeh ek example AI jawab hai (OpenAI disabled)."
    return "This is an example AI-style reply (OpenAI disabled)."

def detect_language(text):
    lower = text.lower()
    # check Urdu script characters
    for ch in lower:
        if '\u0600' <= ch <= '\u06FF':
            return "urdu"
    # roman urdu check
    tokens = lower.split()
    roman_matches = sum(1 for t in tokens if any(r in t for r in ROMAN_URDU))
    eng_matches = sum(1 for t in tokens if any(e == t or t.startswith(e) for e in ENG_KEYWORDS))
    if roman_matches >= eng_matches and roman_matches>0:
        return "roman"
    if eng_matches > 0:
        return "english"
    # fallback: if message contains many non-ascii letters treat as urdu
    if any(ord(c) > 127 for c in text):
        return "urdu"
    return "english"

async def generate_reply(text):
    lang = detect_language(text)
    canned = canned_answer(text, lang)
    if canned:
        return canned
    # try OpenAI if enabled (stubbed here)
    if OPENAI_API_KEY:
        try:
            # Placeholder for real OpenAI call (not implemented here).
            return await call_openai_stub(text, lang)
        except Exception:
            pass
    # Fallback intelligent templates
    if lang == "urdu":
        return "معذرت، میں ابھی تک مکمل جواب فراہم نہیں کر سکتا — مگر میں آپ کی مدد کرنے کی پوری کوشش کروں گا۔ براہِ کرم سوال کو تھوڑا اور واضح کریں۔"
    if lang == "roman":
        return "Maaf kijiye, main abhi detailed jawab nahin de sakta — magar aap apna sawaal thoda aur wazeh likh dein."
    return "Sorry, I can't give a detailed answer right now. Please clarify your question or ask something specific."

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm your Auto-Reply Bot.\n"
        "I can answer in English, Urdu (فارسی/عربی script) and Roman Urdu.\n"
        "Just send any question and I'll try to reply.\n"
        "Commands: /help /info /weather <city>"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send any question in English, Urdu, or Roman Urdu.\n"
        "Examples:\n"
        " - 'What is Python?'\n"
        " - 'Aaj ka time kya hai?'\n"
        " - 'kitne baje hain'\n"
        "Use /weather <city> for quick weather (uses wttr.in)."
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Auto-Reply Bot — supports English, Urdu, and Roman Urdu replies. (Local heuristics)")

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import requests
    city = " ".join(context.args) if context.args else "Karachi"
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=10)
        await update.message.reply_text(f"🌦 {r.text}")
    except Exception:
        await update.message.reply_text("Weather info unavailable right now.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    text = update.message.text.strip()
    print(f"[MSG] from {user.id} ({user.first_name}): {text}")
    reply = await generate_reply(text)
    await update.message.reply_text(reply)
    # multimedia auto replies: quick sample
    if "photo" in text.lower() or "pic" in text.lower() or "تصویر" in text:
        await update.message.reply_photo(photo="https://picsum.photos/320/240", caption="Here's a random photo 📸")
    if "sticker" in text.lower() or "stkr" in text.lower():
        # a sample sticker id; you can change to valid sticker file id if you have one
        try:
            await update.message.reply_sticker(sticker="CAACAgIAAxkBAAEBH0Fj...")  # placeholder, may be invalid
        except Exception:
            pass

def main():
    print("Starting bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running. Press Ctrl+C to stop.")
    # Longer timeouts for unstable networks
    app.run_polling(stop_signals=None, poll_interval=5.0, timeout=30)

if __name__ == "__main__":
    main()
