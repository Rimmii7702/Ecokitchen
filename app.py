from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import os
from waste_model import run_yolo_detection, analyze_image
from heat_model import process_kitchen_image
from werkzeug.utils import secure_filename
from inventory_system import FoodInventorySystem
from own_recipe_generation import *
from inventary import *
from main_application import *
import logging
import json
import cv2
from datetime import datetime
from ultralytics import YOLO
import google.generativeai as genai
from PIL import Image

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['HEATMAP_UPLOAD_FOLDER'] = 'static/heatmap_uploads'
app.config['HEATMAP_RESULT_FOLDER'] = 'static/heatmap_results'

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
os.makedirs(app.config['HEATMAP_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['HEATMAP_RESULT_FOLDER'], exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'mp4', 'avi', 'mov', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register uploads as a static folder
app.config['UPLOADS'] = 'static/uploads'
app.add_url_rule(
    '/uploads/<path:filename>',
    endpoint='uploads',
    view_func=app.send_static_file,
    defaults={'static_folder': app.config['UPLOADS']}
)

# Register inventory_results as a static folder
app.config['INVENTORY_RESULTS'] = os.path.join('static', 'inventory_results')
os.makedirs(app.config['INVENTORY_RESULTS'], exist_ok=True)
app.add_url_rule(
    '/inventory_results/<path:filename>',
    endpoint='inventory_results',
    view_func=app.send_static_file,
    defaults={'static_folder': app.config['INVENTORY_RESULTS']}
)

# Initialize systems
try:
    inventory_system = FoodInventorySystem(
        yolo_model_path='inventory_best.pt',
        expiry_data_path='data/inventory_metadata.csv'
    )
    yolo_model = YOLO('yolov8n.pt')
    app.logger.debug("Successfully initialized systems")
except Exception as e:
    app.logger.error(f"Failed to initialize systems: {e}")
    raise

def allowed_file(filename):
    if '.' not in filename:
        app.logger.debug(f"No extension in filename: {filename}")
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    app.logger.debug(f"Checking extension: {ext} against {ALLOWED_EXTENSIONS}")
    return ext in ALLOWED_EXTENSIONS


# Set up Gemini API
os.getenv("GEMINI_API_KEY")

# Load model
model = genai.GenerativeModel("gemini-2.0-flash")

def waste_level(weight):
    try:
        weight = float(weight)
    except (ValueError, TypeError):
        weight = 0 

    if weight < 100:
        return "Low"
    elif weight < 300:
        return "Medium"
    else:
        return "High"


@app.route("/")
def index():
    return render_template("index.html")

# <================== Inverntory =============================>
@app.route('/Inventory_track')
def inverntory():
    return render_template('Inventory_track.html')



# Ensure other routes (e.g., index, results_image) are defined


@app.route('/results_image')
def results_image():
    # Simulated result data (replace with actual backend logic)
    result = {
        'image': 'IMG_2955.jpeg',
        'total_items': 17,
        'item_counts': {
            'Wine': 4,
            'Spaghetti-Sauce': 2,
            'Noodle': 1,
            'Rice': 2,
            'Pasta-Noodles-Spaghetti': 2,
            'Pasta-Elbow': 1,
            'Honey': 1,
            'Instant-Noodle': 1
        },
        'items': [
            {'ingredient': 'Wine', 'spoilage_status': 'Fresh', 'days_to_expiry': 10, 'detection_confidence': 0.95},
            {'ingredient': 'Spaghetti-Sauce', 'spoilage_status': 'Fresh', 'days_to_expiry': 5, 'detection_confidence': 0.90}
            # Add more items as needed
        ]
    }
    return render_template('results_image.html', result=result, error=None) 

@app.route('/upload_image', methods=['POST'])
def upload_image():
    app.logger.debug("Received upload request for static image")
    
    if 'image' not in request.files:
        app.logger.error("No image uploaded")
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        app.logger.error("No image selected")
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        app.logger.debug(f"Saving uploaded file to {filepath}")
        file.save(filepath)
        
        if not os.path.exists(filepath):
            app.logger.error(f"Failed to save image to {filepath}")
            return jsonify({'error': 'Failed to save uploaded image'}), 500
        
        try:
            app.logger.debug(f"Processing image: {filepath}")
            result = inventory_system.process_image(filepath)
            if result is None or not isinstance(result, dict):
                app.logger.error(f"Image processing returned invalid result: {result}")
                return jsonify({'error': 'Failed to process image'}), 500
            
            result['image'] = filename
            
            # Ensure 'items' is a list
            if 'items' not in result or not isinstance(result.get('items', None), list):
                result['items'] = []
                app.logger.warning(f"Items not found or invalid in result, defaulting to empty list: {result}")
            
            # Ensure 'total_items' is set
            result['total_items'] = len(result['items']) if result.get('total_items') is None else result['total_items']
            
            json_filename = f"{os.path.splitext(filename)[0]}_result.json"
            save_path = os.path.join(app.config['INVENTORY_RESULTS'], json_filename)
            app.logger.debug(f"Saving result JSON to: {save_path}")
            
            # Save JSON result
            with open(save_path, 'w') as f:
                json.dump(result, f, indent=4)
            
            return redirect(url_for('show_results', json_file=json_filename))
        
        except Exception as e:
            app.logger.error(f"Processing failed: {str(e)}")
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
    app.logger.error(f"Invalid file type for filename: {file.filename}")
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/upload_video', methods=['POST'])
def upload_video():
    app.logger.debug("Received upload request for video")
    
    if 'video' not in request.files:
        app.logger.error("No video uploaded")
        return jsonify({'error': 'No video uploaded'}), 400
    
    file = request.files['video']
    if file.filename == '':
        app.logger.error("No video selected")
        return jsonify({'error': 'No video selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        app.logger.debug(f"Saving uploaded video to {filepath}")
        file.save(filepath)
        
        if not os.path.exists(filepath):
            app.logger.error(f"Failed to save video to {filepath}")
            return jsonify({'error': 'Failed to save uploaded video'}), 500
        
        try:
            app.logger.debug(f"Processing video: {filepath}")
            change_log, all_items = process_video(filepath, yolo_model)  # Use yolo_model
            if not isinstance(change_log, list):
                app.logger.error(f"Invalid change_log type: {type(change_log)}, value: {change_log}")
                return jsonify({'error': 'Invalid video processing result'}), 500
            total_added_items = len(set().union(*[set(change.get('added', [])) for change in change_log]))
            result = {
                'video': filename,
                'change_log': change_log,
                'total_added_items': total_added_items,
                'all_items': list(all_items)
            }
            json_filename = f"{os.path.splitext(filename)[0]}_result.json"
            app.logger.debug(f"Generated JSON filename: {json_filename}, Result: {result}")
            with open(os.path.join(app.config['INVENTORY_RESULTS'], json_filename), 'w') as f:
                json.dump(result, f, indent=4)
            return redirect(url_for('show_results', json_file=json_filename))
        except Exception as e:
            app.logger.error(f"Video processing failed: {str(e)}")
            return jsonify({'error': f'Video processing failed: {str(e)}'}), 500
    
    app.logger.error(f"Invalid video file type for filename: {file.filename}")
    return jsonify({'error': 'Invalid video file type'}), 400

@app.route('/video_feed/<filename>')
def video_feed(filename):
    def generate_frames(filepath):
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            app.logger.error(f"Failed to open video file: {filepath}")
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\n{"error": "Failed to open video file"}\r\n'
            return
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                app.logger.error(f"Failed to encode frame from {filepath}")
                yield b'--frame\r\nContent-Type: text/plain\r\n\r\n{"error": "Failed to encode frame"}\r\n'
                break
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        cap.release()

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    app.logger.debug(f"Streaming video from {filepath}")
    if not os.path.exists(filepath):
        app.logger.error(f"Video file not found: {filepath}")
        return jsonify({'error': 'Video file not found'}), 404
    return Response(generate_frames(filepath),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/results/<json_file>')
def show_results(json_file):
    json_path = os.path.join('static/inventory_results', json_file)
    app.logger.debug(f"Attempting to load results from {json_path}")
    try:
        if not os.path.exists(json_path):
            app.logger.error(f"JSON file not found: {json_path}")
            return render_template('results_error.html', error=f"JSON file not found: {json_path}")
        
        with open(json_path, 'r') as f:
            result = json.load(f)
            app.logger.debug(f"Loaded JSON content type: {type(result)}, content: {result}")
            if not isinstance(result, dict):
                app.logger.error(f"Invalid JSON format: {result} is not a dictionary")
                return render_template('results_error.html', error=f"Invalid JSON format: {result} is not a dictionary")
            if 'image' in result:
                image_url = url_for('uploads', filename=result['image'])
                result['image_url'] = image_url
                if 'items' not in result or not isinstance(result.get('items', None), list):
                    result['items'] = []
                    app.logger.warning(f"Items not found or invalid in result, defaulting to empty list: {result}")
                result['total_items'] = len(result['items'])
                return render_template('results_image.html', result=result)
            elif 'video' in result:
                video_url = url_for('video_feed', filename=result['video'])
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], result['video'])):
                    result['video_url'] = video_url
                else:
                    app.logger.error(f"Video file not found for streaming: {result['video']}")
                    result['video_url'] = None
                if 'change_log' not in result or not isinstance(result.get('change_log', None), list):
                    result['change_log'] = []
                    app.logger.warning(f"Change_log not found or invalid in result, defaulting to empty list: {result}")
                return render_template('results_video.html', result=result)
            else:
                app.logger.error(f"Unexpected result structure: {result}")
                return render_template('results_error.html', error=f"Unexpected result structure: {result}")
    except json.JSONDecodeError as e:
        app.logger.error(f"JSON decode error: {e}")
        return render_template('results_error.html', error=f"Error decoding JSON: {e}")
    except Exception as e:
        app.logger.error(f"Error loading results: {e}")
        return render_template('results_error.html', error=f"Error loading results: {e}")

@app.teardown_appcontext
def cleanup(e=None):
    app.logger.debug("Cleaned up")

def process_video(video_path, yolo_model):  # Accept yolo_model as parameter
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        app.logger.error(f"Error: Could not open video file {video_path}")
        raise Exception("Could not open video file")

    previous_items = set()
    change_log = []
    all_items = set()

    print("📡 Monitoring changes...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_items = scan_inventory(frame, yolo_model)  # Use yolo_model
        all_items.update(current_items)

        added_items = sorted(list(current_items - previous_items))
        removed_items = sorted(list(previous_items - current_items))

        if added_items or removed_items:
            timestamp_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            time_key = int(timestamp_sec // 5) * 5
            if not change_log or change_log[-1].get("time_key") != time_key:
                change_log.append({
                    "time_key": time_key,
                    "timestamp": f"{time_key}:00 - {time_key + 4}:59",
                    "added": set(),
                    "removed": set()
                })
            change_log[-1]["added"].update(added_items)
            change_log[-1]["removed"].update(removed_items)
            previous_items = current_items

    for change in change_log:
        change["added"] = sorted(list(change["added"]))
        change["removed"] = sorted(list(change["removed"]))

    cap.release()
    return change_log, all_items

def scan_inventory(frame, yolo_model):  # Accept yolo_model as parameter
    results = yolo_model(frame)  # Use the passed yolo_model
    detected_items = set()
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = yolo_model.names[cls_id]
            if conf > 0.5:
                detected_items.add(class_name)
    return detected_items

@app.route('/live_spoilage_status', methods=['GET', 'POST'])
def live_spoilage_status():
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Load and analyze image (assuming model is defined)
                img = Image.open(filepath)
                response = model.generate_content(
                    [
                        "You're a food inspection assistant. Analyze the food in this image and respond with the following in plain text:\n"
                        "- Item name (e.g., apple, bread, tomato, etc.)\n"
                        "- Spoilage status: Fresh, Soon-to-rot, or Rotten\n"
                        "- Confidence (in percentage)\n"
                        "- Suggested action: Safe to use, Use soon, or Discard now\n"
                        "Keep your response short and in plain language. Example:\n"
                        "Item: Tomato\n"
                        "Status: Rotten\n"
                        "Confidence: 92%\n"
                        "Action: Discard now",
                        img
                    ]
                )
                
                # Parse response
                lines = response.text.strip().split('\n')
                analysis = []
                item_data = {}
                for line in lines:
                    if line.startswith('Item:'):
                        item_data['item'] = line.replace('Item:', '').strip()
                    elif line.startswith('Status:'):
                        item_data['status'] = line.replace('Status:', '').strip()
                    elif line.startswith('Confidence:'):
                        item_data['confidence'] = line.replace('Confidence:', '').strip().replace('%', '')
                    elif line.startswith('Action:'):
                        item_data['action'] = line.replace('Action:', '').strip()
                        analysis.append(item_data.copy())
                
                return jsonify({'analysis': analysis, 'uploaded_image': filename})
            except Exception as e:
                return jsonify({'error': f'Error analyzing image: {str(e)}'}), 500
    
    return render_template('live_spoilage_status.html', analysis=None)

#  <============ Food Waste Analysis =====================>

@app.route("/waste_analysis", methods=["GET", "POST"])
def waste():
    if request.method == "POST":
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            yolo_output = os.path.join(app.config['RESULT_FOLDER'], f"yolo_{filename}")
            run_yolo_detection(upload_path, yolo_output)

            result = analyze_image(upload_path)
            level = waste_level(result.get("approximate_weight", 0))

            return render_template("waste.html",
                upload_path=upload_path,
                yolo_image=yolo_output,
                result=result,
                level=level
            )
    return render_template("waste.html")

@app.route("/kitchen_heatmap", methods=["GET", "POST"])
def kitchen_heatmap():
    if request.method == "POST":
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['HEATMAP_UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            heatmap_output = os.path.join(app.config['HEATMAP_RESULT_FOLDER'], f"heatmap_{filename}")
            dist_graph_output = os.path.join(app.config['HEATMAP_RESULT_FOLDER'], f"dist_graph_{filename}")

            result = process_kitchen_image(upload_path, heatmap_output, dist_graph_output)

            return render_template("kitchen_heatmap.html",
                upload_path=upload_path,
                result=result
            )
    return render_template("kitchen_heatmap.html")

# <========= menu optimaization ========>

@app.route('/recipe')
def recipe():
    return render_template('own_recipe_generation.html')

@app.route('/ingredients')
def ingredients():
    data = load_ingredients_by_category()
    return jsonify(data)

@app.route('/generate-recipe', methods=['POST'])
def get_recipe():
    data = request.get_json()
    selected_ingredients = data.get('ingredients', [])
    recipe = generate_recipe(selected_ingredients)
    return jsonify({"recipe": recipe})

@app.route('/inventory-page')
def inventory_page():
    data = load_inventory_data()
    print(data)
    return render_template('inventory.html', inventory=data)

@app.route('/today_special')
def today_special():
    return render_template('todays_special.html')

@app.route('/api/todays_special', methods=['GET'])
def get_todays_special():
    """API endpoint to get today's special"""
    if recommendations is None:
        return jsonify({"message": "Recommendations not available."}), 404

    todays_special = recommendations.get("todays_special", {})
    expiring_ingredients = recommendations.get("expiring_ingredients", {})

    if todays_special:
        print("Hello")
        return jsonify({
            "todays_special" : todays_special,
            "ingredients" : expiring_ingredients
            })
    else:
        return jsonify({"message": "No special today."}), 404

@app.route('/recipe_detail')
def recipe_detail():
    dish_key = request.args.get('dish')
    
    dish_details = {"name": "Sample Dish", "description": "A tasty treat!"}
    
    return render_template('recipe_detail.html', dish=dish_key)

@app.route("/api/menu/twoweek", methods=["GET"])
def get_two_week_menu():
    TWO_WEEK_MENU = recommendations.get("two_week_menu", {})
    logging(recommendations)
    return jsonify(TWO_WEEK_MENU)


def main():
    global recommendations
    
    gemini_api_key = "YOUR_GEMINI_API_KEY"
    
    system = RecipeRecommendationSystem()
    
    system.load_data()
    
    json_file = system.save_recommendations()
    
    print(f"Recommendations saved to {json_file}")
    
    recommendations = system.get_recommendations()

if __name__ == "__main__":
    main()
    app.run(debug=False)