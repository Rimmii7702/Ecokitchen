import os
import json
import re
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from ultralytics import YOLO
import cv2
import matplotlib
matplotlib.use('Agg')  # Add this at the top before pyplot import

import matplotlib.pyplot as plt

load_dotenv()

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

CATEGORIES = [
    "over_portioning", "spoiled", "plate_waste",
    "prep_waste", "overproduction", "expired", "other"
]

# YOLO model
yolo_model = YOLO('best.pt')

def run_yolo_detection(image_path, output_path):
    results = yolo_model(image_path)
    img_cv = cv2.imread(image_path)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = result.names[int(box.cls)]
            confidence = float(box.conf)
            cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_cv, f"{label} ({confidence:.2f})", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imwrite(output_path, img_cv)
    return output_path

def analyze_image(image_path):
    img = Image.open(image_path)

    prompt = """
    Analyze this food waste image and provide the following information in a structured format:

    1. Primary waste category (choose one): over_portioning, spoiled, plate_waste, prep_waste, overproduction, expired, other
    2. List of visible food items
    3. Approximate weight estimate in grams
    4. Any notable observations about the waste

    Format your response as a structured JSON with keys: category, food_items, approximate_weight, notes.
    """

    response = model.generate_content([prompt, img])
    result_text = response.text

    json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group(1))
    else:
        try:
            result = json.loads(result_text)
        except:
            result = {
                "category": "other",
                "food_items": "unknown",
                "approximate_weight": 0,
                "notes": "Parsing error"
            }

    return result


def visualize_category(result, save_path):
    category = result.get("category", "unknown")
    weight = result.get("approximate_weight", 0)

    plt.figure(figsize=(5, 3))
    plt.bar([category], [weight], color='orange')
    plt.title("Waste Weight by Category")
    plt.ylabel("Grams")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    return save_path