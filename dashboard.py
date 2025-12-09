import streamlit as st
import requests
from PIL import Image
import cv2
import tempfile
import base64
import io
import pandas as pd
from fpdf import FPDF
import os  # <--- THIS IS REQUIRED

# --- CONFIG ---
st.set_page_config(page_title="CleaRoute Pro", layout="wide")

# INTELLIGENT URL SWITCHER
# If we are on Render, use the Cloud URL.
# If we are on Laptop, use Localhost.
BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Remove trailing slash if it exists (prevents double // errors)
if BASE_URL.endswith("/"):
    BASE_URL = BASE_URL[:-1]

API_URL = f"{BASE_URL}/analyze"
HISTORY_URL = f"{BASE_URL}/history"
CLEAR_URL = f"{BASE_URL}/clear_history"

st.title("🚧 CleaRoute: Intelligent Road Monitoring System")
# ... (Leave the rest of the code as it is) ... 

# --- HELPER FUNCTIONS ---
def decode_image(base64_string):
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))

def calculate_unique_potholes(df):
    """
    Smart Logic: Counts new potholes by looking for increases in detection numbers.
    """
    if df.empty: return 0
    df = df.copy()
    # Calculate difference between frames
    df['diff'] = df['potholes'].diff().fillna(df['potholes'].iloc[0])
    # Sum only the positive spikes (new objects entering frame)
    unique_count = df[df['diff'] > 0]['diff'].sum()
    return int(unique_count)

def generate_pdf(dataframe, source_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, txt=f"Official Road Audit: {source_name}", ln=True, align='C')
    pdf.ln(10)
    
    # Smart Stats
    unique_defects = calculate_unique_potholes(dataframe)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"Est. Unique Defects: {unique_defects}", ln=True)
    pdf.cell(0, 10, txt=f"Frames Scanned: {len(dataframe)}", ln=True)
    pdf.cell(0, 10, txt=f"Audit Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(60, 10, "Timestamp", 1)
    pdf.cell(40, 10, "Visible Count", 1)
    pdf.cell(50, 10, "Status", 1)
    pdf.ln()
    
    # Table Rows
    pdf.set_font("Arial", size=12)
    for index, row in dataframe.iterrows():
        ts = str(row['time'])
        status_text = str(row['status'])
        pdf.cell(60, 10, ts, 1)
        pdf.cell(40, 10, str(row['potholes']), 1)
        pdf.cell(50, 10, status_text, 1)
        pdf.ln()
        
    return pdf.output(dest="S").encode("latin-1")

# --- TABS ---
tab1, tab2 = st.tabs(["🔴 Live Surveillance", "📊 Intelligence & Reports"])

# ==========================
# TAB 1: LIVE SURVEILLANCE
# ==========================
with tab1:
    col_head, col_logo = st.columns([4,1])
    with col_head: st.markdown("### CCTV Control Room")
    
    source_type = st.radio("Select Feed:", ["Upload Image", "CCTV Simulation"], horizontal=True)

    if source_type == "Upload Image":
        uploaded_file = st.file_uploader("Upload Snapshot...", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            col1, col2 = st.columns(2)
            with st.spinner("AI Analyzing..."):
                files = {"file": uploaded_file.getvalue()}
                data_payload = {"source_name": uploaded_file.name}
                response = requests.post(API_URL, files=files, data=data_payload, timeout=120)
                data = response.json()
                
                with col1:
                    st.image(decode_image(data["image_base64"]), caption=f"Source: {uploaded_file.name}", use_column_width=True)
                with col2:
                    st.metric("Defects Found", data["potholes_found"])
                    if data["potholes_found"] > 0:
                        st.error(f"🛑 Assessment: {data['road_quality']}")
                    else:
                        st.success(f"✅ Assessment: {data['road_quality']}")

    elif source_type == "CCTV Simulation":
        video_file = st.file_uploader("Upload Footage (MP4)...", type=['mp4'])
        
        if video_file:
            st.info(f"Loaded: {video_file.name}. System Standby.")
            
            # THE START BUTTON (Prevents auto-run loops)
            if st.button("▶️ ACTIVATE AI STREAM"):
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(video_file.read())
                cap = cv2.VideoCapture(tfile.name)
                
                col1, col2 = st.columns([2, 1])
                with col1: stframe = st.empty()
                with col2: 
                    kpi1 = st.empty()
                    kpi2 = st.empty()
                    st.success("System: ONLINE")
                
                # Tracking variables
                prev_count = 0
                unique_potholes_total = 0
                frame_count = 0
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    
                    frame_count += 1
                    # Analyze every 30th frame (1 FPS) for stability
                    if frame_count % 30 == 0:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(frame_rgb)
                        img_byte_arr = io.BytesIO()
                        pil_image.save(img_byte_arr, format='JPEG')
                        
                        try:
                            files = {"file": img_byte_arr.getvalue()}
                            data_payload = {"source_name": f"CCTV: {video_file.name}"}
                            
                            response = requests.post(API_URL, files=files, data=data_payload)
                            data = response.json()
                            
                            # Update Video Feed
                            stframe.image(decode_image(data["image_base64"]), use_column_width=True)
                            
                            # Smart Counting Logic
                            current_visible = data["potholes_found"]
                            if current_visible > prev_count:
                                diff = current_visible - prev_count
                                unique_potholes_total += diff
                            prev_count = current_visible
                            
                            # Live KPIs
                            if current_visible > 0: kpi1.error(f"⚠️ {current_visible} Defects Visible")
                            else: kpi1.success("✅ Road Clear")
                            
                            kpi2.metric("Total Unique Defects", unique_potholes_total)
                        except: pass
                
                cap.release()
                st.toast("Analysis Session Complete.", icon="💾")

# ==========================
# TAB 2: INTELLIGENCE & REPORTS
# ==========================
with tab2:
    col_header, col_btn = st.columns([4,1])
    with col_header: st.markdown("### 📈 Source-Wise Analytics")
    with col_btn:
        if st.button("🗑️ Reset Database"):
            requests.delete(CLEAR_URL)
            st.rerun()

    try:
        response = requests.get(HISTORY_URL)
        history_data = response.json()
        
        if history_data:
            df = pd.DataFrame(history_data)
            unique_sources = df['source'].unique()
            
            if len(unique_sources) > 0:
                # Create tabs for each video source
                source_tabs = st.tabs(list(unique_sources))
                
                for source, tab in zip(unique_sources, source_tabs):
                    with tab:
                        subset = df[df['source'] == source]
                        
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.subheader(f"Defect Density: {source}")
                            subset['time'] = pd.to_datetime(subset['time']).dt.strftime('%H:%M:%S')
                            st.line_chart(subset.set_index('time')['potholes'])
                        
                        with c2:
                            st.markdown("#### Audit Summary")
                            smart_total = calculate_unique_potholes(subset)
                            st.metric("Unique Defects Identified", smart_total)
                            
                            # PDF Download
                            pdf_data = generate_pdf(subset, source)
                            st.download_button(
                                label="📄 Download Official PDF",
                                data=pdf_data,
                                file_name=f"Audit_{source}.pdf",
                                mime="application/pdf"
                            )
                        
                        st.dataframe(subset, use_container_width=True)
            else:
                st.info("No audit data found.")
        else:
            st.info("System Ready. No data in database.")
            
    except Exception as e:
        st.error(f"Connection Error: {e}")