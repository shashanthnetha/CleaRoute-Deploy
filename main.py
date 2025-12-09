from fastapi import FastAPI, UploadFile, File, Form
from ultralytics import YOLO
from PIL import Image
import io
import base64
import cv2
import sqlite3
import datetime

app = FastAPI()

# Load the Super Brain (Trained on 3k+ images)
# model = YOLO('best.pt') 
model = YOLO('yolov8n.pt') # This downloads the tiny model automatically

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('clearoute_v2.db') # New DB file for V2
    c = conn.cursor()
    # Create table with Source tracking
    c.execute('''CREATE TABLE IF NOT EXISTS traffic_data 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  source TEXT, 
                  potholes INTEGER, 
                  quality TEXT)''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

@app.get("/")
def home():
    return {"status": "CleaRoute V2 (Pro) Online"}

@app.post("/analyze")
async def analyze_road(
    file: UploadFile = File(...), 
    source_name: str = Form(...) 
):
    # 1. Read Image
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # 2. Run AI (The Medium model is smarter, so we trust it more)
    results = model(image)
    
    # 3. Draw Boxes
    annotated_frame = results[0].plot()
    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(annotated_frame_rgb)

    # 4. Convert to Base64 for display
    buff = io.BytesIO()
    pil_img.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")

    # 5. Get Stats
    detection_count = len(results[0].boxes)
    # Simple logic: If detections > 0, it's bad.
    quality_score = "Bad" if detection_count > 0 else "Good"

    # 6. Save to V2 Database
    try:
        conn = sqlite3.connect('clearoute_v2.db')
        c = conn.cursor()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO traffic_data (timestamp, source, potholes, quality) VALUES (?, ?, ?, ?)", 
                  (current_time, source_name, detection_count, quality_score))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

    return {
        "potholes_found": detection_count, 
        "road_quality": quality_score, 
        "image_base64": img_str
    }

@app.get("/history")
def get_history():
    conn = sqlite3.connect('clearoute_v2.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, source, potholes, quality FROM traffic_data ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    # Return as 'time' and 'status' to match Dashboard V2
    return [{"time": row[0], "source": row[1], "potholes": row[2], "status": row[3]} for row in data]

@app.delete("/clear_history")
def clear_history():
    conn = sqlite3.connect('clearoute_v2.db')
    c = conn.cursor()
    c.execute("DELETE FROM traffic_data")
    conn.commit()
    conn.close()
    return {"message": "History Deleted"}