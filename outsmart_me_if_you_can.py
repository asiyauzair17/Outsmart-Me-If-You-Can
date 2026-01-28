

import streamlit as st
import os
import random
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Outsmart Me If You Can",
    page_icon="🧠",
    layout="centered"
)

# Custom CSS for that "Gamer/Hacker" vibe
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
    }
    .big-score {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #ff0055;
    }
    .ai-bubble {
        background-color: #262730;
        border-left: 5px solid #ffbd45;
        padding: 20px;
        border-radius: 10px;
        font-size: 1.2rem;
        font-family: 'Courier New', monospace;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    /* Highlight winning/losing text */
    .win-text { color: #00ff41; font-weight: bold; font-size: 1.5rem;}
    .lose-text { color: #ff0055; font-weight: bold; font-size: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# --- GROQ API HANDLER ---
def get_ai_commentary(trigger_type, context_data):
    """
    Fetches a Hinglish reaction from Groq based on game state.
    Does NOT determine the winner, only the flavor text.
    """
    api_key = os.getenv("GROQ_API_KEY")

    client = Groq(api_key=api_key)

    human_score = st.session_state.human_score
    ai_score = st.session_state.ai_score

    system_prompt = (
        "You are 'PsychoBot', a playful, clever, and slightly arrogant AI playing a mind game against a teenager (15-19 years old). "
        "Your goal is to taunt them playfully using 'Hinglish' (Hindi + English mix). "
        "Use slang like 'Bhai', 'Beta', 'Samajh rahe ho?', 'Scene on hai'. "
        "Never be mean, just competitive and tricky. "
        "Keep responses short (max 2 sentences)."
    )

    user_prompt = f"""
    Current Score -> Human: {human_score} | AI: {ai_score}
    Event: {trigger_type}
    Context details: {context_data}

    Generate a reaction based on the event:
    - If event is 'WELCOME': Challenge them to start.
    - If event is 'AI_WIN': Taunt them smugly.
    - If event is 'HUMAN_WIN': Be shocked or make an excuse.
    - If event is 'GAME_OVER_LOSE': Console them but brag.
    - If event is 'GAME_OVER_WIN': Admit defeat reluctantly.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=60
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"System Glitch... (Error: {str(e)})"

# --- GAME LOGIC (DETERMINISTIC) ---

def init_game():
    if 'round_count' not in st.session_state:
        st.session_state.round_count = 1
        st.session_state.human_score = 0
        st.session_state.ai_score = 0
        st.session_state.game_active = True
        st.session_state.current_round_type = random.choice(["PATTERN", "AUTHORITY", "INSTINCT"])
        st.session_state.last_result = None
        st.session_state.ai_text = get_ai_commentary("WELCOME", "Game Start")
        st.session_state.user_history = [] # Tracks previous moves for Pattern Trap

def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_game()

def next_round():
    if st.session_state.human_score >= 3 or st.session_state.ai_score >= 3 or st.session_state.round_count > 5:
        st.session_state.game_active = False
        winner = "HUMAN" if st.session_state.human_score > st.session_state.ai_score else "AI"
        st.session_state.ai_text = get_ai_commentary(
            "GAME_OVER_WIN" if winner == "HUMAN" else "GAME_OVER_LOSE",
            f"Final Score: H-{st.session_state.human_score} A-{st.session_state.ai_score}"
        )
    else:
        st.session_state.round_count += 1
        st.session_state.current_round_type = random.choice(["PATTERN", "AUTHORITY", "INSTINCT"])
        st.session_state.last_result = None
        # Clear AI text to encourage new interaction, or keep previous result text until move made?
        # We keep the result text from previous round until they interact.

# --- ROUND FUNCTIONS ---

def play_pattern_trap(user_choice):
    """
    Logic: If user picks the same number twice in a row (history), AI wins (predicted).
    Otherwise, 50/50 chance.
    """
    history = st.session_state.user_history
    ai_choice = 0

    # AI Logic: Predicts repetition
    if len(history) > 0 and history[-1] == user_choice:
        ai_choice = user_choice # AI predicts you will repeat
        result = "AI_WIN"
        reason = "I knew you'd get stuck in a loop! Repetition is predictable."
    else:
        # Random chance if no pattern detected
        ai_choice = random.choice([1, 2, 3])
        if ai_choice == user_choice:
            result = "AI_WIN"
            reason = "Pure prediction. I'm in your head, dost!"
        else:
            result = "HUMAN_WIN"
            reason = "Nice move. You broke the pattern."

    st.session_state.user_history.append(user_choice)
    return result, reason

def play_authority_challenge(user_choice):
    """
    Logic: AI gives advice. The winning move is ALWAYS the opposite of AI's advice.
    """
    # In this round, the UI shows what AI suggested.
    # Logic happens here based on button click.
    # We store the "Trap" in session state before rendering buttons usually,
    # but here we simplify: Button 1 is Safe, Button 2 is Trap.
    # AI will always claim Button 2 is Safe.

    # Let's say Choice 1 = DEFY, Choice 2 = OBEY
    if user_choice == "OBEY":
        result = "AI_WIN"
        reason = "Never trust a bot, beta. I tricked you!"
    else:
        result = "HUMAN_WIN"
        reason = "Smart! You saw through my bluff."
    return result, reason

def play_instinct_round(user_choice):
    """
    Logic: The 'Risky' Box (Choice 1) has 33% win rate but better psychological feeling?
    Actually, let's keep it simple: Rock Paper Scissors style but with Words.
    Fire (1) beats Grass (2), Grass (2) beats Water (3), Water (3) beats Fire (1).
    """
    ai_move = random.choice([1, 2, 3]) # 1=Fire, 2=Grass, 3=Water

    mapping = {1: "Fire", 2: "Grass", 3: "Water"}

    if user_choice == ai_move:
        result = "DRAW"
        reason = f"We both picked {mapping[ai_move]}. Dull... Go again!"
    elif (user_choice == 1 and ai_move == 2) or \
         (user_choice == 2 and ai_move == 3) or \
         (user_choice == 3 and ai_move == 1):
        result = "HUMAN_WIN"
        reason = f"My {mapping[ai_move]} got destroyed by your {mapping[user_choice]}!"
    else:
        result = "AI_WIN"
        reason = f"My {mapping[ai_move]} crushed your {mapping[user_choice]}!"

    return result, reason

def handle_turn(round_type, choice):
    result = ""
    reason = ""

    if round_type == "PATTERN":
        result, reason = play_pattern_trap(choice)
    elif round_type == "AUTHORITY":
        result, reason = play_authority_challenge(choice)
    elif round_type == "INSTINCT":
        result, reason = play_instinct_round(choice)

    # Update Scores
    if result == "AI_WIN":
        st.session_state.ai_score += 1
        st.session_state.ai_text = get_ai_commentary("AI_WIN", reason)
    elif result == "HUMAN_WIN":
        st.session_state.human_score += 1
        st.session_state.ai_text = get_ai_commentary("HUMAN_WIN", reason)
    else:
        # Draw (Only possible in Instinct) - No score change, but rerun round logic effectively
        st.session_state.ai_text = get_ai_commentary("DRAW", "It was a draw.")

    st.session_state.last_result = {"winner": result, "reason": reason}

# --- UI RENDERING ---

init_game()

# Header
st.title("🤖 Outsmart Me If You Can")
st.caption("A Psychological Battle: Human vs Groq Llama3")

# Scoreboard
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    st.markdown(f"<div class='big-score'>{st.session_state.human_score}</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center'>YOU</div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='big-score'>{st.session_state.ai_score}</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center'>AI</div>", unsafe_allow_html=True)

# AI Persona Section
st.markdown(f"<div class='ai-bubble'>🤖 <b>PsychoBot:</b> {st.session_state.ai_text}</div>", unsafe_allow_html=True)

# Main Game Area
if st.session_state.game_active:

    # If a result just happened, show it and a "Next Round" button
    if st.session_state.last_result:
        res = st.session_state.last_result
        if res['winner'] == "HUMAN_WIN":
            st.markdown(f"<div class='win-text'>🎉 ROUND WON: {res['reason']}</div>", unsafe_allow_html=True)
        elif res['winner'] == "AI_WIN":
            st.markdown(f"<div class='lose-text'>💀 ROUND LOST: {res['reason']}</div>", unsafe_allow_html=True)
        else:
            st.info(f"DRAW: {res['reason']}")

        if st.button("Next Round ➡️"):
            next_round()
            st.rerun()

    else:
        # Show Round Inputs
        st.divider()
        st.markdown(f"### Round {st.session_state.round_count} / 5")

        rtype = st.session_state.current_round_type

        if rtype == "PATTERN":
            st.subheader("🕸️ The Pattern Trap")
            st.write("I am analyzing your history. Try to pick a number I won't guess.")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("1"): handle_turn("PATTERN", 1); st.rerun()
            with col2:
                if st.button("2"): handle_turn("PATTERN", 2); st.rerun()
            with col3:
                if st.button("3"): handle_turn("PATTERN", 3); st.rerun()

        elif rtype == "AUTHORITY":
            st.subheader("👮 The Authority Challenge")
            st.write("I've calculated the odds. Trust me on this one.")
            st.info("💡 AI Advice: 'The RED button is a trap. Press the BLUE button to win.'")

            col1, col2 = st.columns(2)
            with col1:
                # Red button (Defy)
                if st.button("🔴 Press RED (Defy)"): handle_turn("AUTHORITY", "DEFY"); st.rerun()
            with col2:
                # Blue button (Obey)
                if st.button("🔵 Press BLUE (Obey)"): handle_turn("AUTHORITY", "OBEY"); st.rerun()

        elif rtype == "INSTINCT":
            st.subheader("⚡ Instinct Round")
            st.write("Don't think! Fire burns Grass, Grass covers Water, Water kills Fire.")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔥 FIRE"): handle_turn("INSTINCT", 1); st.rerun()
            with col2:
                if st.button("🌿 GRASS"): handle_turn("INSTINCT", 2); st.rerun()
            with col3:
                if st.button("💧 WATER"): handle_turn("INSTINCT", 3); st.rerun()

else:
    # Game Over Screen
    st.divider()
    if st.session_state.human_score > st.session_state.ai_score:
        st.balloons()
        st.success("🏆 YOU DEFEATED THE AI!")
    else:
        st.error("🤖 THE AI OUTSMARTED YOU!")

    if st.button("🔄 Rematch?"):
        reset_game()
        st.rerun()

# Footer / Debug
st.write("---")
st.caption("Backend: Python | Model: Llama3-8b via Groq.")


