import os
import cv2
import json
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            print(f"❌ Failed to configure Gemini: {e}")
            return None
    print("Gemini API key not provided.")
    return None

def load_image(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Failed to load image.")
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return None

def create_blank_kitchen():
    return np.ones((600, 800, 3), dtype=np.uint8) * 255

def analyze_with_gemini(kitchen_image, gemini_model):
    if kitchen_image is None or gemini_model is None:
        return None

    prompt = """
    Analyze this kitchen image and identify:
    1. All visible kitchen stations or areas (e.g., prep station, grill, sink, storage)
    2. For each area, estimate potential waste generation level (High, Medium, Low)
    3. Provide approximate x,y coordinates for each area in the image (as percentage of width/height)

    Format your response as JSON only:
    {
      "areas": [
        {
          "name": "station name",
          "waste_level": "High/Medium/Low",
          "x_percent": 0.XX,
          "y_percent": 0.XX
        }
      ]
    }
    """

    try:
        pil_image = Image.fromarray(kitchen_image)
        response = gemini_model.generate_content([prompt, pil_image])
        result = response.text.strip()

        if result.startswith("```"):
            result = result.split("```")[1].strip()
        if result.startswith("json"):
            result = result.replace("json", "").strip()

        if not result or not result.startswith("{"):
            raise ValueError("Gemini returned an empty or non-JSON response.")

        data = json.loads(result)

        height, width = kitchen_image.shape[:2]
        waste_map = {"Low": 1.5, "Medium": 5.0, "High": 8.5}
        waste_data_list = []

        for area in data["areas"]:
            waste_kg = max(0.1, waste_map.get(area["waste_level"], 3.0) + np.random.normal(0, 0.5))
            x = int(area["x_percent"] * width)
            y = int(area["y_percent"] * height)
            waste_data_list.append({
                "area": area["name"],
                "waste_level": area["waste_level"],
                "waste_kg": waste_kg,
                "x": x,
                "y": y
            })

        return pd.DataFrame(waste_data_list)

    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
        return None

def create_sample_data(kitchen_image):
    areas = ["Prep Station", "Grill", "Sink", "Fryer", "Storage"]
    waste_kg = [4.5, 8.1, 2.9, 6.2, 1.1]
    h, w = kitchen_image.shape[:2] if kitchen_image is not None else (600, 800)
    xs = np.linspace(w * 0.1, w * 0.9, len(areas))
    ys = [h * 0.3 if i % 2 == 0 else h * 0.7 for i in range(len(areas))]
    return pd.DataFrame({
        "area": areas,
        "waste_kg": waste_kg,
        "x": [int(x) for x in xs],
        "y": [int(y) for y in ys]
    })

def generate_heatmap(kitchen_image, waste_data, output_path, alpha=0.6, radius=100):
    if kitchen_image is None:
        kitchen_image = create_blank_kitchen()
    if waste_data is None:
        waste_data = create_sample_data(kitchen_image)

    h, w = kitchen_image.shape[:2]
    heat = np.zeros((h, w), dtype=np.float32)
    max_w = waste_data['waste_kg'].max()

    for _, row in waste_data.iterrows():
        x, y = int(row["x"]), int(row["y"])
        intensity = row["waste_kg"] / max_w
        for i in range(max(0, y-radius), min(h, y+radius)):
            for j in range(max(0, x-radius), min(w, x+radius)):
                dist = np.sqrt((i-y)**2 + (j-x)**2)
                if dist < radius:
                    heat[i, j] += intensity * np.exp(-(dist**2)/(2*(radius/3)**2))

    heat /= np.max(heat)
    heat_img = (heat * 255).astype(np.uint8)
    color_map = cv2.applyColorMap(heat_img, cv2.COLORMAP_JET)
    color_map = cv2.cvtColor(color_map, cv2.COLOR_BGR2RGB)
    heatmap = cv2.addWeighted(kitchen_image, 1 - alpha, color_map, alpha, 0)

    for _, row in waste_data.iterrows():
        cv2.circle(heatmap, (int(row["x"]), int(row["y"])), 5, (0, 0, 0), -1)
        cv2.putText(heatmap, f"{row['area']}: {row['waste_kg']:.1f}kg",
                    (int(row["x"]) + 10, int(row["y"])), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

    cv2.imwrite(output_path, cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR))
    return output_path

def generate_distribution_graph(waste_data, output_path):
    if waste_data is None:
        return None

    waste_dist = waste_data.groupby('area')['waste_kg'].sum()
    total_waste = waste_dist.sum()
    areas = waste_dist.index
    weights = waste_dist.values

    img_height = 400
    img_width = 600
    bar_width = img_width // (len(areas) * 2)
    max_height = 300
    padding = 50

    graph_img = np.ones((img_height, img_width, 3), dtype=np.uint8) * 255

    for i, (area, weight) in enumerate(zip(areas, weights)):
        bar_height = int((weight / weights.max()) * max_height)
        x_start = i * bar_width * 2 + padding
        y_start = img_height - padding - bar_height
        cv2.rectangle(graph_img, (x_start, y_start), (x_start + bar_width, img_height - padding),
                      (0, 0, 255), -1)
        cv2.putText(graph_img, f"{area}: {(weight/total_waste*100):.1f}%", (x_start, y_start - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

    cv2.line(graph_img, (padding, img_height - padding), (img_width - padding, img_height - padding), (0, 0, 0), 2)
    cv2.line(graph_img, (padding, padding), (padding, img_height - padding), (0, 0, 0), 2)
    cv2.putText(graph_img, "Waste Distribution by Area", (padding, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    cv2.imwrite(output_path, graph_img)
    return output_path

def get_distribution_text(waste_data):
    if waste_data is None:
        return "No waste data available."
    waste_dist = waste_data.groupby('area')['waste_kg'].sum()
    total_waste = waste_dist.sum()
    dist_text = "Waste Distribution by Area (%):\n"
    for area, kg in waste_dist.items():
        percent = (kg / total_waste) * 100
        dist_text += f"{area}: {percent:.1f}% ({kg:.1f}kg)\n"
    return dist_text

def process_kitchen_image(image_path, heatmap_output, dist_graph_output):
    gemini_model = configure_gemini()
    kitchen_image = load_image(image_path)
    waste_data = analyze_with_gemini(kitchen_image, gemini_model)
    if waste_data is None:
        waste_data = create_sample_data(kitchen_image)
    heatmap_path = generate_heatmap(kitchen_image, waste_data, heatmap_output)
    dist_graph_path = generate_distribution_graph(waste_data, dist_graph_output)
    dist_text = get_distribution_text(waste_data)
    total_waste = waste_data['waste_kg'].sum() if waste_data is not None else 0
    return {
        "waste_data": waste_data.to_dict(orient="records"),
        "heatmap_path": heatmap_path,
        "dist_graph_path": dist_graph_path,
        "dist_text": dist_text,
        "total_waste": total_waste
    }