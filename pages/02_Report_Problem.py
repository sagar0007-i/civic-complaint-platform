"""Citizen Complaint Submission Wizard."""

import os
import sys
from pathlib import Path
import streamlit as st
import folium
from streamlit_folium import st_folium

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import settings
from backend.database import get_db_session
from backend.models.complaint import ComplaintSeverity
from backend.schemas.complaint import ComplaintCreateSchema, LocationCreateSchema, MediaUploadMetaSchema
from backend.services.complaint_service import ComplaintService
import importlib
import backend.services.location_service
import backend.utils.india_boundary
try:
    importlib.reload(backend.services.location_service)
    importlib.reload(backend.utils.india_boundary)
except Exception:
    pass

from backend.services.storage_service import get_storage_provider
from backend.services.location_service import LocationService
from backend.services.ai_service import AIService
from backend.services.yolo_service import YOLOPotholeDetector
from backend.services.whisper_service import WhisperAudioService
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.ward_repo import WardRepository
from backend.repositories.user_repo import UserRepository
from backend.utils.session import init_session_state, get_current_user, is_logged_in, apply_custom_css
from backend.utils.icons import icon_svg
from backend.utils.india_boundary import add_india_boundary_layer, add_maharashtra_boundary_layer


def is_in_maharashtra(loc_svc: LocationService, lat: float, lng: float) -> bool:
    """Safe boundary check for Maharashtra that never raises AttributeError."""
    try:
        if hasattr(loc_svc, "is_within_maharashtra_bounds"):
            return loc_svc.is_within_maharashtra_bounds(lat, lng)
    except Exception:
        pass
    return 15.50 <= lat <= 22.20 and 72.50 <= lng <= 81.00


init_session_state()
apply_custom_css()

st.markdown(f'<h1 class="main-header">{icon_svg("file-text", size=28, color="#1E3A8A")} Report a Civic Problem</h1>', unsafe_allow_html=True)
st.caption("Help local authorities resolve issues in your neighborhood in ~2 minutes.")

# Ensure session state variables for wizard
if "report_step" not in st.session_state:
    st.session_state.report_step = 1
if "report_category_id" not in st.session_state:
    st.session_state.report_category_id = None
if "report_category_name" not in st.session_state:
    st.session_state.report_category_name = None
if "report_category_slug" not in st.session_state:
    st.session_state.report_category_slug = None
if "report_title" not in st.session_state:
    st.session_state.report_title = ""
if "report_description" not in st.session_state:
    st.session_state.report_description = ""
if "report_severity" not in st.session_state:
    st.session_state.report_severity = "MEDIUM"
if "report_landmark" not in st.session_state:
    st.session_state.report_landmark = ""
if "report_lat" not in st.session_state:
    st.session_state.report_lat = settings.DEFAULT_LATITUDE
if "report_lng" not in st.session_state:
    st.session_state.report_lng = settings.DEFAULT_LONGITUDE
if "report_address" not in st.session_state:
    st.session_state.report_address = ""
if "report_sector" not in st.session_state:
    st.session_state.report_sector = ""
if "report_ward_id" not in st.session_state:
    st.session_state.report_ward_id = None
if "uploaded_media_meta" not in st.session_state:
    st.session_state.uploaded_media_meta = []
if "submitted_complaint_number" not in st.session_state:
    st.session_state.submitted_complaint_number = None

# Step indicator progress bar
step_names = ["Select Category", "Describe Problem", "Photo & Video Proof", "Pin Location", "Review & Submit"]
curr_step = st.session_state.report_step

