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
from backend.services.storage_service import get_storage_provider
from backend.services.location_service import LocationService
from backend.services.ai_service import AIService
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.ward_repo import WardRepository
from backend.repositories.user_repo import UserRepository
from backend.utils.session import init_session_state, get_current_user, is_logged_in, apply_custom_css

init_session_state()
apply_custom_css()

st.markdown('<h1 class="main-header">📢 Report a Civic Problem</h1>', unsafe_allow_html=True)
st.caption("Help local authorities resolve issues in your neighborhood in ~2 minutes.")

# Ensure session state variables for wizard
if "report_step" not in st.session_state:
    st.session_state.report_step = 1
if "report_category_id" not in st.session_state:
    st.session_state.report_category_id = None
if "report_category_name" not in st.session_state:
    st.session_state.report_category_name = None
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
if "report_ward_id" not in st.session_state:
    st.session_state.report_ward_id = None
if "uploaded_media_meta" not in st.session_state:
    st.session_state.uploaded_media_meta = []
if "submitted_complaint_number" not in st.session_state:
    st.session_state.submitted_complaint_number = None

# Step indicator progress bar
step_names = ["1. Category", "2. Details", "3. Photos / Video", "4. Location", "5. Review & Submit"]
curr_step = st.session_state.report_step

if curr_step <= 5:
    st.progress(curr_step / 5, text=f"Step {curr_step} of 5: {step_names[curr_step - 1]}")
    st.write("")

# -----------------------------------------------------------------------------
# STEP 1: SELECT CATEGORY
# -----------------------------------------------------------------------------
if st.session_state.report_step == 1:
    st.markdown("### 🗂️ **Step 1: Select Problem Category**")

    with get_db_session() as session:
        cat_repo = CategoryRepository(session)
        categories = cat_repo.get_all(active_only=True)

        if not categories:
            st.warning("No complaint categories found. Please run the seed script.")
        else:
            # Render clean grid of selectable category cards
            cols = st.columns(3)
            for idx, cat in enumerate(categories):
                col = cols[idx % 3]
                with col:
                    is_selected = st.session_state.report_category_id == cat.id
                    btn_label = f"{cat.icon} {cat.name}"
                    if is_selected:
                        btn_label = f"👉 {cat.icon} **{cat.name}**"

                    if st.button(btn_label, key=f"cat_btn_{cat.id}", use_container_width=True):
                        st.session_state.report_category_id = cat.id
                        st.session_state.report_category_name = f"{cat.icon} {cat.name}"
                        st.session_state.report_severity = cat.default_severity
                        st.session_state.report_step = 2
                        st.rerun()

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
        if st.button("⬅️ Back to Category", use_container_width=True):
            st.session_state.report_step = 1
            st.rerun()
    with col_next:
        if st.button("Next: Upload Photos / Videos ➡️", type="primary", use_container_width=True):
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

    # Show count of currently attached media
    count = len(st.session_state.uploaded_media_meta)
    if count > 0:
        st.info(f"📎 **{count}** media file(s) attached.")

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅️ Back to Details", use_container_width=True):
            st.session_state.report_step = 2
            st.rerun()
    with col_next:
        if st.button("Next: Set Location ➡️", type="primary", use_container_width=True):
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

    # Quick Ward Selector to center map
    ward_options = {w.name: w for w in wards}
    selected_ward_name = st.selectbox(
        "Quick Focus on Ward / Locality",
        options=["(Current Map Center)"] + list(ward_options.keys()),
    )

    if selected_ward_name in ward_options:
        w_obj = ward_options[selected_ward_name]
        if w_obj.center_latitude and w_obj.center_longitude:
            c_lat = w_obj.center_latitude
            c_lng = w_obj.center_longitude
            st.session_state.report_lat = c_lat
            st.session_state.report_lng = c_lng
            st.session_state.report_ward_id = w_obj.id

    # Interactive Folium Map
    m = folium.Map(location=[c_lat, c_lng], zoom_start=14)
    folium.Marker(
        [c_lat, c_lng],
        popup="Pinned Location",
        tooltip="Complaint Location",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    map_output = st_folium(m, height=350, width=None)

    # If citizen clicks map, update coordinates
    if map_output and map_output.get("last_clicked"):
        clicked_lat = map_output["last_clicked"]["lat"]
        clicked_lng = map_output["last_clicked"]["lng"]
        st.session_state.report_lat = clicked_lat
        st.session_state.report_lng = clicked_lng
        c_lat, c_lng = clicked_lat, clicked_lng

        # Reverse geocode address automatically
        rev = loc_service.reverse_geocode(c_lat, c_lng)
        st.session_state.report_address = rev["address"]

        # Nearest ward
        nearest_w = loc_service.find_nearest_ward(c_lat, c_lng, wards)
        if nearest_w:
            st.session_state.report_ward_id = nearest_w.id

    st.write(f"📌 **Selected Coordinates:** `{c_lat:.5f}, {c_lng:.5f}`")

    # Address field
    addr_val = st.text_input(
        "Street Address / Locality",
        value=st.session_state.report_address or f"Near coordinates {c_lat:.4f}, {c_lng:.4f}, {settings.DEFAULT_CITY}",
    )
    st.session_state.report_address = addr_val

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅️ Back to Media", use_container_width=True):
            st.session_state.report_step = 3
            st.rerun()
    with col_next:
        if st.button("Next: Review & Submit ➡️", type="primary", use_container_width=True):
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
        if st.button("✏️ Edit Complaint", use_container_width=True):
            st.session_state.report_step = 2
            st.rerun()

    with col_submit:
        if st.button("🚀 Submit Grievance", type="primary", use_container_width=True):
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
        if st.button("🔍 Track This Complaint Now", type="primary", use_container_width=True):
            st.session_state.search_complaint_num = comp_num
            st.switch_page("pages/03_Track_Complaint.py")
    with c2:
        if st.button("📢 File Another Complaint", use_container_width=True):
            # Reset wizard
            st.session_state.report_step = 1
            st.session_state.report_title = ""
            st.session_state.report_description = ""
            st.session_state.uploaded_media_meta = []
            st.session_state.submitted_complaint_number = None
            st.rerun()
