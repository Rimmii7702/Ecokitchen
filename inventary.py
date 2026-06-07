from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime
import os

inventary = Flask(__name__)

def load_inventory_data():
    try:
        df = pd.read_csv('data/Ingredients.csv')
        df['Expiry date'] = pd.to_datetime(df['Expiry date'], errors='coerce')
        df['Days until expiry'] = (df['Expiry date'] - pd.Timestamp.now()).dt.days

        print(df[['Name', 'Expiry date', 'Days until expiry']].head())

        return df.to_dict(orient='records')
    except Exception as e:
        print("Error loading inventory data:", e)
        return []


# @inventary.route('/inventory-page')
# def inventory_page():
#     data = load_inventory_data()
#     print(data)
#     return render_template('inventory.html', inventory=data)


# if __name__ == '__main__':
#     inventary.run(debug=True)
