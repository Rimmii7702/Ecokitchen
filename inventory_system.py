import os
import cv2
import csv
import json
import numpy as np
from datetime import datetime
from collections import Counter
from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.DEBUG)

class FoodInventorySystem:
    def __init__(self, yolo_model_path, expiry_data_path):
        """
        Initialize the Food Inventory and Spoilage Detection System.
        
        Args:
            yolo_model_path: Path to the trained YOLO model
            expiry_data_path: Path to the CSV file containing expiry information
        """
        # Load YOLO model
        self.yolo_model = YOLO(yolo_model_path)
        self.class_names = self.yolo_model.names
        
        # Load expiry data from CSV
        self.expiry_data = self._load_expiry_data(expiry_data_path)
        
        # Create output directories
        self.output_dir = "inventory_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Color mapping for different spoilage statuses
        self.status_colors = {
            "Fresh": (0, 255, 0),        # Green
            "Soon-to-be-expire": (0, 165, 255),  # Orange
            "Expired": (0, 0, 255)       # Red
        }
        
    def _load_expiry_data(self, csv_path):
        """Load and process expiry data from CSV file."""
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
            return expiry_dict
        except Exception as e:
            logging.error(f"Error loading expiry data: {e}")
            return {}
    
    def _get_spoilage_status(self, item_label):
        """
        Determine spoilage status of an item based on its label.
        
        Returns:
            tuple: (status, days_to_expiry)
        """
        if item_label not in self.expiry_data:
            return "Unknown", None
        item_info = self.expiry_data[item_label][0]
        return item_info['status'], item_info['days_to_expiry']
    
    def process_image(self, image_path):
        """
        Process a single image to detect food items and their spoilage status.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            dict: Detection results including items, quantities, and spoilage status
        """
        if not os.path.isfile(image_path):
            logging.error(f"⚠️ Image file not found: {image_path}")
            return None
            
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"⚠️ Could not load image {image_path}")
            return None
        
        image_filename = os.path.basename(image_path)
        image_name_no_ext = os.path.splitext(image_filename)[0]
        
        results = self.yolo_model.predict(source=image_path, conf=0.4, save=False)
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
            
            color = self.status_colors.get(spoilage_status, (255, 255, 255))
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            text = f"{label} ({spoilage_status})"
            if days_to_expiry is not None:
                text += f": {days_to_expiry} days"
            cv2.putText(image, text, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        annotated_filename = f"{image_name_no_ext}_annotated.jpg"
        annotated_path = os.path.join(self.output_dir, annotated_filename)
        success = cv2.imwrite(annotated_path, image)
        if success:
            logging.debug(f"✅ Saved annotated image to {annotated_path}")
        else:
            logging.error(f"❌ Failed to save annotated image to {annotated_path}")
        
        result = {
            "image": image_filename,
            "items": detected_items,
            "item_counts": dict(item_counter),
            "total_items": sum(item_counter.values())
        }
        
        json_path = os.path.join(self.output_dir, f"{image_name_no_ext}_result.json")
        with open(json_path, "w") as f:
            json.dump(result, f, indent=4)
        
        logging.debug(f"✅ Processed {image_filename} → Saved results to {self.output_dir}")
        return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process food inventory from a single image')
    parser.add_argument('--image', required=True, help='')
    parser.add_argument('--model', default="best.pt", help='best.pt')
    parser.add_argument('--expiry', default="inventory_metadata.csv", help='')
    args = parser.parse_args()
    inventory_system = FoodInventorySystem(args.model, args.expiry)
    result = inventory_system.process_image(args.image)
    if result:
        print(f"\n📊 Detection Summary for {os.path.basename(args.image)}")
        print(f"   • Total items detected: {result['total_items']}")
        print("\n📋 Ingredient Inventory:")
        for item, count in result["item_counts"].items():
            print(f"   • {item}: {count}")
        print("\n🍎 Spoilage Status:")
        spoilage_counter = Counter()
        for item in result["items"]:
            spoilage_counter[item["spoilage_status"]] += 1
        for status, count in spoilage_counter.items():
            print(f"   • {status}: {count} items")
        print(f"\n🎉 Process complete. Results saved to {inventory_system.output_dir}")
    else:
        print(f"\n❌ Failed to process image: {args.image}")