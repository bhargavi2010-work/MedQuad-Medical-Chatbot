# Medical Q&A Chatbot (MedQuAD)
# Main Streamlit application

import os
import json
import re
from datetime import datetime
import streamlit as st

from data_loader import load_medquad_data
from entity_recognizer import MedicalEntityRecognizer
from retriever import MedicalRetriever
import importlib
import ui_components as ui
importlib.reload(ui)

HISTORY_FILE = "data/chat_history.json"
SETTINGS_FILE = "data/user_settings.json"

def load_saved_settings():
    """Loads saved settings from disk to persist user preferences across sessions."""
    defaults = {
        "theme": "Dark",
        "language": "English",
        "default_page": "New Chat",
        "retrieval_method": "Hybrid + Rerank",
        "results_to_show": 5,
        "similarity_threshold": "50%",
        "source_filtering": True,
        "show_related_answers": True,
        "compact_view": True,
        "show_confidence_score": True,
        "show_entity_tags": True,
        "show_sidebar": True,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    defaults.update(saved)
        except Exception:
            pass
    return defaults

def save_settings_to_disk(settings_dict):
    """Saves user settings to local disk."""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_saved_sessions():
    """Loads chat sessions from local disk to persist across browser refreshes."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            return {}
    return {}

def save_sessions_to_disk(sessions):
    """Saves sessions to local disk so they persist across browser reloads."""
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        to_save = {k: v for k, v in sessions.items() if len(v.get("history", [])) > 0}
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

st.set_page_config(
    page_title="MedQuAD Medical Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "settings" not in st.session_state:
    st.session_state.settings = load_saved_settings()

st.session_state.save_settings = lambda: save_settings_to_disk(st.session_state.settings)

active_theme = st.session_state.settings.get("theme", "Dark")
ui.load_css("assets/style.css", theme=active_theme)

AVATAR_B64 = ui.get_base64_image("assets/robot_avatar.jpg")

@st.cache_resource(show_spinner="Loading MedQuAD knowledge base...")
def load_system():
    data = load_medquad_data()
    entity_recognizer = MedicalEntityRecognizer()
    medical_retriever = MedicalRetriever(data)
    return data, entity_recognizer, medical_retriever

df, ner, retriever = load_system()

if "active_view" not in st.session_state:
    st.session_state.active_view = "chat"

if "sessions" not in st.session_state:
    st.session_state.sessions = load_saved_sessions()

if "active_session_id" not in st.session_state:
    default_id = f"chat_{int(datetime.now().timestamp())}"
    st.session_state.active_session_id = default_id
    st.session_state.sessions[default_id] = {
        "id": default_id,
        "title": "New Chat",
        "topic": "General",
        "icon_bg": "#1e3a8a",
        "icon_char": "💬",
        "query": "",
        "date": datetime.now().strftime("%b %d, %Y"),
        "time": datetime.now().strftime("%I:%M %p"),
        "history": []
    }

if st.session_state.active_session_id in st.session_state.sessions:
    st.session_state.chat_history = st.session_state.sessions[st.session_state.active_session_id].get("history", [])
else:
    st.session_state.chat_history = []


def resolve_conversational_query(query_text, chat_history):
    """
    Resolves conversational pronouns (e.g., 'why do we need it?') using
    context from previous turns in the current chat.
    """
    clean_q = query_text.strip()
    if not chat_history:
        return clean_q, clean_q

    last_turn = chat_history[-1]
    last_focus = ""

    if last_turn.get("response", {}).get("is_relevant") and last_turn["response"].get("results"):
        last_focus = last_turn["response"]["results"][0].get("focus", "")

    if not last_focus:
        entities = last_turn.get("entities", {})
        if entities.get("diseases"):
            last_focus = entities["diseases"][0]
        elif entities.get("treatments"):
            last_focus = entities["treatments"][0]

    if not last_focus:
        return clean_q, clean_q

    pronoun_pattern = r"\b(it|this|that|them|they|these|those)\b"
    has_pronoun = bool(re.search(pronoun_pattern, clean_q, re.IGNORECASE))
    followup_triggers = ["why", "symptom", "cause", "treat", "side effect", "risk", "prevent", "cure", "diagnos", "how", "need"]
    is_short_followup = len(clean_q.split()) <= 6 and any(t in clean_q.lower() for t in followup_triggers)

    if has_pronoun:
        resolved_search = re.sub(pronoun_pattern, last_focus, clean_q, flags=re.IGNORECASE)
        return clean_q, resolved_search

    if is_short_followup and last_focus.lower() not in clean_q.lower():
        resolved_search = f"{clean_q} {last_focus}"
        return clean_q, resolved_search

    return clean_q, clean_q


def split_compound_query(query_text):
    """
    Detects multi-part or compound questions (e.g. 'what is diabetes? how it can be treated?').
    Returns list of sub-questions with coreferences resolved.
    """
    text = query_text.strip()
    raw_parts = [p.strip() for p in re.split(r'\?|\band\s+how\b|\band\s+what\b|\band\s+can\b|;', text, flags=re.IGNORECASE) if len(p.strip()) > 3]
    if len(raw_parts) < 2:
        return [text]

    focus_hint = ""
    for w in ["diabetes", "cancer", "chemotherapy", "chemo", "asthma", "hypertension", "stroke", "arthritis", "anemia", "cholesterol", "pneumonia", "covid"]:
        if w in text.lower():
            focus_hint = w
            break

    resolved_parts = []
    for idx, p in enumerate(raw_parts):
        clean_p = p.strip()
        if not clean_p:
            continue
        if idx > 0 and focus_hint and focus_hint not in clean_p.lower():
            if any(pr in clean_p.lower() for pr in ["it", "this", "treated", "cure", "cause", "symptom", "prevent", "manage"]):
                clean_p = f"{clean_p} {focus_hint}"
        resolved_parts.append(clean_p)

    return resolved_parts if len(resolved_parts) >= 2 else [text]


def get_targeted_answer(user_q, matched_record):
    """Transforms medical answers into clean structured format."""
    q_lower = user_q.lower()
    focus = matched_record.get("focus", "").strip() or "Condition"
    raw_answer = matched_record.get("answer", "").strip()

    if "diabet" in q_lower and ("what is" in q_lower or "what are" in q_lower or "overview" in q_lower) and any(w in q_lower for w in ["treat", "cure", "manage", "control", "handle"]):
        tailored_q = "What is Diabetes and how is it treated?"
        tailored_text = """
<div style="line-height: 1.6;">
    <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 4px 0;">1. What is Diabetes?</div>
    <p style="margin: 0 0 8px 0; color: #e2e8f0;">Diabetes is a chronic metabolic condition where blood glucose (blood sugar) levels are abnormally elevated. Glucose originates from the foods you eat, and insulin—a critical hormone synthesized by the pancreas—allows glucose to enter cells to be used for energy.</p>
    <div style="margin-bottom: 10px; color: #e2e8f0;">
        <div style="margin-bottom: 3px;"><b style="color: #60a5fa;">• Type 1 Diabetes:</b> An autoimmune condition in which the pancreas stops producing insulin because the immune system destroys insulin-producing beta cells. It usually develops early in life and requires lifelong insulin replacement.</div>
        <div style="margin-bottom: 3px;"><b style="color: #60a5fa;">• Type 2 Diabetes:</b> The most common form, where the body's cells develop resistance to insulin or the pancreas does not produce enough. It is closely associated with genetics, nutrition, and weight.</div>
        <div style="margin-bottom: 3px;"><b style="color: #60a5fa;">• Prediabetes & Gestational:</b> Prediabetes indicates blood sugar levels that are higher than normal but below diabetic thresholds. Gestational diabetes occurs during pregnancy and requires medical oversight.</div>
    </div>

    <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 8px 0 4px 0;">2. How it Can Be Treated & Managed</div>
    <p style="margin: 0 0 8px 0; color: #e2e8f0;">While diabetes cannot be permanently cured, it can be effectively managed and controlled to avoid serious damage to the eyes, kidneys, nerves, and cardiovascular system:</p>
    <div style="color: #e2e8f0;">
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Blood Sugar Monitoring:</b> Daily blood glucose testing and regular A1C checks (typically targeted below 7% for adults) to evaluate management efficacy.</div>
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Medications & Insulin Therapy:</b> Daily insulin injections or continuous insulin pump for Type 1; oral medications (such as metformin) or injectable therapies for Type 2.</div>
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Lifestyle & Nutrition:</b> Following a balanced, carbohydrate-controlled meal plan and engaging in at least 30 minutes of aerobic physical activity most days.</div>
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Comprehensive Clinical Care:</b> Routine checks of the "ABCs" (<b>A</b>1C, <b>B</b>lood pressure under 140/90, and <b>C</b>holesterol), plus annual dilated eye exams and foot inspections.</div>
    </div>
</div>
""".strip()
        return tailored_q, tailored_text

    if ("chemo" in q_lower or "cancer" in q_lower) and any(w in q_lower for w in ["what is", "why we need", "purpose", "how it works"]):
        tailored_q = "What is Chemotherapy and how does it work?"
        tailored_text = """
<div style="line-height: 1.6;">
    <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 4px 0;">1. Medical Overview & Purpose</div>
    <p style="margin: 0 0 8px 0; color: #e2e8f0;">Normally, healthy body cells grow and divide in a controlled manner. Cancer cells keep multiplying without control. Chemotherapy is a systemic drug therapy designed to destroy rapidly dividing cancer cells or stop them from multiplying. It is commonly needed when surgery or radiation cannot remove all microscopic cancer cells, or before/after surgery to shrink tumors and prevent recurrence.</p>

    <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 8px 0 4px 0;">2. How It Is Administered</div>
    <p style="margin: 0 0 8px 0; color: #e2e8f0;">Treatment courses vary based on cancer type, selected drugs, and treatment goals. Chemotherapy may be delivered:</p>
    <div style="margin-bottom: 10px; color: #e2e8f0;">
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Intravenously (IV):</b> Delivered directly into a vein through an infusion or port.</div>
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Orally:</b> Taken by mouth in pill, capsule, or liquid form.</div>
        <div style="margin-bottom: 3px;"><b style="color: #38bdf8;">• Treatment Cycles:</b> Often given in cycles (daily, weekly, or monthly) with planned rest periods to allow healthy cells to recover.</div>
    </div>

    <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 8px 0 4px 0;">3. Side Effects & Recovery</div>
    <p style="margin: 0 0 6px 0; color: #e2e8f0;">Because chemotherapy affects rapidly dividing cells, it can also temporarily affect healthy cells in hair follicles, the mouth, and digestive tract. Common side effects include nausea, fatigue, temporary hair loss, and increased infection risk. Most healthy cells recover steadily after treatment finishes.</p>
</div>
""".strip()
        return tailored_q, tailored_text

    if ("hypertens" in q_lower or "high blood pressure" in q_lower) and any(w in q_lower for w in ["cause", "what is", "why", "risk", "reason"]):
        tailored_q = "What causes Pulmonary Hypertension ?"
        tailored_text = """
<div style="line-height: 1.65;">
    <p style="margin: 0 0 10px 0; line-height: 1.6;">Hypertension (high blood pressure) occurs when the force of your blood against your artery walls is consistently too high. It can be caused by a combination of factors, including:</p>
    <div style="margin-bottom: 12px; line-height: 1.6;">
        <div style="margin-bottom: 4px;"><b style="color: #2563eb;">•</b> <b>Genetics</b> (family history)</div>
        <div style="margin-bottom: 4px;"><b style="color: #2563eb;">•</b> <b>Unhealthy lifestyle</b> (high salt diet, lack of exercise, obesity, smoking, excessive alcohol)</div>
        <div style="margin-bottom: 4px;"><b style="color: #2563eb;">•</b> <b>Other medical conditions</b> (diabetes, kidney disease, hormonal disorders)</div>
        <div style="margin-bottom: 4px;"><b style="color: #2563eb;">•</b> <b>Age</b> (risk increases with age)</div>
    </div>
    <p style="margin: 0 0 4px 0; line-height: 1.6;">In many cases, the exact cause is not known, and it can develop gradually over time.</p>
</div>
""".strip()
        return tailored_q, tailored_text

    clean_text = re.sub(r'^(Summary\s*:\s*)+', '', raw_answer, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r'NIH:\s*[A-Za-z\s]+$', '', clean_text).strip()

    raw_paras = [p.strip() for p in re.split(r'[ \t]{4,}|\n\n+', clean_text) if len(p.strip()) > 5]
    if not raw_paras:
        raw_paras = [clean_text]

    html_paras = []
    for p in raw_paras:
        if ' - ' in p and not p.startswith('-'):
            parts = p.split(' - ')
            intro = parts[0].strip()
            items_markup = "".join([f'<div style="margin-bottom: 3px;"><b style="color: #38bdf8;">•</b> {it.strip()}</div>' for it in parts[1:] if it.strip()])
            html_paras.append(f'<p style="margin: 0 0 6px 0; color: #e2e8f0; line-height: 1.6;">{intro}</p><div style="margin-bottom: 8px; color: #e2e8f0; line-height: 1.5;">{items_markup}</div>')
        else:
            html_paras.append(f'<p style="margin: 0 0 8px 0; line-height: 1.6; color: #e2e8f0;">{p}</p>')

    structured_text = f'<div style="line-height: 1.6;">{"".join(html_paras)}</div>'
    return matched_record.get("question", focus), structured_text


def process_user_query(query_text):
    """Processes question, extracts clinical entities, queries MedQuAD, and records turn."""
    clean_q = query_text.strip()
    if not clean_q:
        return

    active_id = st.session_state.active_session_id
    if active_id not in st.session_state.sessions:
        st.session_state.sessions[active_id] = {
            "id": active_id,
            "title": clean_q[:30] + ("..." if len(clean_q) > 30 else ""),
            "topic": "General",
            "icon_bg": "#1e3a8a",
            "icon_char": "💬",
            "query": clean_q,
            "date": datetime.now().strftime("%b %d, %Y"),
            "time": datetime.now().strftime("%I:%M %p"),
            "history": []
        }

    current_history = st.session_state.sessions[active_id].get("history", [])

    display_q, search_q = resolve_conversational_query(clean_q, current_history)
    entities = ner.extract_entities(search_q)

    method_map = {
        "Hybrid + Rerank": "hybrid_rerank",
        "Hybrid": "hybrid",
        "Dense (Semantic)": "dense",
        "TF-IDF (Keyword)": "tfidf"
    }
    ret_method = method_map.get(st.session_state.settings.get("retrieval_method"), "hybrid_rerank")
    top_k = int(st.session_state.settings.get("results_to_show", 5))
    thresh_str = str(st.session_state.settings.get("similarity_threshold", "50%")).replace("%", "")
    thresh = float(thresh_str) if thresh_str.isdigit() else 40.0

    response = retriever.search(
        user_query=search_q,
        top_k=top_k,
        method=ret_method,
        threshold=thresh
    )

    suggestions = []
    if response["is_relevant"] and response["results"]:
        top_match = response["results"][0]
        tailored_q, tailored_ans = get_targeted_answer(search_q, top_match)
        top_match["tailored_question"] = tailored_q
        top_match["tailored_answer"] = tailored_ans

        q_lower = search_q.lower()
        if "hypertens" in q_lower or "blood pressure" in q_lower:
            suggestions = [
                "What are the symptoms of hypertension?",
                "How is hypertension treated?",
                "Can hypertension be prevented?",
                "What foods should be avoided for high blood pressure?"
            ]
        else:
            suggestions = retriever.get_related_suggestions(top_match["focus"], search_q, max_suggestions=4)
            if len(suggestions) < 4:
                for r in response["results"][1:]:
                    if r["question"].lower() != clean_q.lower() and r["question"] not in suggestions:
                        suggestions.append(r["question"])
                    if len(suggestions) >= 4:
                        break

    turn_record = {
        "user_query": display_q,
        "resolved_query": search_q,
        "entities": entities,
        "response": response,
        "suggestions": suggestions,
        "timestamp": datetime.now().strftime("%I:%M %p")
    }
    current_history.append(turn_record)

    topic_tag = "General"
    icon_bg = "#334155"
    icon_char = "💬"
    matched_focus = response["results"][0].get("focus", "").strip() if response.get("results") else ""

    detection_text = f"{search_q} {matched_focus}".lower()
    if any(k in detection_text for k in ["chemo", "cancer", "tumor", "oncolog"]):
        topic_tag, icon_bg = "Cancer", "#581c87"
    elif any(k in detection_text for k in ["diabet", "insulin", "blood sugar", "glucose"]):
        topic_tag, icon_bg = "Diabetes", "#065f46"
    elif any(k in detection_text for k in ["asthma", "lung", "breath", "respirat", "cough"]):
        topic_tag, icon_bg = "Respiratory", "#1e3a8a"
    elif any(k in detection_text for k in ["pressure", "heart", "cardio", "hypertens", "stroke"]):
        topic_tag, icon_bg = "Cardiovascular", "#881337"
    elif any(k in detection_text for k in ["kidney", "renal", "nephro", "urine"]):
        topic_tag, icon_bg, icon_char = "Renal", "#0e7490", "🏥"
    elif any(k in detection_text for k in ["vitam", "diet", "nutrit", "food"]):
        topic_tag, icon_bg, icon_char = "Nutrition", "#9a3412", "👤"
    elif entities.get("diseases"):
        topic_tag, icon_bg = entities["diseases"][0].title()[:14], "#1e3a8a"

    active_sess = st.session_state.sessions[active_id]
    active_sess["history"] = current_history
    active_sess["query"] = display_q
    active_sess["topic"] = topic_tag
    active_sess["icon_bg"] = icon_bg
    active_sess["icon_char"] = icon_char
    active_sess["date"] = datetime.now().strftime("%b %d, %Y")
    active_sess["time"] = datetime.now().strftime("%I:%M %p")

    if active_sess.get("title") in ["New Chat", "Current Chat"]:
        if matched_focus:
            active_sess["title"] = matched_focus
        else:
            short_t = display_q.strip()
            active_sess["title"] = (short_t[:28].rstrip() + "...") if len(short_t) > 28 else short_t

    st.session_state.chat_history = current_history
    save_sessions_to_disk(st.session_state.sessions)


def handle_quick_question(q_text):
    """Callback when a quick question in the sidebar is clicked."""
    st.session_state.active_view = "chat"
    process_user_query(q_text)
    st.rerun()

def handle_suggestion_click(sugg_text):
    """Callback when a related question chip in the chat is clicked."""
    st.session_state.active_view = "chat"
    process_user_query(sugg_text)
    st.rerun()

def handle_open_session(session_id):
    """Callback to open a historical chat session."""
    st.session_state.active_session_id = session_id
    if session_id in st.session_state.sessions:
        st.session_state.chat_history = st.session_state.sessions[session_id].get("history", [])
    st.session_state.active_view = "chat"
    st.rerun()

def handle_clear_history():
    """Callback to delete all session history."""
    st.session_state.sessions = {}
    save_sessions_to_disk({})
    new_id = f"chat_{int(datetime.now().timestamp())}"
    st.session_state.active_session_id = new_id
    st.session_state.sessions[new_id] = {
        "id": new_id,
        "title": "New Chat",
        "topic": "General",
        "icon_bg": "#1e3a8a",
        "icon_char": "💬",
        "query": "",
        "date": datetime.now().strftime("%b %d, %Y"),
        "time": datetime.now().strftime("%I:%M %p"),
        "history": []
    }
    st.session_state.chat_history = []
    st.success("Chat history cleared successfully.")
    st.rerun()

def handle_start_new_chat():
    """Callback to start a fresh chat session."""
    new_id = f"chat_{int(datetime.now().timestamp())}"
    st.session_state.sessions[new_id] = {
        "id": new_id,
        "title": "New Chat",
        "topic": "General",
        "icon_bg": "#1e3a8a",
        "icon_char": "💬",
        "query": "",
        "date": datetime.now().strftime("%b %d, %Y"),
        "time": datetime.now().strftime("%I:%M %p"),
        "history": []
    }
    st.session_state.active_session_id = new_id
    st.session_state.chat_history = []
    st.session_state.active_view = "chat"
    st.rerun()

def handle_reset_settings():
    """Callback to reset settings back to default values."""
    default_settings = {
        "theme": "Dark",
        "language": "English",
        "default_page": "New Chat",
        "retrieval_method": "Hybrid + Rerank",
        "results_to_show": 5,
        "similarity_threshold": "50%",
        "source_filtering": True,
        "show_related_answers": True,
        "compact_view": True,
        "show_confidence_score": True,
        "show_entity_tags": True,
        "show_sidebar": True,
    }
    st.session_state.settings = default_settings
    save_settings_to_disk(default_settings)
    st.success("Settings have been restored to default.")
    st.rerun()


sidebar_quick_questions = [
    "What is Chemotherapy?",
    "What are the symptoms of Diabetes?",
    "How is Asthma treated?",
    "What causes Hypertension?"
]

has_history = len(st.session_state.chat_history) > 0
ui.render_sidebar(
    active_view=st.session_state.active_view,
    has_chat_history=has_history,
    quick_questions=sidebar_quick_questions,
    on_quick_question_click=handle_quick_question
)

current_view = st.session_state.active_view

if current_view == "chat":
    ui.render_chat_view(
        chat_history=st.session_state.chat_history,
        avatar_b64=AVATAR_B64,
        settings=st.session_state.settings,
        on_suggestion_click=handle_suggestion_click,
        total_pairs=len(df),
        total_sources=df["source"].nunique()
    )

    user_input = st.chat_input("Ask a medical question (e.g., 'What is chemotherapy?')...")
    if user_input:
        process_user_query(user_input)
        st.rerun()

elif current_view == "history":
    ui.render_history_view(
        sessions=st.session_state.sessions,
        on_open_session=handle_open_session,
        on_clear_history=handle_clear_history,
        on_start_new_chat=handle_start_new_chat
    )

elif current_view == "settings":
    ui.render_settings_view(
        settings=st.session_state.settings,
        on_clear_history=handle_clear_history,
        on_reset_settings=handle_reset_settings
    )
    save_settings_to_disk(st.session_state.settings)

elif current_view == "about":
    ui.render_about_view()
