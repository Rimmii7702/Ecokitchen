import pandas as pd
import os
from datetime import datetime, timedelta

def load_inventory_data():
    """Load inventory data and preprocess it"""
    df = pd.read_csv("data/Ingredients.csv", sep=',')

    print("Columns in the CSV file:", df.columns)

    df.columns = df.columns.str.strip()

    if 'Expiry date' not in df.columns:
        raise KeyError("'Expiry date' column is missing or has a different name.")
    
    df['Expiry date'] = pd.to_datetime(df['Expiry date'], errors='coerce')
    
    today = pd.Timestamp.today().normalize()
    df['Days until expiry'] = (df['Expiry date'] - today).dt.days

    return df

def load_menu_data():
    """Load menu data"""
    df = pd.read_csv("data/Recipes.csv", sep=',')
    df.columns = df.columns.str.strip()
    return df

def get_expiring_today_tomorrow(inventory_df):
    """Get ingredients expiring today or tomorrow"""
    return inventory_df[inventory_df['Days until expiry'] <= 2].sort_values('Days until expiry')

def get_expiring_within_two_weeks(inventory_df):
    """Get ingredients expiring within 3-15 days"""
    return inventory_df[
        (inventory_df['Days until expiry'] >= 3) & 
        (inventory_df['Days until expiry'] <= 15)
    ].sort_values('Days until expiry')

def get_fresh_fruits_vegetables(inventory_df):
    """Get fruits and vegetables that should be used soon (within 8-10 days after restock)"""
    return inventory_df[
        (inventory_df['Catagory'] == 'Fruits & Vegetables') & 
        (inventory_df['No of days after restock.'] >= 8) & 
        (inventory_df['No of days after restock.'] <= 10)
    ]

def main():
    inventory_file = "inventory_data.tsv"
    menu_file = "menu_data.tsv"
    
    inventory_df = load_inventory_data(inventory_file)
    menu_df = load_menu_data(menu_file)
    
    expiring_soon = get_expiring_today_tomorrow(inventory_df)
    expiring_two_weeks = get_expiring_within_two_weeks(inventory_df)
    fresh_produce = get_fresh_fruits_vegetables(inventory_df)
    
    print(f"Total ingredients: {len(inventory_df)}")
    print(f"Ingredients expiring today/tomorrow: {len(expiring_soon)}")
    print(f"Ingredients expiring within 2 weeks: {len(expiring_two_weeks)}")
    print(f"Fresh produce to use: {len(fresh_produce)}")

if __name__ == "__main__":
    main()