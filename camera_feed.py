import cv2
import numpy as np
from ultralytics import YOLO
import logging
import json
from collections import Counter
import os
import csv

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class CameraFeed:
    def __init__(self, yolo_model_path, expiry_data_path):
        self.yolo_model = YOLO(yolo_model_path)
        self.class_names = self.yolo_model.names
        self.expiry_data = self._load_expiry_data(expiry_data_path)
        self.cap = None
        for i in range(3):  # Try indices 0, 1, 2
            self.cap = cv2.VideoCapture(i)
            if self.cap.isOpened():
                logging.debug(f"Webcam opened successfully at index {i}")
                break
            self.cap.release()
        if not self.cap.isOpened():
            logging.error("Failed to open webcam. Check if a camera is connected and indices (0-2) are correct.")
            raise Exception("Webcam not accessible")
        self.previous_counts = Counter()  # Track previous frame's item counts for change detection
        logging.debug(f"Initialized CameraFeed with model: {yolo_model_path}, expiry data: {expiry_data_path}")

    def _load_expiry_data(self, csv_path):
        expiry_dict = {}
        try:
            with open(csv_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    item_label = row['label']
                    if item_label not in expiry_dict:
                        expiry_dict[item_label] = []
                    expiry_dict[item_label].append({
                        'image_name': row['image_name'],
                        'expiry_date': row['expiry_date'],
                        'days_to_expiry': int(row['days_to_expiry']),
                        'status': row['status']
                    })
            logging.debug(f"Successfully loaded expiry data from {csv_path}")
            return expiry_dict
        except Exception as e:
            logging.error(f"Error loading expiry data from {csv_path}: {e}")
            return {}

    def _get_spoilage_status(self, item_label):
        if item_label not in self.expiry_data:
            return "Unknown", None
        item_info = self.expiry_data[item_label][0]
        return item_info['status'], item_info['days_to_expiry']

    def generate_frames(self):
        frame_count = 0
        while True:
            success, frame = self.cap.read()
            frame_count += 1
            if not success:
                logging.error(f"Failed to read frame {frame_count} from webcam. Check camera connection or permissions.")
                yield json.dumps({"error": "Failed to read frame from webcam"}).encode()
                break
            
            logging.debug(f"Processed frame {frame_count}")
            # Process frame with YOLO
            results = self.yolo_model.predict(source=frame, conf=0.4, save=False)
            if not results or len(results) == 0:
                logging.error(f"No predictions from YOLO model for frame {frame_count}")
                yield json.dumps({"error": "No detections"}).encode()
                continue
            
            detections = results[0].boxes.data.cpu().numpy()
            detected_items = []
            item_counter = Counter()
            
            for det in detections:
                x1, y1, x2, y2, conf, class_id = det
                label = self.class_names[int(class_id)]
                item_counter[label] += 1
                spoilage_status, days_to_expiry = self._get_spoilage_status(label)
                x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
                
                detected_items.append({
                    "ingredient": label,
                    "bounding_box": [x1, y1, x2, y2],
                    "detection_confidence": round(float(conf), 2),
                    "spoilage_status": spoilage_status,
                    "days_to_expiry": days_to_expiry
                })
            
            # Detect stock changes
            stock_changes = {}
            for item, count in item_counter.items():
                prev_count = self.previous_counts.get(item, 0)
                if count > prev_count:
                    stock_changes[item] = f"+{count - prev_count} added"
                elif count < prev_count:
                    stock_changes[item] = f"{prev_count - count} removed"
            self.previous_counts = item_counter.copy()

            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                logging.error(f"Failed to encode frame {frame_count} to JPEG")
                yield json.dumps({"error": "Failed to encode frame"}).encode()
                continue
            frame = buffer.tobytes()
            
            # Prepare JSON data with detection results
            result_data = {
                "total_items": sum(item_counter.values()),
                "item_counts": dict(item_counter),
                "items": detected_items,
                "stock_changes": stock_changes
            }
            json_data = json.dumps(result_data).encode()
            
            # Yield frame and data
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                   b'--frame\r\n'
                   b'Content-Type: application/json\r\n\r\n' + json_data + b'\r\n')

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
            logging.debug("Camera feed released")

if __name__ == "__main__":
    camera = CameraFeed(yolo_model_path="food-waste-best.pt", expiry_data_path="inventory_metadata.csv")
    try:
        for frame_data in camera.generate_frames():
            print(frame_data.decode(), end='')
    except KeyboardInterrupt:
        camera.release()