if curr_step <= 5:
    pct = int((curr_step / 5) * 100)
    current_label = step_names[curr_step - 1].upper()
    st.markdown(
        f"""
        <div style="background:#ffffff; border:1.5px solid #cbd5e1; border-radius:12px; padding:12px 18px; margin-bottom:0.8rem; box-shadow:0 2px 8px rgba(15,45,107,0.06);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="font-family:'Rajdhani', sans-serif; font-weight:700; font-size:1.05rem; color:#0f2d6b; letter-spacing:0.02em;">
                    STEP {curr_step} OF 5 — <span style="color:#ff9900;">{current_label}</span>
                </div>
                <div style="background:rgba(255,153,0,0.12); color:#e67e00; border:1px solid rgba(255,153,0,0.3); border-radius:9999px; padding:2px 10px; font-weight:700; font-size:0.8rem;">
                    {pct}% COMPLETED
                </div>
            </div>
            <div style="width:100%; height:8px; background-color:#e2e8f0; border-radius:9999px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:linear-gradient(90deg, #0f2d6b 0%, #ff9900 100%); border-radius:9999px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clickable Step Breadcrumbs Bar (Direct jump to any step)
    step_short_names = ["1. Category", "2. Details", "3. Media", "4. Location", "5. Review"]
    step_cols = st.columns(5)
    for s_idx, s_col in enumerate(step_cols, 1):
        with s_col:
            if s_idx == curr_step:
                st.button(f"📍 {step_short_names[s_idx-1]}", key=f"top_step_btn_{s_idx}", type="primary", use_container_width=True)
            elif s_idx < curr_step:
                if st.button(f"⬅️ {step_short_names[s_idx-1]}", key=f"top_step_btn_{s_idx}", type="secondary", use_container_width=True):
                    st.session_state.report_step = s_idx
                    st.rerun()
            else:
                st.button(f"{step_short_names[s_idx-1]}", key=f"top_step_btn_{s_idx}", disabled=True, use_container_width=True)

    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# STEP 1: SELECT CATEGORY
# -----------------------------------------------------------------------------
if st.session_state.report_step == 1:
    st.markdown("### **STEP 1: SELECT PROBLEM CATEGORY**")
    st.caption("Choose the category that best describes your civic issue. Can't find it? Use **'Other / Not Listed'** at the bottom.")

    with get_db_session() as session:
        cat_repo = CategoryRepository(session)
        categories = cat_repo.get_all(active_only=True)

    # ── EXPRESS VOICE GRIEVANCE ASSISTANT (WHISPER) ───────────────────────────
    if settings.WHISPER_ENABLED and categories:
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                    <span style="font-size:1.4rem;">🎙️</span>
                    <div>
                        <span style="font-family:'Rajdhani', sans-serif; font-weight:700; color:#0f2d6b; font-size:1.1rem; display:block;">
                            EXPRESS VOICE GRIEVANCE REPORTING
                        </span>
                        <span style="font-size:0.83rem; color:#64748b;">
                            बोलून तक्रार नोंदवा · बोलकर शिकायत दर्ज करें · Speak in Marathi, Hindi, or English
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Language Selection Pill
            lang_col1, _ = st.columns([1.5, 2.5])
            with lang_col1:
                selected_lang_label = st.selectbox(
                    "🗣️ Spoken Language (भाषा निवडा / भाषा चुनें)",
                    options=["🌐 Auto-Detect (स्वयंचलित)", "🇮🇳 हिन्दी (Hindi)", "🚩 मराठी (Marathi)", "🇬🇧 English"],
                    key="voice_lang_choice",
                    help="Select your spoken language for 100% accurate transcription.",
                )
            lang_code_map = {
                "🌐 Auto-Detect (स्वयंचलित)": None,
                "🇮🇳 हिन्दी (Hindi)": "hi",
                "🚩 मराठी (Marathi)": "mr",
                "🇬🇧 English": "en",
            }
            chosen_lang_code = lang_code_map.get(selected_lang_label)

            audio_source = None
            tab_mic, tab_upload_audio = st.tabs(["🎤 Record Live Voice", "📁 Upload Audio Clip"])

            with tab_mic:
                if hasattr(st, "audio_input"):
                    audio_source = st.audio_input(
                        "Click the microphone to record your complaint (e.g. 'मेरे घर के आगे एक कूड़ेदान है सेक्टर 24' or 'Garbage dump near hospital gate')",
                        key="voice_audio_mic"
                    )
                else:
                    st.caption("Microphone input active on supported browsers.")

            with tab_upload_audio:
                audio_file = st.file_uploader(
                    "Upload Voice Note (WAV, MP3, M4A, OGG, WEBM)",
                    type=["wav", "mp3", "m4a", "ogg", "webm"],
                    key="voice_audio_upload",
                )
                if audio_file is not None and audio_source is None:
                    audio_source = audio_file

            if audio_source is not None:
                audio_bytes = audio_source.read() if hasattr(audio_source, "read") else audio_source.getvalue()

                if audio_bytes:
                    with st.spinner("🤖 Whisper is transcribing and translating your voice grievance..."):
                        whisper_svc = WhisperAudioService()
                        trans_res = whisper_svc.transcribe_audio(audio_bytes, language_override=chosen_lang_code)

                    if trans_res.success and trans_res.text:
                        # Parse structured elements (distinct title, description, landmark, sector address)
                        ai_svc = AIService()
                        parsed = ai_svc.parse_voice_transcript(
                            trans_res.text,
                            english_translation=trans_res.english_translation,
                        )

                        matched_slug = parsed.get("suggested_category_slug", "other")
                        matched_category = next((c for c in categories if c.slug == matched_slug), None)
                        if not matched_category and categories:
                            matched_category = categories[0]

                        # Format translation display if spoken in Hindi / Marathi
                        trans_html = ""
                        if trans_res.english_translation and trans_res.english_translation != trans_res.text:
                            trans_html = f"""<div style="font-size:0.86rem; color:#0369a1; margin-bottom:8px; background:#f0f9ff; padding:6px 10px; border-radius:6px; border:1px solid #bae6fd;"><b>🌐 English Translation:</b> "{trans_res.english_translation}"</div>"""

                        landmark_html = f"""<div style="color:#0369a1; margin-bottom:4px;">📍 <b>Extracted Landmark:</b> {parsed["landmark"]}</div>""" if parsed["landmark"] else ""
                        address_html = f"""<div style="color:#0369a1; margin-bottom:4px;">🏘️ <b>Extracted Sector/Address:</b> {parsed["address"]}</div>""" if parsed["address"] and parsed["address"] != settings.DEFAULT_CITY else ""

                        # 1-Click Review Card (Option 1 with Confirm & Next)
                        card_html = f"""<div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:10px; padding:14px; margin-top:10px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
<span style="font-weight:700; color:#15803d; font-size:0.95rem;">🗣️ Spoken Voice Note ({trans_res.language_name}):</span>
<span style="background:#dcfce7; color:#166534; font-size:0.75rem; padding:2px 8px; border-radius:12px; font-weight:600;">AI Structured</span>
</div>
<div style="font-style:italic; color:#166534; font-size:0.92rem; margin-bottom:8px; background:#ffffff; padding:10px 14px; border-radius:6px; border:1px solid #bbf7d0; line-height:1.5;">"{trans_res.text}"</div>
{trans_html}
<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; margin-bottom:10px; font-size:0.88rem;">
<div style="color:#0f2d6b; margin-bottom:4px;">📌 <b>Auto-Generated Title:</b> {parsed['title']}</div>
<div style="color:#334155; margin-bottom:4px;">📝 <b>Auto-Formatted Description:</b> {parsed['description']}</div>
{landmark_html}
{address_html}
<div style="display:flex; flex-wrap:wrap; gap:16px; margin-top:6px; color:#1e3a8a;">
<span>🎯 <b>Category:</b> {matched_category.icon if matched_category else '📌'} {matched_category.name if matched_category else 'Other'}</span>
<span>⚡ <b>Severity:</b> <b>{parsed['suggested_severity']}</b></span>
</div>
</div>
</div>"""
                        st.markdown(card_html, unsafe_allow_html=True)

                        st.write("")
                        col_conf, col_edit = st.columns([2, 1])
                        with col_conf:
                            if st.button("✨ Confirm & Next: Upload Evidence ➡️", type="primary", width="stretch", key="confirm_voice_btn"):
                                if matched_category:
                                    st.session_state.report_category_id = matched_category.id
                                    st.session_state.report_category_name = f"{matched_category.icon} {matched_category.name}"
                                    st.session_state.report_category_slug = matched_category.slug
                                    st.session_state.report_severity = parsed.get("suggested_severity", matched_category.default_severity)
                                st.session_state.report_title = parsed["title"]
                                st.session_state.report_description = parsed["description"]
                                if parsed.get("sector"):
                                    st.session_state.report_sector = parsed["sector"]
                                if parsed["landmark"]:
                                    st.session_state.report_landmark = parsed["landmark"]
                                if parsed["address"]:
                                    st.session_state.report_address = parsed["address"]
                                st.session_state.report_step = 3  # Advance directly to Step 3 (Media/Photos)
                                st.rerun()
                        with col_edit:
                            if st.button("📝 Edit Details First", width="stretch", key="edit_voice_btn"):
                                if matched_category:
                                    st.session_state.report_category_id = matched_category.id
                                    st.session_state.report_category_name = f"{matched_category.icon} {matched_category.name}"
                                    st.session_state.report_category_slug = matched_category.slug
                                    st.session_state.report_severity = parsed.get("suggested_severity", matched_category.default_severity)
                                st.session_state.report_title = parsed["title"]
                                st.session_state.report_description = parsed["description"]
                                if parsed.get("sector"):
                                    st.session_state.report_sector = parsed["sector"]
                                if parsed["landmark"]:
                                    st.session_state.report_landmark = parsed["landmark"]
                                if parsed["address"]:
                                    st.session_state.report_address = parsed["address"]
                                st.session_state.report_step = 2  # Advance to Step 2 (Edit Details)
                                st.rerun()
                    elif trans_res.message:
                        st.warning(f"🎙️ {trans_res.message}")



        st.markdown(
            """
            <div style="display:flex; align-items:center; margin: 1.2rem 0 0.8rem 0;">
                <div style="flex:1; height:1px; background:#cbd5e1;"></div>
                <span style="padding:0 12px; color:#64748b; font-size:0.85rem; font-weight:600; text-transform:uppercase;">
                    OR SELECT MANUALLY BELOW
                </span>
                <div style="flex:1; height:1px; background:#cbd5e1;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Category group mapping
    CATEGORY_GROUPS = {
        "🚰 Water & Sanitation": ["open-sewage", "water-leakage", "water-supply", "public-sanitation"],
        "🛣️ Roads & Infrastructure": ["pothole", "damaged-infrastructure"],
        "🗑️ Waste & Environment": ["garbage", "illegal-dumping", "flooding"],
        "💡 Utilities": ["streetlight", "drainage"],
        "📌 Other": ["other"],
    }

    # Search bar
    search_query = st.text_input(
        "🔍 Search Categories",
        placeholder="Type to filter... e.g. 'water', 'pothole', 'light'",
    )

    if not categories:
        st.warning("No complaint categories found. Please run the seed script.")
    else:
        # Filter by search query
        if search_query.strip():
            categories = [c for c in categories if search_query.lower() in c.name.lower() or search_query.lower() in (c.description or "").lower()]
            if not categories:
                st.info("No categories match your search. Try a different keyword or use **Other / Not Listed** below.")

        # Render categories grouped
        rendered_slugs = set()
        for group_name, slugs in CATEGORY_GROUPS.items():
            group_cats = [c for c in categories if c.slug in slugs and c.slug != "other"]
            if not group_cats:
                continue
            st.markdown(
                f"""
                <div style="margin: 1.1rem 0 0.5rem 0; display: flex; align-items: center; gap: 8px;">
                    <span style="font-family:'Rajdhani', sans-serif; font-weight:700; font-size:1.15rem; color:#0f2d6b; letter-spacing:0.02em;">
                        {group_name}
                    </span>
                    <div style="flex:1; height:1px; background:#cbd5e1; margin-left:8px;"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            for idx, cat in enumerate(group_cats):
                col = cols[idx % 3]
                rendered_slugs.add(cat.slug)
                with col:
                    is_selected = st.session_state.report_category_id == cat.id
                    btn_label = f"{cat.icon}  {cat.name}"
                    if is_selected:
                        btn_label = f"✅  {cat.icon}  {cat.name}"
                    if st.button(btn_label, key=f"cat_btn_{cat.id}", width="stretch",
                                 type="primary" if is_selected else "secondary"):
                        st.session_state.report_category_id = cat.id
                        st.session_state.report_category_name = f"{cat.icon} {cat.name}"
                        st.session_state.report_category_slug = cat.slug
                        st.session_state.report_severity = cat.default_severity
                        st.session_state.report_other_description = ""
                        st.session_state.report_step = 2
                        st.rerun()

        # Remaining ungrouped categories (not in any group)
        ungrouped = [c for c in categories if c.slug not in rendered_slugs and c.slug != "other"]
        if ungrouped:
            st.markdown(
                """
                <div style="margin: 1.1rem 0 0.5rem 0; display: flex; align-items: center; gap: 8px;">
                    <span style="font-family:'Rajdhani', sans-serif; font-weight:700; font-size:1.15rem; color:#0f2d6b; letter-spacing:0.02em;">
                        📋 Other Civic Issues
                    </span>
                    <div style="flex:1; height:1px; background:#cbd5e1; margin-left:8px;"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            for idx, cat in enumerate(ungrouped):
                col = cols[idx % 3]
                with col:
                    is_selected = st.session_state.report_category_id == cat.id
                    btn_label = f"{cat.icon}  {cat.name}"
                    if is_selected:
                        btn_label = f"✅  {cat.icon}  {cat.name}"
                    if st.button(btn_label, key=f"cat_btn_{cat.id}", width="stretch",
                                 type="primary" if is_selected else "secondary"):
                        st.session_state.report_category_id = cat.id
                        st.session_state.report_category_name = f"{cat.icon} {cat.name}"
                        st.session_state.report_category_slug = cat.slug
                        st.session_state.report_severity = cat.default_severity
                        st.session_state.report_other_description = ""
                        st.session_state.report_step = 2
                        st.rerun()

        st.divider()

        # ── OTHER / NOT LISTED ────────────────────────────────────────────────
        st.markdown("#### **PROBLEM NOT IN THE LIST ABOVE?**")
        st.caption("Use this section to describe any civic issue that doesn't fit the categories above.")

        with st.container(border=True):
            st.markdown("##### ✍️ Describe Your Problem Directly")


            other_problem_type = st.text_input(
                "Problem Type / Category Name *",
                placeholder="e.g. Broken park bench, Illegal parking, Damaged bus stop shelter",
                key="other_problem_type_input",
            )
            other_problem_desc = st.text_area(
                "Describe the Problem in Detail *",
                placeholder="Please describe what is wrong, where it is, how long it has been like this, and any safety risk it poses...",
                height=110,
                key="other_problem_desc_input",
            )
            other_severity = st.select_slider(
                "How urgent is this issue?",
                options=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                value="MEDIUM",
                key="other_severity_slider",
            )

            # Find the "other" category from the DB
            other_cat = next((c for c in categories if c.slug == "other"), None)
            if not other_cat:
                # fallback: pick any available category
                other_cat = categories[-1] if categories else None

            if st.button("➡️ Continue with Custom Problem", type="primary", width="content"):
                if not other_problem_type.strip():
                    st.error("Please enter a short name for the problem type.")
                elif len(other_problem_desc.strip()) < 10:
                    st.error("Please describe the problem in at least 10 characters.")
                elif other_cat:
                    st.session_state.report_category_id = other_cat.id
                    st.session_state.report_category_name = f"📌 Other — {other_problem_type.strip()}"
                    st.session_state.report_category_slug = "other"
                    st.session_state.report_severity = other_severity
                    st.session_state.report_title = other_problem_type.strip()
                    st.session_state.report_description = other_problem_desc.strip()
                    st.session_state.report_step = 3  # Skip to media since title+desc are filled
                    st.rerun()
                else:
                    st.error("No categories available. Please contact support.")


# -----------------------------------------------------------------------------
# STEP 2: DESCRIBE THE PROBLEM
# -----------------------------------------------------------------------------
elif st.session_state.report_step == 2:
    st.markdown(f"### 📝 **Step 2: Describe the Problem**")
    st.info(f"Selected Category: **{st.session_state.report_category_name}**")

    # Optional AI Assistant Helper
    ai_col1, ai_col2 = st.columns([3, 1])
    with ai_col1:
        title_val = st.text_input(
            "Complaint Title *",
            value=st.session_state.report_title,
            placeholder="e.g. Deep pothole causing accidents near Sony World Signal",
        )
    with ai_col2:
        severity_options = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        sev_idx = severity_options.index(st.session_state.report_severity) if st.session_state.report_severity in severity_options else 1
        severity_val = st.selectbox("Severity Level *", severity_options, index=sev_idx)

    desc_val = st.text_area(
        "Short Description *",
        value=st.session_state.report_description,
        placeholder="Provide a brief explanation of the problem, duration, or any safety hazard...",
        height=120,
    )

    landmark_val = st.text_input(
        "Landmark / Specific Spot (Optional)",
        value=st.session_state.report_landmark,
        placeholder="e.g. In front of Pillar 42, near HDFC ATM",
    )

    # AI Suggestion button
    if title_val and desc_val:
        if st.button("✨ Run AI Assistant (Severity & Summary Check)", type="secondary"):
            ai_service = AIService()
            sugg = ai_service.get_suggestions(title_val, desc_val, landmark_val)
            st.success(f"🤖 **AI Recommendation**: Severity: `{sugg['suggested_severity']}` | Summary: *{sugg['summary_text']}*")
            if sugg["suggested_severity"] in severity_options:
                st.session_state.report_severity = sugg["suggested_severity"]

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅️ Back to Category", width="stretch"):
            st.session_state.report_step = 1
            st.rerun()
    with col_next:
        if st.button("Next: Upload Photos / Videos ➡️", type="primary", width="stretch"):
            if len(title_val.strip()) < 5:
                st.error("Please enter a clear title (at least 5 characters).")
            elif len(desc_val.strip()) < 10:
                st.error("Please enter a short description (at least 10 characters).")
            else:
                st.session_state.report_title = title_val
                st.session_state.report_description = desc_val
                st.session_state.report_severity = severity_val
                st.session_state.report_landmark = landmark_val
                st.session_state.report_step = 3
                st.rerun()

# -----------------------------------------------------------------------------
# STEP 3: PHOTO AND VIDEO UPLOADS
# -----------------------------------------------------------------------------
elif st.session_state.report_step == 3:
    st.markdown("### 📸 **Step 3: Photo and Video Evidence**")
    st.caption("Visual proof helps field engineers diagnose and dispatch the right repair equipment quickly.")

    tab_upload, tab_camera = st.tabs(["📁 Upload Files (Photos/Videos)", "📷 Take Live Photo"])

    storage = get_storage_provider()

    with tab_upload:
        uploaded_files = st.file_uploader(
            "Choose Photos (JPG, PNG, WEBP) or Videos (MP4, WEBM)",
            type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "webm"],
            accept_multiple_files=True,
            help="Maximum 50MB per file. Only safe, validated images and videos are stored.",
        )

        if uploaded_files:
            new_metas = []
            for f in uploaded_files:
                file_bytes = f.read()
                try:
                    meta = storage.save_file(
                        file_bytes=file_bytes,
                        original_filename=f.name,
                        content_type=f.type,
                    )
                    new_metas.append(meta)
                    st.success(f"✅ Uploaded: `{f.name}` ({meta['media_type'].upper()})")
                except Exception as e:
                    st.error(f"❌ Upload failed for {f.name}: {e}")
            if new_metas:
                st.session_state.uploaded_media_meta = new_metas

    with tab_camera:
        camera_img = st.camera_input("Capture Photo with Device Camera")
        if camera_img:
            img_bytes = camera_img.read()
            try:
                meta = storage.save_file(
                    file_bytes=img_bytes,
                    original_filename="camera_capture.jpg",
                    content_type="image/jpeg",
                )
                st.session_state.uploaded_media_meta.append(meta)
                st.success("✅ Camera photo captured and saved!")
            except Exception as e:
                st.error(f"Capture upload error: {e}")

    # Show count of currently attached media & YOLO Vision Verification
    count = len(st.session_state.uploaded_media_meta)
    if count > 0:
        st.info(f"📎 **{count}** media file(s) attached.")

        # YOLO Vision AI Inspection Block (Only for Pothole & Road Surface category)
        is_pothole_cat = (
            st.session_state.get("report_category_slug") == "pothole"
            or "pothole" in (st.session_state.get("report_category_name") or "").lower()
        )

        if settings.YOLO_ENABLED and is_pothole_cat:
            with st.expander("🤖 **AI Vision Inspection (YOLO Pothole Detector)**", expanded=True):
                detector = YOLOPotholeDetector()
                has_image = any(m.get("media_type") == "image" for m in st.session_state.uploaded_media_meta)

                if has_image:
                    for idx, meta in enumerate(st.session_state.uploaded_media_meta):
                        if meta.get("media_type") == "image":
                            file_path = storage.get_file_path(meta["storage_path"])
                            if file_path and os.path.exists(file_path):
                                with open(file_path, "rb") as f:
                                    img_data = f.read()

                                vision_res = detector.detect_potholes(img_data)
                                if vision_res.potholes_detected:
                                    st.success(
                                        f"🎯 **YOLO Model Verified**: Detected **{vision_res.pothole_count} Pothole(s)** "
                                        f"(Confidence: `{int(vision_res.max_confidence * 100)}%`) in `{meta.get('original_filename', 'photo')}`"
                                    )
                                    if vision_res.annotated_image_bytes:
                                        st.image(
                                            vision_res.annotated_image_bytes,
                                            caption=f"🎯 AI Bounding Box Detection - {vision_res.pothole_count} Pothole(s) Identified",
                                            width="stretch",
                                        )
                                    # Auto-suggest severity if higher
                                    if vision_res.suggested_severity in ["HIGH", "CRITICAL"] and st.session_state.report_severity != "CRITICAL":
                                        st.session_state.report_severity = vision_res.suggested_severity
                                        st.info(f"⚡ Severity automatically upgraded to **{vision_res.suggested_severity}** based on road hazard density.")
                                elif vision_res.is_loaded:
                                    st.caption(f"ℹ️ `{meta.get('original_filename', 'photo')}`: No road potholes detected by Vision model.")
                                else:
                                    st.caption(f"💡 Vision Model Status: {vision_res.message}")

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅️ Back to Details", width="stretch"):
            st.session_state.report_step = 2
            st.rerun()
    with col_next:
        if st.button("Next: Set Location ➡️", type="primary", width="stretch"):
            st.session_state.report_step = 4
            st.rerun()

# -----------------------------------------------------------------------------
# STEP 4: LOCATION & INTERACTIVE MAP
# -----------------------------------------------------------------------------
elif st.session_state.report_step == 4:
    st.markdown("### 📍 **Step 4: Location & Map**")
    st.caption("Click on the map or type an address to pin the exact problem location.")

    loc_service = LocationService()

    with get_db_session() as session:
        ward_repo = WardRepository(session)
        wards = ward_repo.get_all(active_only=True)

    c_lat, c_lng = st.session_state.report_lat, st.session_state.report_lng

    # Quick Ward Selector to focus location across all wards of Maharashtra & BMC
    ward_options = {f"[{w.city}] {w.name} ({w.zone})": w for w in wards}
    selected_ward_label = st.selectbox(
        "Quick Focus on Ward / Municipal Locality (All Maharashtra & Mumbai Wards)",
        options=["(Current Map Center)"] + list(ward_options.keys()),
    )

    if selected_ward_label in ward_options:
        w_obj = ward_options[selected_ward_label]
        if w_obj.center_latitude and w_obj.center_longitude:
            c_lat = w_obj.center_latitude
            c_lng = w_obj.center_longitude
            st.session_state.report_lat = c_lat
            st.session_state.report_lng = c_lng
            st.session_state.report_ward_id = w_obj.id

    # Interactive Folium Map centered on Maharashtra / Mumbai
    m = folium.Map(
        location=[c_lat, c_lng],
        zoom_start=12,
        min_zoom=5,
        max_zoom=18,
        tiles="CartoDB positron",
    )
    add_maharashtra_boundary_layer(m)
    add_india_boundary_layer(m)
    folium.Marker(
        [c_lat, c_lng],
        popup=f"Pinned Location ({c_lat:.4f}, {c_lng:.4f})",
        tooltip="Complaint Location",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    map_output = st_folium(m, height=350, width=None, key=f"rep_map_{st.session_state.report_step}")

    # If citizen clicks map, update coordinates
    if map_output and map_output.get("last_clicked"):
        clicked_lat = map_output["last_clicked"]["lat"]
        clicked_lng = map_output["last_clicked"]["lng"]
        st.session_state.report_lat = clicked_lat
        st.session_state.report_lng = clicked_lng
        c_lat, c_lng = clicked_lat, clicked_lng

        # Reverse geocode address automatically
        rev = loc_service.reverse_geocode(c_lat, c_lng)
        rev_addr = rev["address"]
        sec = st.session_state.get("report_sector", "")
        if sec and sec.lower() not in rev_addr.lower():
            rev_addr = f"{sec}, {rev_addr}"
        st.session_state.report_address = rev_addr

        # Nearest ward
        nearest_w = loc_service.find_nearest_ward(c_lat, c_lng, wards)
        if nearest_w:
            st.session_state.report_ward_id = nearest_w.id

    # Fine-tune coordinates & Address
    coord_col1, coord_col2 = st.columns(2)
    with coord_col1:
        st.write(f"📌 **Selected Coordinates:** `{c_lat:.5f}, {c_lng:.5f}`")
    with coord_col2:
        with st.popover("⚙️ Fine-Tune Coordinates Manually"):
            man_lat = st.number_input("Latitude", value=float(c_lat), format="%.5f")
            man_lng = st.number_input("Longitude", value=float(c_lng), format="%.5f")
            if st.button("Apply Coordinates"):
                st.session_state.report_lat = man_lat
                st.session_state.report_lng = man_lng
                c_lat, c_lng = man_lat, man_lng
                rev = loc_service.reverse_geocode(c_lat, c_lng)
                rev_addr = rev["address"]
                sec = st.session_state.get("report_sector", "")
                if sec and sec.lower() not in rev_addr.lower():
                    rev_addr = f"{sec}, {rev_addr}"
                st.session_state.report_address = rev_addr
                st.rerun()

    if not is_in_maharashtra(loc_service, c_lat, c_lng):
        st.warning("⚠️ The selected location is outside the State of Maharashtra municipal jurisdiction. Please select a location within Maharashtra.")

    # Address field
    curr_addr = st.session_state.report_address
    sec = st.session_state.get("report_sector", "")
    if sec and sec.lower() not in (curr_addr or "").lower():
        curr_addr = f"{sec}, {curr_addr}" if curr_addr else f"{sec}, {settings.DEFAULT_CITY}"
        st.session_state.report_address = curr_addr

    addr_val = st.text_input(
        "Street Address / Locality",
        value=st.session_state.report_address or f"Near coordinates {c_lat:.4f}, {c_lng:.4f}, {settings.DEFAULT_CITY}",
    )
    st.session_state.report_address = addr_val

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅️ Back to Media", width="stretch"):
            st.session_state.report_step = 3
            st.rerun()
    with col_next:
        if st.button("Next: Review & Submit ➡️", type="primary", width="stretch"):
            st.session_state.report_step = 5
            st.rerun()

# -----------------------------------------------------------------------------
# STEP 5: REVIEW, DUPLICATE CHECK & SUBMISSION
# -----------------------------------------------------------------------------
elif st.session_state.report_step == 5:
    st.markdown("### 📋 **Step 5: Review & Confirm Submission**")

    # 1. Proactive Duplicate Check
    with get_db_session() as session:
        comp_service = ComplaintService(session)
        duplicates = comp_service.check_for_duplicates(
            category_id=st.session_state.report_category_id,
            latitude=st.session_state.report_lat,
            longitude=st.session_state.report_lng,
            title=st.session_state.report_title,
            description=st.session_state.report_description,
        )

    if duplicates:
        st.warning("⚠️ **Notice: An existing grievance was recently reported nearby.**")
        for dup in duplicates:
            st.markdown(
                f"""
                <div style="background:#FEF3C7; border:1px solid #FCD34D; border-radius:6px; padding:10px; margin-bottom:8px;">
                    <strong>{dup['complaint_number']}</strong> - {dup['title']}<br>
                    <span style="font-size:0.85rem; color:#92400E;">Distance: ~{dup['distance_meters']}m away | Status: <b>{dup['status']}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption("You may still proceed with submitting your grievance if it is a distinct issue.")

    # 2. Review Card
    st.markdown(
        f"""
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:16px; margin-bottom:16px;">
            <h4>{st.session_state.report_title}</h4>
            <p style="color:#4B5563; font-size:0.95rem;">{st.session_state.report_description}</p>
            <hr style="margin:10px 0; border:0; border-top:1px solid #E2E8F0;">
            <div style="display:flex; flex-wrap:wrap; gap:16px; font-size:0.88rem;">
                <div>🏷️ <b>Category:</b> {st.session_state.report_category_name}</div>
                <div>⚡ <b>Severity:</b> <span class="badge-critical">{st.session_state.report_severity}</span></div>
                <div>📍 <b>Address:</b> {st.session_state.report_address}</div>
                <div>📌 <b>Landmark:</b> {st.session_state.report_landmark or 'N/A'}</div>
                <div>📎 <b>Media Attachments:</b> {len(st.session_state.uploaded_media_meta)} file(s)</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Citizen Contact Details (if guest, ask for name & phone)
    user = get_current_user()
    citizen_id = user["user_id"] if user else None

    if not is_logged_in():
        st.markdown("#### 👤 **Your Contact Information**")
        c_name = st.text_input("Your Full Name *", placeholder="e.g. Rahul Sharma")
        c_phone = st.text_input("Mobile Phone Number *", placeholder="+91 98800 12345")
        c_email = st.text_input("Email (for status tracking) *", placeholder="rahul@example.com")
    else:
        st.success(f"Logged in as **{user['full_name']}** (`{user['email']}`)")

    col_edit, col_submit = st.columns([1, 2])
    with col_edit:
        if st.button("✏️ Edit Complaint", width="stretch"):
            st.session_state.report_step = 2
            st.rerun()

    with col_submit:
        if st.button("🚀 Submit Grievance", type="primary", width="stretch"):
            # If guest, create or find citizen user
            with get_db_session() as session:
                user_repo = UserRepository(session)
                comp_service = ComplaintService(session)

                if not citizen_id:
                    if not c_name or not c_email:
                        st.error("Please provide your name and email to proceed.")
                        st.stop()

                    guest_user = user_repo.get_by_email(c_email)
                    if not guest_user:
                        from backend.utils.security import hash_password

                        guest_user = user_repo.create_user(
                            email=c_email,
                            full_name=c_name,
                            phone=c_phone,
                            hashed_password=hash_password("Citizen@123"),
                        )
                    citizen_id = guest_user.id

                # Prepare media schema list
                media_schemas = [
                    MediaUploadMetaSchema(
                        file_name=m["file_name"],
                        original_filename=m["original_filename"],
                        file_size_bytes=m["file_size_bytes"],
                        mime_type=m["mime_type"],
                        storage_provider=m["storage_provider"],
                        storage_path=m["storage_path"],
                        file_hash=m.get("file_hash"),
                        media_type=m.get("media_type", "image"),
                    )
                    for m in st.session_state.uploaded_media_meta
                ]

                # Create complaint payload
                payload = ComplaintCreateSchema(
                    category_id=st.session_state.report_category_id,
                    title=st.session_state.report_title,
                    description=st.session_state.report_description,
                    severity=ComplaintSeverity(st.session_state.report_severity),
                    landmark=st.session_state.report_landmark,
                    ward_id=st.session_state.report_ward_id,
                    location=LocationCreateSchema(
                        latitude=st.session_state.report_lat,
                        longitude=st.session_state.report_lng,
                        address=st.session_state.report_address,
                        landmark=st.session_state.report_landmark,
                        city=settings.DEFAULT_CITY,
                    ),
                    media_files=media_schemas,
                )

                try:
                    created = comp_service.submit_complaint(citizen_id=citizen_id, data=payload)
                    session.commit()
                    st.session_state.submitted_complaint_number = created.complaint_number
                    st.session_state.search_complaint_num = created.complaint_number
                    st.session_state.report_step = 6
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Failed to submit complaint: {e}")

# -----------------------------------------------------------------------------
# STEP 6: SUBMISSION SUCCESS SCREEN
# -----------------------------------------------------------------------------
elif st.session_state.report_step == 6:
    comp_num = st.session_state.submitted_complaint_number
    st.balloons()

    st.markdown(
        f"""
        <div style="background:#ECFDF5; border:2px solid #10B981; border-radius:12px; padding:24px; text-align:center; margin-bottom:20px;">
            <h2 style="color:#065F46; margin:0 0 10px 0;">🎉 Complaint Submitted Successfully!</h2>
            <p style="color:#047857; font-size:1.1rem;">Your unique Complaint ID is:</p>
            <div style="background:#FFFFFF; border:2px dashed #059669; border-radius:8px; display:inline-block; padding:10px 24px; font-size:1.6rem; font-weight:bold; color:#065F46; letter-spacing:1px; margin-bottom:12px;">
                {comp_num}
            </div>
            <p style="color:#4B5563; font-size:0.9rem;">The responsible municipal department and local ward engineer have been notified.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 Track This Complaint Now", type="primary", width="stretch"):
            st.session_state.search_complaint_num = comp_num
            st.switch_page("pages/03_Track_Complaint.py")
    with c2:
        if st.button("📢 File Another Complaint", width="stretch"):
            # Reset wizard
            st.session_state.report_step = 1
            st.session_state.report_title = ""
            st.session_state.report_description = ""
            st.session_state.uploaded_media_meta = []
            st.session_state.submitted_complaint_number = None
            st.rerun()
