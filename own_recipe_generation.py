from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)
CSV_FILE = 'data/Grocery_Inventory_and_Sales_Dataset.csv'

def load_ingredients_by_category():
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['Catagory', 'Product_Name'])

        ingredients_by_category = {}

        for _, row in df.iterrows():
            cat = row['Catagory'].strip()
            item = row['Product_Name'].strip()

            if cat not in ingredients_by_category:
                ingredients_by_category[cat] = []
            if item not in ingredients_by_category[cat]:
                ingredients_by_category[cat].append(item)

        return ingredients_by_category

    except Exception as e:
        print("Error loading CSV:", e)
        return {}

def generate_recipe(ingredients):
    from dotenv import load_dotenv
    load_dotenv()
    
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        return "Please set your GEMINI_API_KEY environment variable."

    try:
        import google.generativeai as genai
        
        # Configure the Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
        
        prompt = f"""Create a delicious and easy-to-make Indian recipe using some or all of these ingredients: {', '.join(ingredients)}.

        Please ensure the recipe is something that would be familiar and appealing to an Indian audience.
        
        Format the recipe as follows:
        
        1.  A creative and descriptive Indian-style recipe name.
        2.  A list of ingredients with measurements (using common Indian units where applicable, e.g., "cups," "tablespoons," "teaspoons," "grams," or "numbers of items").
        3.  Clear, step-by-step cooking instructions written in a way that's easy for an Indian cook to follow.
        4.  An estimated cooking time.
        5.  A recommended serving size.
        """
        
        response = model.generate_content(prompt)
        recipe = response.text
        return recipe
        
    except Exception as e:
        print(f"Error generating recipe: {e}")
        return f"Sorry, there was an error generating your recipe: {str(e)}"
    return recipe

# @app.route('/recipe')
# def recipe():
#     return render_template('own_recipe_generation.html')

# @app.route('/ingredients')
# def ingredients():
#     data = load_ingredients_by_category()
#     return jsonify(data)

# @app.route('/generate-recipe', methods=['POST'])
# def get_recipe():
#     data = request.get_json()
#     selected_ingredients = data.get('ingredients', [])
#     recipe = generate_recipe(selected_ingredients)
#     return jsonify({"recipe": recipe})

# if __name__ == '__main__':
#     app.run(debug=True)
