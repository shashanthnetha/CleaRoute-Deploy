import streamlit as st
import requests
from PIL import Image
import cv2
import tempfile
import base64
import io
import pandas as pd
from fpdf import FPDF

# --- CONFIG FOR LOCALHOST ---
st.set_page_config(page_title="CleaRoute Pro", layout="wide")

# Force connection to Local Server
API_URL = "http://127.0.0.1:8000/analyze"
HISTORY_URL = "http://127.0.0.1:8000/history"
CLEAR_URL = "http://127.0.0.1:8000/clear_history"

st.title("🚧 CleaRoute Pro: Local Infrastructure Monitor")

# --- HELPER FUNCTIONS ---
def decode_image(base64_string):
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))

def calculate_unique_potholes(df):
    """Counts unique potholes by tracking positive increases in detection."""
    if df.empty: return 0
    df = df.copy()
    df['diff'] = df['potholes'].diff().fillna(df['potholes'].iloc[0])
    unique_count = df[df['diff'] > 0]['diff'].sum()
    return int(unique_count)

def generate_pdf(dataframe, source_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, txt=f"Audit Report: {source_name}", ln=True, align='C')
    pdf.ln(10)
    
    # Stats
    unique_defects = calculate_unique_potholes(dataframe)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"Unique Defects: {unique_defects}", ln=True)
    pdf.cell(0, 10, txt=f"Frames Analyzed: {len(dataframe)}", ln=True)
    pdf.cell(0, 10, txt=f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    
    # Table
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(60, 10, "Timestamp", 1)
    pdf.cell(40, 10, "Visible", 1)
    pdf.cell(50, 10, "Status", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=12)
    for index, row in dataframe.iterrows():
        ts = str(row['time'])
        status_text = str(row['status'])
        pdf.cell(60, 10, ts, 1)
        pdf.cell(40, 10, str(row['potholes']), 1)
        pdf.cell(50, 10, status_text, 1)
        pdf.ln()
        
    return pdf.output(dest="S").encode("latin-1")

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["🔴 Live Surveillance", "📊 Analytics & Report"])

# TAB 1: LIVE
with tab1:
    st.markdown("### CCTV Control Room (Local)")
    source_type = st.radio("Input Source:", ["Upload Image", "CCTV Simulation"], horizontal=True)

    if source_type == "Upload Image":
        uploaded_file = st.file_uploader("Upload Image...", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            col1, col2 = st.columns(2)
            with st.spinner("Analyzing..."):
                try:
                    files = {"file": uploaded_file.getvalue()}
                    data_payload = {"source_name": uploaded_file.name}
                    response = requests.post(API_URL, files=files, data=data_payload)
                    data = response.json()
                    
                    with col1:
                        st.image(decode_image(data["image_base64"]), caption="Analysis Result", use_column_width=True)
                    with col2:
                        st.metric("Potholes Detected", data["potholes_found"])
                        if data["potholes_found"] > 0:
                            st.error("🛑 Bad Road Condition")
                        else:
                            st.success("✅ Good Road Condition")
                except Exception as e:
                    st.error(f"Server Error: {e}")

    elif source_type == "CCTV Simulation":
        video_file = st.file_uploader("Upload Video (MP4)...", type=['mp4'])
        
        if video_file:
            if st.button("▶️ START ANALYSIS"):
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(video_file.read())
                cap = cv2.VideoCapture(tfile.name)
                
                col1, col2 = st.columns([2, 1])
                with col1: stframe = st.empty()
                with col2: 
                    kpi1 = st.empty()
                    kpi2 = st.empty()
                
                prev_count = 0
                unique_total = 0
                frame_count = 0
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    
                    frame_count += 1
                    # Analyze every 5th frame locally (we can go faster on localhost!)
                    if frame_count % 5 == 0:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(frame_rgb)
                        img_byte_arr = io.BytesIO()
                        pil_image.save(img_byte_arr, format='JPEG')
                        
                        try:
                            files = {"file": img_byte_arr.getvalue()}
                            data_payload = {"source_name": f"CCTV: {video_file.name}"}
                            
                            response = requests.post(API_URL, files=files, data=data_payload)
                            data = response.json()
                            
                            stframe.image(decode_image(data["image_base64"]), use_column_width=True)
                            
                            curr = data["potholes_found"]
                            if curr > prev_count:
                                unique_total += (curr - prev_count)
                            prev_count = curr
                            
                            if curr > 0: kpi1.error(f"⚠️ Defects: {curr}")
                            else: kpi1.success("✅ Clear")
                            kpi2.metric("Total Unique", unique_total)
                        except: pass
                cap.release()
                st.success("Analysis Complete")

# TAB 2: REPORTS
with tab2:
    col_h, col_b = st.columns([4,1])
    with col_h: st.markdown("### 📈 Audit History")
    with col_b: 
        if st.button("🗑️ Clear Data"):
            requests.delete(CLEAR_URL)
            st.rerun()

    try:
        response = requests.get(HISTORY_URL)
        history_data = response.json()
        
        if history_data:
            df = pd.DataFrame(history_data)
            sources = df['source'].unique()
            
            tabs = st.tabs(list(sources))
            for src, tab in zip(sources, tabs):
                with tab:
                    sub = df[df['source'] == src]
                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        st.subheader("Detection Timeline")
                        st.line_chart(sub.set_index('time')['potholes'])
                    with c2:
                        st.markdown("#### Summary")
                        unique_val = calculate_unique_potholes(sub)
                        st.metric("Unique Defects", unique_val)
                        
                        pdf = generate_pdf(sub, src)
                        st.download_button("📄 Download PDF", pdf, f"Report_{src}.pdf", "application/pdf")
                    
                    st.dataframe(sub, use_container_width=True)
        else:
            st.info("No data yet. Run the simulation.")
    except:
        st.warning("Ensure backend is running on Port 8000")