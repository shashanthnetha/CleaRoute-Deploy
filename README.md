# 🚧 CleaRoute Pro: AI Infrastructure Monitor (Local Edition)

**CleaRoute Pro** is a high-performance, AI-powered system designed to detect road defects (potholes) in real-time. Unlike simple image scanners, this system uses a custom-trained **YOLOv8** model to analyze video feeds, track unique defects over time, and generate official audit reports automatically.

This version is optimized to run **Locally** on your machine for maximum privacy, zero latency, and high accuracy.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/AI-YOLOv8-green)
![Backend](https://img.shields.io/badge/Backend-FastAPI-teal)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red)

---

## 🛠️ Prerequisites

Before you begin, make sure you have these installed on your computer:

1.  **Python (3.10 or higher):** [Download Here](https://www.python.org/downloads/)
    * *Note: During installation, tick the box "Add Python to PATH".*
2.  **Git:** [Download Here](https://git-scm.com/downloads)
3.  **VS Code (Optional but recommended):** [Download Here](https://code.visualstudio.com/)

---

## 📥 Step 1: Download the Project

Open your **Command Prompt** (Windows) or **Terminal** (Mac/Linux) and run the following commands to download the code to your computer:

```bash
# Clone the repository
git clone [https://github.com/shashanthnetha/CleaRoute-Deploy.git](https://github.com/shashanthnetha/CleaRoute-Deploy.git)

# Enter the project folder
cd CleaRoute-Deploy
📦 Step 2: Install Requirements
We need to install the "brains" of the operation (AI libraries, Dashboard tools, etc.). Run this command inside the folder:

Bash

pip install -r requirements.txt
This will install: ultralytics (YOLO), fastapi (Server), streamlit (Dashboard), fpdf (Reports), and other necessary tools.

🧠 Step 3: Setup the AI Model
The system needs a trained model file to recognize potholes.

Look inside the project folder.

Ensure you have a file named best.pt.

Note: This file contains the custom training data. If it is missing, the system will automatically download a backup model (yolov8n.pt) when you run it, but accuracy will be lower.

🚀 Step 4: How to Run (The Important Part!)
Because this is a professional Client-Server Architecture, you need to run two separate components at the same time.

🟢 Terminal 1: Start the Backend (The Brain)
Open a terminal inside the project folder.

Run this command:

Bash

uvicorn main:app --reload
Wait until you see the message: Application startup complete.

Do not close this terminal. Leave it running.

🔵 Terminal 2: Start the Dashboard (The Interface)
Open a New Terminal window (keeping the first one open).

Make sure you are in the project folder (cd CleaRoute-Deploy).

Run this command:

Bash

streamlit run dashboard.py
A browser window will automatically open showing the CleaRoute Pro interface!

🎮 How to Use the System
Once the browser window opens, follow these steps to test the AI:

Select Input Source:

Choose "CCTV Simulation" to test with video.

Upload Footage:

Upload any .mp4 video file of a road (Dashcam or Phone recording).

Activate AI:

Click the "▶️ START ANALYSIS" button.

Watch Real-Time Detection:

You will see red boxes appear around potholes instantly.

The "Unique Defects" counter will update only when new potholes appear (smart tracking).

Download Report:

Go to the "Analytics & Report" tab at the top.

View the graph history.

Click "📄 Download PDF" to get an official government-style audit report.

❓ Troubleshooting
Error: "Address already in use"

This means the server is already running in the background. Close your terminals and try again.

Error: "Connection Refused"

Make sure Terminal 1 (Backend) is actually running. The Dashboard cannot work without the Backend.

System detects cars instead of potholes?

Check if you have the correct best.pt file. If the system cannot find your custom model, it defaults to a standard model that detects cars.

👨‍💻 Author
P. Shashanth Infrastructure Monitoring & Computer Vision Project
