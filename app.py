from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
import cv2
import numpy as np
from PIL import Image
import pytesseract
import io
import re
from datetime import datetime

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
CORS(app)

def extract_dob_from_image(image):
    text = pytesseract.image_to_string(image)
    print("OCR Text:", text)  # Debug
    patterns = [
        r"\b\d{2}/\d{2}/\d{4}\b",  # 01/01/2000
        r"\b\d{4}-\d{2}-\d{2}\b",  # 2000-01-01
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None

def calculate_age(dob_str):
    try:
        if '/' in dob_str:
            dob = datetime.strptime(dob_str, "%d/%m/%Y")
        else:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return None

@app.route("/verify", methods=["POST"])
def verify():
    selfie_file = request.files.get("selfie")
    id_card_file = request.files.get("id_card")

    if not selfie_file or not id_card_file:
        return jsonify({"success": False, "message": "Missing files"}), 400

    # Convert to OpenCV format
    selfie_np = np.frombuffer(selfie_file.read(), np.uint8)
    selfie_img = cv2.imdecode(selfie_np, cv2.IMREAD_COLOR)

    id_np = np.frombuffer(id_card_file.read(), np.uint8)
    id_img = cv2.imdecode(id_np, cv2.IMREAD_COLOR)

    try:
        # Face match
        verification = DeepFace.verify(selfie_img, id_img, enforce_detection=False)
        match = verification["verified"]
    except Exception as e:
        return jsonify({"success": False, "message": "Face match failed", "error": str(e)})

    # DOB Extraction
    pil_img = Image.fromarray(id_img)
    dob = extract_dob_from_image(pil_img)
    age = calculate_age(dob) if dob else None
    eligible = age >= 18 if age else False

    return jsonify({
        "success": True,
        "match": match,
        "dob": dob,
        "age": age,
        "eligible": eligible
    })

if __name__ == "__main__":
    app.run(debug=True)
