"""
==============================================================================
Medical Q&A Assistant - UI Components Module
Student Project: MedQuAD Chatbot UI Layer
Separates UI rendering logic, HTML templates, and Streamlit components.
==============================================================================
"""

import os
import re
import base64
from datetime import datetime
import streamlit as st


def load_css(file_path="assets/style.css", theme="Dark"):
    """Loads external CSS file into Streamlit and injects active theme stylesheet."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    if str(theme).lower() == "light":
        light_path = os.path.join(os.path.dirname(file_path), "light_theme.css")
        if os.path.exists(light_path):
            with open(light_path, "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_base64_image(image_path="assets/robot_avatar.jpg"):
    """Encodes a local image to base64 for HTML embedding."""
    candidates = [
        image_path,
        os.path.join(os.path.dirname(__file__), image_path) if image_path else "",
        "assets/robot_avatar.jpg",
        os.path.join(os.path.dirname(__file__), "assets", "robot_avatar.jpg"),
        "robot_avatar.jpg",
        "medical_robot_avatar_1790159443756.jpg",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


def get_pill_class(topic_name):
    """Maps medical condition / topic to corresponding CSS pill badge style."""
    tn = str(topic_name).lower()
    if "cancer" in tn or "chemo" in tn:
        return "pill-cancer"
    if "diabet" in tn:
        return "pill-diabetes"
    if "respir" in tn or "asthma" in tn:
        return "pill-respiratory"
    if "cardio" in tn or "pressure" in tn or "heart" in tn:
        return "pill-cardiovascular"
    if "nutrit" in tn or "vitam" in tn:
        return "pill-nutrition"
    if "renal" in tn or "kidney" in tn:
        return "pill-renal"
    return "pill-general"


def render_header_stats(total_pairs=16358, total_sources=9):
    """Legacy helper kept for backward compatibility."""
    pass


def get_topic_icon_bg(topic, default_bg="#1e3a8a"):
    """Maps topic to vibrant card bubble background color matching the design."""
    t = str(topic).lower()
    if "cancer" in t or "chemo" in t:
        return "#7c3aed"
    if "diabet" in t:
        return "#0d9488"
    if "respir" in t or "asthma" in t:
        return "#2563eb"
    if "cardio" in t or "pressure" in t or "heart" in t:
        return "#e11d48"
    if "anxiet" in t or "hyper" in t:
        return "#7c3aed"
    if "nutrit" in t or "vitam" in t:
        return "#d97706"
    if "renal" in t or "kidney" in t:
        return "#0891b2"
    return default_bg or "#1d68f0"


def render_sidebar(active_view, has_chat_history, quick_questions, on_quick_question_click):
    """Renders the left navigation sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding: 2px 0;">
            <svg class="sidebar-logo-icon" xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/>
                <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/>
                <circle cx="20" cy="10" r="2"/>
            </svg>
            <div>
                <div class="sidebar-header-title">Medical Q&A<br>Assistant</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        is_chat_active = (active_view == "chat")
        if st.button("New Chat", key="btn_nav_new_chat", icon=":material/chat_bubble:", type="primary" if is_chat_active else "secondary", use_container_width=True):
            st.session_state.active_view = "chat"
            st.session_state.active_session_id = f"chat_{int(datetime.now().timestamp())}"
            st.session_state.sessions[st.session_state.active_session_id] = {
                "id": st.session_state.active_session_id,
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
            st.rerun()

        if st.button("Chat History", key="btn_nav_history", icon=":material/schedule:", type="primary" if active_view == "history" else "secondary", use_container_width=True):
            st.session_state.active_view = "history"
            st.rerun()

        if st.button("About", key="btn_nav_about", icon=":material/info:", type="primary" if active_view == "about" else "secondary", use_container_width=True):
            st.session_state.active_view = "about"
            st.rerun()

        if st.button("Settings", key="btn_nav_settings", icon=":material/settings:", type="primary" if active_view == "settings" else "secondary", use_container_width=True):
            st.session_state.active_view = "settings"
            st.rerun()

        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section-label'>💡 Quick Questions</div>", unsafe_allow_html=True)
        st.markdown('<div class="quick-question-box">', unsafe_allow_html=True)
        for q_text in quick_questions:
            if st.button(q_text, key=f"quick_{q_text}", use_container_width=True):
                on_quick_question_click(q_text)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-notice-card">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <div class="sidebar-notice-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                    </svg>
                </div>
                <span class="sidebar-notice-title">Medical Information Notice</span>
            </div>
            <div class="sidebar-notice-body">
                This information is for educational purposes only and is not a substitute for professional medical advice.
            </div>
        </div>

        <div class="sidebar-emergency-card">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <span style="font-size: 1.25rem; line-height: 1; flex-shrink: 0;">⚠️</span>
                <span class="sidebar-emergency-title">In case of emergency</span>
            </div>
            <div class="sidebar-emergency-body">
                Please contact your local emergency services immediately.
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_welcome_screen(avatar_b64):
    """Renders the centered neon glowing robot mascot welcome screen."""
    img_markup = (
        f'<div class="neon-mascot-circle" style="'
        f'display: inline-flex; align-items: center; justify-content: center; '
        f'border-radius: 50%; padding: 5px; '
        f'border: 3.5px solid #00d2ff; '
        f'box-shadow: 0 0 15px #00f0ff, 0 0 35px #00d2ff, 0 0 65px rgba(0, 210, 255, 0.75), inset 0 0 15px rgba(0, 240, 255, 0.5); '
        f'background: transparent;">'
        f'<img src="data:image/jpeg;base64,{avatar_b64}" style="width: 275px; height: 275px; border-radius: 50%; object-fit: cover; display: block;">'
        f'</div>'
    ) if avatar_b64 else '<span style="font-size: 7rem;">🤖</span>'

    st.markdown(f"""
    <div style="text-align: center; padding: 8px 20px 0 20px; max-width: 600px; margin: 0 auto;">
        <div style="display: flex; justify-content: center; margin-bottom: 12px;">
            {img_markup}
        </div>
        <h1 class="welcome-heading" style="font-size: 2.1rem; font-weight: 700; margin: 0 0 6px 0; letter-spacing: -0.5px;">Welcome!</h1>
        <div class="welcome-subheading" style="font-size: 1.1rem; font-weight: 600; margin-bottom: 8px;">
            Your MedQuAD AI Health Companion
        </div>
        <div class="welcome-desc" style="font-size: 0.86rem; line-height: 1.4; max-width: 450px; margin: 0 auto; padding-bottom: 0;">
            Evidence-based medical answers powered by the NIH.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_view(chat_history, avatar_b64, settings, on_suggestion_click, total_pairs=16358, total_sources=9):
    """Renders the conversational chat interface."""
    st.html(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0px; margin-bottom: 22px; flex-wrap: wrap; gap: 14px;">
        <div>
            <h1 class="chat-header-title" style="font-size: 1.85rem; font-weight: 700; margin: 0 0 4px 0; letter-spacing: -0.02em;">Medical Q&A Assistant</h1>
            <div class="chat-header-subtitle" style="font-size: 0.9rem;">NIH MedQUAD Medical Knowledge Base</div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <div class="stat-badge">
                <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2715%27%20height%3D%2715%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%2338bdf8%27%20stroke-width%3D%272.2%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M14%202H6a2%202%200%200%200-2%202v16a2%202%200%200%200%202%202h12a2%202%200%200%200%202-2V8z%27/%3E%3Cpolyline%20points%3D%2714%202%2014%208%2020%208%27/%3E%3Cline%20x1%3D%2716%27%20y1%3D%2713%27%20x2%3D%278%27%20y2%3D%2713%27/%3E%3Cline%20x1%3D%2716%27%20y1%3D%2717%27%20x2%3D%278%27%20y2%3D%2717%27/%3E%3Cpolyline%20points%3D%2710%209%209%209%208%209%27/%3E%3C/svg%3E" width="15" height="15" style="margin-right: 6px; flex-shrink: 0; vertical-align: middle;" />
                <span><span class="stat-badge-bold">{total_pairs:,}</span> Q&A Pairs</span>
            </div>
            <div class="stat-badge">
                <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2715%27%20height%3D%2715%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%2338bdf8%27%20stroke-width%3D%272.2%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cline%20x1%3D%273%27%20y1%3D%2721%27%20x2%3D%2721%27%20y2%3D%2721%27/%3E%3Cline%20x1%3D%273%27%20y1%3D%2710%27%20x2%3D%2721%27%20y2%3D%2710%27/%3E%3Cpolyline%20points%3D%275%206%2012%203%2019%206%27/%3E%3Cline%20x1%3D%274%27%20y1%3D%2710%27%20x2%3D%274%27%20y2%3D%2721%27/%3E%3Cline%20x1%3D%2720%27%20y1%3D%2710%27%20x2%3D%2720%27%20y2%3D%2721%27/%3E%3Cline%20x1%3D%278%27%20y1%3D%2714%27%20x2%3D%278%27%20y2%3D%2717%27/%3E%3Cline%20x1%3D%2712%27%20y1%3D%2714%27%20x2%3D%2712%27%20y2%3D%2717%27/%3E%3Cline%20x1%3D%2716%27%20y1%3D%2714%27%20x2%3D%2716%27%20y2%3D%2717%27/%3E%3C/svg%3E" width="15" height="15" style="margin-right: 6px; flex-shrink: 0; vertical-align: middle;" />
                <span><span class="stat-badge-bold">{total_sources}</span> NIH Sources</span>
            </div>
        </div>
    </div>
    """)

    if not chat_history:
        render_welcome_screen(avatar_b64)
        return

    total_turns = len(chat_history)
    for turn_idx, turn in enumerate(chat_history):
        user_q = turn["user_query"]
        entities = turn["entities"]
        response = turn["response"]
        suggestions = turn.get("suggestions", [])
        timestamp = turn.get("timestamp", "")
        is_latest = (turn_idx == total_turns - 1)

        st.html(f"""
        <div class="user-msg-row">
            <div class="user-avatar-circle"></div>
            <div class="user-bubble-box">
                <div class="user-msg-text">{user_q}</div>
                <div class="user-msg-time">{timestamp}</div>
            </div>
        </div>
        """)

        if not response.get("is_relevant") or not response.get("results"):
            st.html("""
            <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px;">
                <div class="bot-avatar-circle" style="background-color: #fef3c7;">
                    <span style="font-size: 1.1rem;">⚠️</span>
                </div>
                <div class="assistant-unified-card" style="border-color: #f59e0b; background-color: #fffbeb;">
                    <div style="font-size: 1rem; font-weight: 700; color: #b45309; margin-bottom: 4px;">No Relevant Medical Answer Found</div>
                    <div style="font-size: 0.88rem; color: #92400e; line-height: 1.5;">
                        I couldn't find a sufficiently relevant answer in the MedQuAD knowledge base.<br>
                        Try asking about symptoms, diseases, treatments, or medical conditions.
                    </div>
                </div>
            </div>
            """)
        else:
            top_match = response["results"][0]
            matched_q = top_match.get("tailored_question", top_match["question"])
            raw_answer = top_match.get("tailored_answer", top_match["answer"])
            if raw_answer.strip().startswith("<"):
                clean_answer = raw_answer
            else:
                clean_answer = re.sub(r'[ \t]{4,}', '<br><br>', raw_answer)
                clean_answer = clean_answer.replace("\n\n", "<br><br>").replace("\n", "<br>")

            badges_html = ""
            if settings.get("show_entity_tags", True):
                for d in entities.get("diseases", []):
                    badges_html += f'<span class="chat-entity-pill entity-pill-disease">{d.title()} - Disease</span> '
                for s in entities.get("symptoms", []):
                    badges_html += f'<span class="chat-entity-pill entity-pill-symptom">{s.title()} - Symptom</span> '
                for t in entities.get("treatments", []):
                    badges_html += f'<span class="chat-entity-pill entity-pill-treatment">{t.title()} - Treatment</span> '
                for diag in entities.get("diagnostics", []):
                    badges_html += f'<span class="chat-entity-pill entity-pill-diagnostic">{diag.title()} - Diagnostic Test</span> '

            if not badges_html:
                badges_html = '<span style="color: #64748b; font-size: 0.85rem;">No specific clinical entities detected.</span>'

            score_val = top_match.get("score", 78)
            score_badge_html = ""
            if settings.get("show_confidence_score", True):
                score_badge_html = f"""
                <div class="card-match-badge">
                    <div style="font-size: 0.72rem; color: #2563eb; font-weight: 600;">Retrieval Match</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #2563eb; line-height: 1.1; margin-top: 2px;">{score_val}%</div>
                </div>
                """

            f_topic = top_match.get('focus', 'General')
            f_cond = 'High blood pressure' if 'hypertens' in f_topic.lower() else f_topic
            f_cat = 'Cardiovascular' if any(w in f_topic.lower() for w in ['heart', 'cardio', 'hypertens', 'blood pressure']) else top_match.get('qtype', 'Information').title()
            f_src = top_match.get('source', 'NIH')

            ref_url = top_match.get("url", "")
            source_display = f_src
            if "medline" in source_display.lower():
                source_display = "NIH MedlinePlus"
            elif not source_display.startswith("NIH"):
                source_display = f"NIH {source_display}"

            view_src_btn = ""
            if ref_url:
                view_src_btn = f"""
                <a href="{ref_url}" target="_blank" style="display: flex; align-items: center; gap: 5px; color: #2563eb; font-weight: 600; font-size: 0.84rem; text-decoration: none;">
                    <span>View Source</span>
                    <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2713%27%20height%3D%2713%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%232563eb%27%20stroke-width%3D%272.2%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M18%2013v6a2%202%200%200%201-2%202H5a2%202%200%200%201-2-2V8a2%202%200%200%201%202-2h6%27/%3E%3Cpolyline%20points%3D%2715%203%2021%203%2021%209%27/%3E%3Cline%20x1%3D%2710%27%20y1%3D%2714%27%20x2%3D%2721%27%20y2%3D%273%27/%3E%3C/svg%3E" width="13" height="13" style="vertical-align: middle; display: inline-block;" />
                </a>
                """

            st.html(f"""
            <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px;">
                <div class="bot-avatar-circle"></div>
                <div class="assistant-unified-card" style="flex: 1; min-width: 0;">
                    <div style="margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2716%27%20height%3D%2716%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%23e11d48%27%20stroke-width%3D%272.4%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M22%2012h-4l-3%209L9%203l-3%209H2%27/%3E%3C/svg%3E" width="16" height="16" style="vertical-align: middle; display: inline-block;" />
                            <span class="card-section-title" style="font-weight: 700; font-size: 0.92rem; color: #0f172a;">Detected Clinical Entities</span>
                        </div>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                            {badges_html}
                        </div>
                    </div>
                    <div style="border-top: 1px solid #f1f5f9; margin-top: 14px; margin-bottom: 16px;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2718%27%20height%3D%2718%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%232563eb%27%20stroke-width%3D%272.2%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27m12%203-1.912%205.813a2%202%200%200%201-1.275%201.275L3%2012l5.813%201.912a2%202%200%200%201%201.275%201.275L12%2021l1.912-5.813a2%202%200%200%201%201.275-1.275L21%2012l-5.813-1.912a2%202%200%200%201-1.275-1.275L12%203Z%27/%3E%3C/svg%3E" width="18" height="18" style="vertical-align: middle; display: inline-block;" />
                                <span class="card-section-title" style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">Assistant Response</span>
                            </div>
                            <div style="font-size: 0.94rem; font-weight: 700; color: #2563eb; margin-top: 6px;">
                                Matched Question: {matched_q}
                            </div>
                        </div>
                        {score_badge_html}
                    </div>
                    <div class="card-metadata-row" style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 0.84rem; margin-bottom: 14px;">
                        <span><span class="meta-label">Topic:</span> <span class="meta-val">{f_topic}</span></span>
                        <span class="meta-sep" style="color: #cbd5e1;">|</span>
                        <span><span class="meta-label">Condition:</span> <span class="meta-val">{f_cond}</span></span>
                        <span class="meta-sep" style="color: #cbd5e1;">|</span>
                        <span><span class="meta-label">Category:</span> <span class="meta-val">{f_cat}</span></span>
                        <span class="meta-sep" style="color: #cbd5e1;">|</span>
                        <span><span class="meta-label">Source:</span> <span class="meta-val">{f_src}</span></span>
                    </div>
                    <div class="answer-text" style="font-size: 0.92rem; line-height: 1.65; margin-bottom: 16px;">
                        {clean_answer}
                    </div>
                    <div class="card-source-bar" style="display: flex; justify-content: space-between; align-items: center; background-color: #f0f7ff; border: 1px solid #e0f2fe; border-radius: 8px; padding: 10px 16px; margin-top: 14px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <img src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2715%27%20height%3D%2715%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%232563eb%27%20stroke-width%3D%272.2%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M10%2013a5%205%200%200%200%207.54.54l3-3a5%205%200%200%200-7.07-7.07l-1.72%201.71%27/%3E%3Cpath%20d%3D%27M14%2011a5%205%200%200%200-7.54-.54l-3%203a5%205%200%200%200%207.07%207.07l1.71-1.71%27/%3E%3C/svg%3E" width="15" height="15" style="vertical-align: middle; display: inline-block;" />
                            <span style="font-weight: 700; color: #1d4ed8; font-size: 0.88rem;">Source: {source_display}</span>
                        </div>
                        {view_src_btn}
                    </div>
                </div>
            </div>
            """)

            if is_latest and suggestions and settings.get("show_related_answers", True):
                with st.container(border=True, key=f"sugg_box_{turn_idx}"):
                    st.html("""
                    <div class="sugg-header-row" style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                        <img class="sugg-header-icon" src="data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%2716%27%20height%3D%2716%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%2338bdf8%27%20stroke-width%3D%272.2%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27M15%2014c.2-1%20.7-1.7%201.5-2.5%201-.9%201.5-2.2%201.5-3.5A6%206%200%200%200%206%208c0%201%20.2%202.2%201.5%203.5.7.7%201.3%201.5%201.5%202.5%27/%3E%3Cpath%20d%3D%27M9%2018h6%27/%3E%3Cpath%20d%3D%27M10%2022h4%27/%3E%3C/svg%3E" width="16" height="16" style="vertical-align: middle; display: inline-block;" />
                        <span class="sugg-header-title" style="font-weight: 700; font-size: 0.95rem;">You may also want to ask ?</span>
                    </div>
                    """)

                    for row_start in range(0, min(4, len(suggestions)), 2):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            sug_a = suggestions[row_start]
                            sug_a_clean = re.sub(r'^(?:[>\s<›»•\-\*]|&gt;|&lt;)+', '', str(sug_a)).strip()
                            if st.button(sug_a_clean, key=f"sug_{turn_idx}_{row_start}", use_container_width=True):
                                on_suggestion_click(sug_a_clean)
                        if row_start + 1 < len(suggestions):
                            with col_b:
                                sug_b = suggestions[row_start + 1]
                                sug_b_clean = re.sub(r'^(?:[>\s<›»•\-\*]|&gt;|&lt;)+', '', str(sug_b)).strip()
                                if st.button(sug_b_clean, key=f"sug_{turn_idx}_{row_start+1}", use_container_width=True):
                                    on_suggestion_click(sug_b_clean)


def render_history_view(sessions, on_open_session, on_clear_history, on_start_new_chat):
    """Renders the dedicated Chat History page."""
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown("""
        <div style="margin-bottom: 18px;">
            <h1 class="page-title" style="font-size: 1.85rem; font-weight: 700; margin: 0 0 2px 0;">Chat History</h1>
            <div class="page-subtitle" style="font-size: 0.88rem;">View and manage your previous conversations</div>
        </div>
        """, unsafe_allow_html=True)
    with h_col2:
        st.markdown('<div style="text-align: right; padding-top: 6px;">', unsafe_allow_html=True)
        if st.button("🗑️ Clear All History", key="btn_clear_all_hist"):
            on_clear_history()
        st.markdown('</div>', unsafe_allow_html=True)

    search_col, filter_col = st.columns([3.2, 1.2])
    with search_col:
        search_query = st.text_input(
            "Search your chat history...",
            placeholder="🔍 Search your chat history...",
            label_visibility="collapsed",
            key="hist_search_input"
        )
    with filter_col:
        filter_cat = st.selectbox(
            "Filter Category",
            ["All Chats", "Cancer", "Diabetes", "Cardiovascular", "Respiratory", "Nutrition", "Renal", "General"],
            label_visibility="collapsed",
            key="hist_cat_filter"
        )

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    def _sess_sort_key(s):
        try:
            s_id = s.get("id", "")
            if s_id.startswith("chat_"):
                return int(s_id.split("_")[1])
        except Exception:
            pass
        return 0

    all_sessions_list = sorted(
        [s for s in sessions.values() if len(s.get("history", [])) > 0],
        key=_sess_sort_key,
        reverse=True
    )
    filtered_sessions = []
    for s in all_sessions_list:
        topic = s.get("topic", "General")
        if filter_cat != "All Chats" and filter_cat.lower() not in topic.lower():
            continue
        if search_query.strip():
            sq = search_query.strip().lower()
            text_corpus = f"{s.get('title','')} {s.get('topic','')} {s.get('query','')}".lower()
            if sq not in text_corpus:
                continue
        filtered_sessions.append(s)

    if not all_sessions_list:
        st.markdown("""
        <div class="hist-empty-card" style="text-align: center; padding: 60px 20px; border-radius: 12px; margin-top: 16px;">
            <div style="font-size: 2.8rem; margin-bottom: 12px;">🕒</div>
            <div class="hist-empty-title" style="font-size: 1.25rem; font-weight: 600; margin-bottom: 8px;">No Saved Chat History Yet</div>
            <div class="hist-empty-desc" style="font-size: 0.88rem; max-width: 440px; margin: 0 auto 20px auto; line-height: 1.5;">
                All medical questions you ask are permanently recorded and organized here with dates, clinical tags, and timestamps so you can review them anytime.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; margin-top: 16px;">', unsafe_allow_html=True)
        if st.button("💬 Start a New Chat", key="btn_start_new_chat_hist"):
            on_start_new_chat()
        st.markdown('</div>', unsafe_allow_html=True)

    elif not filtered_sessions:
        st.markdown("""
        <div class="hist-empty-card" style="text-align: center; padding: 50px 20px; border-radius: 12px; margin-top: 16px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;">🔍</div>
            <div class="hist-empty-title" style="font-size: 1.15rem; font-weight: 600; margin-bottom: 6px;">No Matches Found</div>
            <div class="hist-empty-desc" style="font-size: 0.88rem; max-width: 400px; margin: 0 auto 16px auto;">
                No saved searches matched your query or category filter. Try clearing the filter.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        with st.container(key="hist_cards_list"):
            for idx, sess in enumerate(filtered_sessions):
                s_id = sess["id"]
                title = sess.get("title", "Medical Conversation")
                topic = sess.get("topic", "General")
                query_preview = sess.get("query", "")
                s_date = sess.get("date", datetime.now().strftime("%b %d, %Y"))
                s_time = sess.get("time", datetime.now().strftime("%I:%M %p"))
                icon_bg = get_topic_icon_bg(topic, sess.get("icon_bg", "#1e3a8a"))
                pill_cls = get_pill_class(topic)

                with st.container(border=True, key=f"hist_card_{idx}"):
                    card_col_main, card_col_dt, card_col_arrow = st.columns([7.0, 2.2, 0.8], vertical_alignment="center")

                    with card_col_main:
                        st.markdown(f"""
                        <div style="display: flex; align-items: flex-start; gap: 14px; padding: 2px 0;">
                            <span class="hist-icon-badge" style="background-color: {icon_bg};">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="#ffffff">
                                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                                </svg>
                            </span>
                            <div style="min-width: 0; flex: 1;">
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap;">
                                    <span class="hist-card-title">{title}</span>
                                    <span class="pill-tag {pill_cls}">{topic}</span>
                                </div>
                                <div class="hist-card-query">
                                    {query_preview}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with card_col_dt:
                        st.markdown(f"""
                        <div class="hist-card-datetime" style="text-align: right; padding-right: 6px;">
                            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 5px; margin-bottom: 3px;">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                    <line x1="16" y1="2" x2="16" y2="6"></line>
                                    <line x1="8" y1="2" x2="8" y2="6"></line>
                                    <line x1="3" y1="10" x2="21" y2="10"></line>
                                </svg>
                                <span>{s_date}</span>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 5px;">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <polyline points="12 6 12 12 16 14"></polyline>
                                </svg>
                                <span>{s_time}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with card_col_arrow:
                        if st.button(">", key=f"open_chat_{s_id}_{idx}", use_container_width=True):
                            on_open_session(s_id)


def render_settings_view(settings, on_clear_history, on_reset_settings):
    """Renders the dedicated Settings page."""
    st.markdown("""
    <div style="margin-bottom: 22px;">
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #ffffff; margin: 0 0 2px 0;">Settings</h1>
        <div style="font-size: 0.88rem; color: #94a3b8;">Customize your experience and preferences</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="settings-card">
        <div class="settings-title">⚙️ General Settings</div>
        <div class="settings-sub">Basic preferences for the application</div>
    """, unsafe_allow_html=True)

    r1_col1, r1_col2 = st.columns([7, 3])
    with r1_col1:
        st.markdown("""
        <div class="settings-label">Theme</div>
        <div class="settings-desc">Choose between light and dark mode.</div>
        """, unsafe_allow_html=True)
    with r1_col2:
        t_col_l, t_col_d = st.columns(2)
        active_theme = settings.get("theme", "Dark")
        with t_col_l:
            if st.button("☀️ Light", key="set_theme_light", use_container_width=True, type="primary" if active_theme == "Light" else "secondary"):
                settings["theme"] = "Light"
                st.session_state.settings["theme"] = "Light"
                if "save_settings" in st.session_state and callable(st.session_state.save_settings):
                    st.session_state.save_settings()
                st.rerun()
        with t_col_d:
            if st.button("🌙 Dark", key="set_theme_dark", use_container_width=True, type="primary" if active_theme == "Dark" else "secondary"):
                settings["theme"] = "Dark"
                st.session_state.settings["theme"] = "Dark"
                if "save_settings" in st.session_state and callable(st.session_state.save_settings):
                    st.session_state.save_settings()
                st.rerun()

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    r2_col1, r2_col2 = st.columns([7, 3])
    with r2_col1:
        st.markdown("""
        <div class="settings-label">Language</div>
        <div class="settings-desc">Select your preferred language.</div>
        """, unsafe_allow_html=True)
    with r2_col2:
        st.selectbox("Language", ["English", "Spanish", "French", "German"], index=0, label_visibility="collapsed", key="set_lang")

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    r3_col1, r3_col2 = st.columns([7, 3])
    with r3_col1:
        st.markdown("""
        <div class="settings-label">Default Page</div>
        <div class="settings-desc">Choose which page opens when you launch the app.</div>
        """, unsafe_allow_html=True)
    with r3_col2:
        st.selectbox("Default Page", ["New Chat", "Chat History", "Settings"], index=0, label_visibility="collapsed", key="set_def_page")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="settings-card">
        <div class="settings-title">🔍 Search & Retrieval Settings</div>
        <div class="settings-sub">Configure how we find and rank relevant information</div>
    """, unsafe_allow_html=True)

    sr2_col1, sr2_col2 = st.columns([7, 3])
    with sr2_col1:
        st.markdown("""
        <div class="settings-label">Results to Show</div>
        <div class="settings-desc">Number of top results to display.</div>
        """, unsafe_allow_html=True)
    with sr2_col2:
        sel_results = st.selectbox(
            "Results to Show",
            [1, 3, 5, 10],
            index=[1, 3, 5, 10].index(int(settings.get("results_to_show", 5))),
            label_visibility="collapsed",
            key="set_results_show"
        )
        settings["results_to_show"] = sel_results

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    sr3_col1, sr3_col2 = st.columns([7, 3])
    with sr3_col1:
        st.markdown("""
        <div class="settings-label">Similarity Threshold</div>
        <div class="settings-desc">Minimum relevance score for results.</div>
        """, unsafe_allow_html=True)
    with sr3_col2:
        sel_thresh = st.selectbox(
            "Similarity Threshold",
            ["30%", "40%", "50%", "60%", "70%"],
            index=["30%", "40%", "50%", "60%", "70%"].index(
                settings.get("similarity_threshold", "50%")
            ),
            label_visibility="collapsed",
            key="set_sim_thresh"
        )
        settings["similarity_threshold"] = sel_thresh

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    sr4_col1, sr4_col2 = st.columns([7, 3])
    with sr4_col1:
        st.markdown("""
        <div class="settings-label">Enable Source Filtering</div>
        <div class="settings-desc">Allow filtering by specific NIH sources.</div>
        """, unsafe_allow_html=True)
    with sr4_col2:
        settings["source_filtering"] = st.toggle(
            "Enable Source Filtering",
            value=settings.get("source_filtering", True),
            label_visibility="collapsed",
            key="set_toggle_src_filter"
        )

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    sr5_col1, sr5_col2 = st.columns([7, 3])
    with sr5_col1:
        st.markdown("""
        <div class="settings-label">Show Related Answers</div>
        <div class="settings-desc">Display related questions and answers below each response.</div>
        """, unsafe_allow_html=True)
    with sr5_col2:
        settings["show_related_answers"] = st.toggle(
            "Show Related Answers",
            value=settings.get("show_related_answers", True),
            label_visibility="collapsed",
            key="set_toggle_rel_ans"
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="settings-card">
        <div class="settings-title">💻 Display Preferences</div>
        <div class="settings-sub">Customize the look and feel of the chat interface</div>
    """, unsafe_allow_html=True)

    dp1_col1, dp1_col2 = st.columns([7, 3])
    with dp1_col1:
        st.markdown("""
        <div class="settings-label">Compact View</div>
        <div class="settings-desc">Reduce spacing for a denser layout (more content on screen).</div>
        """, unsafe_allow_html=True)
    with dp1_col2:
        settings["compact_view"] = st.toggle(
            "Compact View",
            value=settings.get("compact_view", True),
            label_visibility="collapsed",
            key="set_toggle_compact"
        )

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    dp2_col1, dp2_col2 = st.columns([7, 3])
    with dp2_col1:
        st.markdown("""
        <div class="settings-label">Show Confidence Score</div>
        <div class="settings-desc">Display retrieval match percentage (not exceeding 100%).</div>
        """, unsafe_allow_html=True)
    with dp2_col2:
        settings["show_confidence_score"] = st.toggle(
            "Show Confidence Score",
            value=settings.get("show_confidence_score", True),
            label_visibility="collapsed",
            key="set_toggle_conf_score"
        )

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    dp3_col1, dp3_col2 = st.columns([7, 3])
    with dp3_col1:
        st.markdown("""
        <div class="settings-label">Show Clinical Entity Tags</div>
        <div class="settings-desc">Highlight detected medical entities in the query.</div>
        """, unsafe_allow_html=True)
    with dp3_col2:
        settings["show_entity_tags"] = st.toggle(
            "Show Clinical Entity Tags",
            value=settings.get("show_entity_tags", True),
            label_visibility="collapsed",
            key="set_toggle_entity_tags"
        )

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    dp4_col1, dp4_col2 = st.columns([7, 3])
    with dp4_col1:
        st.markdown("""
        <div class="settings-label">Show Sidebar</div>
        <div class="settings-desc">Keep the left sidebar visible at all times.</div>
        """, unsafe_allow_html=True)
    with dp4_col2:
        settings["show_sidebar"] = st.toggle(
            "Show Sidebar",
            value=settings.get("show_sidebar", True),
            label_visibility="collapsed",
            key="set_toggle_sidebar"
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="settings-card">
        <div class="settings-title">🛡️ Data & Privacy</div>
        <div class="settings-sub">Manage your data and usage</div>
    """, unsafe_allow_html=True)

    dp_col1, dp_col2 = st.columns([7, 3])
    with dp_col1:
        st.markdown("""
        <div class="settings-label">Clear Chat History</div>
        <div class="settings-desc">Delete all your chat conversations.</div>
        """, unsafe_allow_html=True)
    with dp_col2:
        if st.button("🗑️ Clear", key="btn_settings_clear_hist"):
            on_clear_history()

    st.markdown("<hr style='border: 0; border-top: 1px solid #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)

    res_col1, res_col2 = st.columns([7, 3])
    with res_col1:
        st.markdown("""
        <div class="settings-label">Reset Settings</div>
        <div class="settings-desc">Restore default settings.</div>
        """, unsafe_allow_html=True)
    with res_col2:
        if st.button("🔄 Reset", key="btn_settings_reset"):
            on_reset_settings()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="settings-card">
        <div class="settings-title">ℹ️ About</div>
        <div class="settings-sub">Information about this application</div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 6px;">
            <span style="font-size: 0.92rem; color: #94a3b8;">Version</span>
            <span style="font-size: 0.92rem; font-weight: 600; color: #f8fafc;">Medical Q&A Assistant v1.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: rgba(30, 58, 138, 0.2); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 8px; padding: 12px 16px; display: flex; align-items: center; gap: 10px; margin-top: 10px;">
        <span style="color: #38bdf8; font-size: 1.1rem;">ℹ️</span>
        <span style="font-size: 0.84rem; color: #93c5fd;">Your settings are automatically saved and will be applied immediately.</span>
    </div>
    """, unsafe_allow_html=True)


def render_about_view():
    """Renders the About application overview page."""
    st.markdown("""
    <div style="margin-bottom: 22px;">
        <h1 class="page-title" style="font-size: 1.85rem; font-weight: 700; margin: 0 0 4px 0;">About Medical Q&A Assistant</h1>
        <div class="welcome-desc" style="font-size: 0.88rem; color: #64748b;">Architecture, Knowledge Base, and Clinical Verification</div>
    </div>

    <!-- 1. Blue Card: NIH MedQuAD Dataset -->
    <div class="about-card about-card-blue">
        <div class="about-card-header">
            <div class="about-icon-badge about-icon-blue">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                </svg>
            </div>
            <div>
                <div class="about-card-title about-title-blue">NIH MedQuAD Dataset</div>
                <div class="about-card-sub about-sub-blue">Trusted biomedical question-answering corpus</div>
            </div>
        </div>
        <div class="about-card-body about-body-blue">
            The <b>MedQuAD</b> (Medical Question Answering Dataset) is curated by the U.S. National Library of Medicine (NLM) and the National Institutes of Health (NIH).
            It comprises <b>16,358 medical question-answer pairs</b> across 9 authoritative NIH institutes, covering diseases, drugs, diagnostic tests, and treatments.
        </div>
    </div>

    <!-- 2. Green Card: Information Retrieval Pipeline -->
    <div class="about-card about-card-green">
        <div class="about-card-header">
            <div class="about-icon-badge about-icon-green">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
            </div>
            <div>
                <div class="about-card-title about-title-green">Information Retrieval Pipeline</div>
                <div class="about-card-sub about-sub-green">Hybrid Dense Semantic Embedding + Lexical TF-IDF + Entity Reranking</div>
            </div>
        </div>
        <div class="about-card-body about-body-green">
            <div class="about-bullet-list">
                <div class="about-bullet">
                    <span class="bullet-dot">•</span>
                    <div><b>Dense Semantic Search:</b> Precomputed 384-dimensional dense vectors using <code>all-MiniLM-L6-v2</code>.</div>
                </div>
                <div class="about-bullet">
                    <span class="bullet-dot">•</span>
                    <div><b>Lexical Search:</b> High-dimensional sublinear TF-IDF sparse matrix.</div>
                </div>
                <div class="about-bullet">
                    <span class="bullet-dot">•</span>
                    <div><b>Hybrid Blending:</b> 65% dense semantic similarity + 35% TF-IDF keyword overlap.</div>
                </div>
                <div class="about-bullet">
                    <span class="bullet-dot">•</span>
                    <div><b>Clinical Entity Recognition:</b> Regex-assisted clinical NER for diseases, symptoms, diagnostic tests, and treatments.</div>
                </div>
                <div class="about-bullet">
                    <span class="bullet-dot">•</span>
                    <div><b>Conversational Coreference Resolution:</b> Dynamically resolves multi-turn questions to prior topics.</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 3. Red Card: Clinical & Legal Disclaimer -->
    <div class="about-card about-card-red">
        <div class="about-card-header">
            <div class="about-icon-badge about-icon-red">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="#dc2626">
                    <path d="M12 2L1 21h22L12 2zm0 3.5L20.5 19h-17L12 5.5zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z"/>
                </svg>
            </div>
            <div>
                <div class="about-card-title about-title-red">Clinical & Legal Disclaimer</div>
            </div>
        </div>
        <div class="about-card-body about-body-red">
            Medical Q&A Assistant is designed for educational and informational purposes only. It is not intended to provide clinical diagnosis, medical treatment, or replace the advice of a qualified healthcare professional.
        </div>
    </div>
    """, unsafe_allow_html=True)
