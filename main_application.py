import pandas as pd
import os
import json
from datetime import datetime, timedelta
from data_loader import load_inventory_data, load_menu_data, get_expiring_today_tomorrow, get_expiring_within_two_weeks, get_fresh_fruits_vegetables
from recipe_generator import RecipeRecommender
from flask import Flask, render_template, request, jsonify

main_application = Flask(__name__)

class RecipeRecommendationSystem:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
    
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            return "Please set your GEMINI_API_KEY environment variable."

        """Initialize the recipe recommendation system"""
        self.gemini_api_key = GEMINI_API_KEY
        self.inventory_df = None
        self.menu_df = None
        self.recommender = RecipeRecommender(self.gemini_api_key)
        self.today = datetime.now().date()
        
    def load_data(self):
        self.inventory_df = load_inventory_data()

        self.menu_df = load_menu_data()
        
        return True
    
    def get_expiring_ingredients(self):
        """Get ingredients expiring today or tomorrow"""
        if self.inventory_df is None:
            raise ValueError("Data not loaded. Call load_data first.")
        
        expiring_soon = get_expiring_today_tomorrow(self.inventory_df)
        return expiring_soon
    
    def get_two_week_expiring(self):
        """Get ingredients expiring within two weeks"""
        if self.inventory_df is None:
            raise ValueError("Data not loaded. Call load_data first.")
        
        expiring_soon = get_expiring_within_two_weeks(self.inventory_df)
        return expiring_soon
    
    def get_recommendations(self):
        """Get all recommendations"""
        if self.inventory_df is None or self.menu_df is None:
            raise ValueError("Data not loaded. Call load_data first.")
        
        expiring_ingredients = self.get_expiring_ingredients()
        
        todays_special = self.recommender.generate_todays_special(self.inventory_df, self.menu_df)
        
        two_week_menu = self.recommender.generate_two_week_menu(self.inventory_df, self.menu_df)
        
        result = {
            "date": self.today.strftime("%Y-%m-%d"),
            "expiring_ingredients": expiring_ingredients.to_dict('records'),
            "todays_special": todays_special,
            "two_week_menu": two_week_menu
        }
        
        return result
    
    def save_recommendations(self, filename="recommendations.json"):
        """Save recommendations to a JSON file"""
        recommendations = self.get_recommendations()
        
        with open(filename, "w") as f:
            json.dump(recommendations, f, indent=4, default=str)
        
        return filename

# def main():
#     global recommendations
    
#     gemini_api_key = "YOUR_GEMINI_API_KEY"
    
#     system = RecipeRecommendationSystem()
    
#     system.load_data()
    
#     json_file = system.save_recommendations()
    
#     print(f"Recommendations saved to {json_file}")
    
#     recommendations = system.get_recommendations()

# @main_application.route('/today_special')
# def today_special():
#     return render_template('todays_special.html')

# @main_application.route('/api/todays_special', methods=['GET'])
# def get_todays_special():
#     """API endpoint to get today's special"""
#     if recommendations is None:
#         return jsonify({"message": "Recommendations not available."}), 404

#     todays_special = recommendations.get("todays_special", {})
#     expiring_ingredients = recommendations.get("expiring_ingredients", {})

#     if todays_special:
#         print("Hello")
#         return jsonify({
#             "todays_special" : todays_special,
#             "ingredients" : expiring_ingredients
#             })
#     else:
#         return jsonify({"message": "No special today."}), 404

# @main_application.route('/recipe_detail')
# def recipe_detail():
#     dish_key = request.args.get('dish')
    
#     dish_details = {"name": "Sample Dish", "description": "A tasty treat!"}
    
#     return render_template('recipe_detail.html', dish=dish_key)

# @main_application.route("/api/menu/twoweek", methods=["GET"])
# def get_two_week_menu():
#     TWO_WEEK_MENU = recommendations.get("two_week_menu", {})
#     return jsonify(TWO_WEEK_MENU)

# if __name__ == "__main__":
#     main()