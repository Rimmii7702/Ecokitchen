import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RestaurantCostOptimizer:
    def __init__(self):
        """
        Initialize the cost optimizer with restaurant data
        
        Args:
            selling_price_data_path: Path to CSV with dish cost and price data
            sales_data_path: Path to CSV with sales history data
        """
        self.dish_data = pd.read_csv('data/selling_price data.csv')
        self.sales_data = pd.read_csv('data/Sales_Weekly.csv')
       
        self.dish_data['Total_Cost'] = self.dish_data['Preparation Cost'] + self.dish_data['Cooking Cost ']
        self.dish_data['Profit_Margin'] = (self.dish_data['Selling Price'] - self.dish_data['Total_Cost']) / self.dish_data['Selling Price']
        self.dish_data['Profit_Amount'] = self.dish_data['Selling Price'] - self.dish_data['Total_Cost']
        
        self.analyze_sales_popularity()
        
    def analyze_sales_popularity(self):
        """Calculate popularity score from sales data"""
        popularity = self.sales_data.groupby('Dish Name')['Quantity Sold'].sum().reset_index()
        popularity.columns = ['Name', 'Total_Quantity_Sold']
        
        max_sold = popularity['Total_Quantity_Sold'].max()
        popularity['Popularity_Score'] = popularity['Total_Quantity_Sold'] / max_sold if max_sold > 0 else 0
        
        self.dish_data = pd.merge(self.dish_data, popularity[['Name', 'Popularity_Score']], 
                                  on='Name', how='left')
        
        self.dish_data['Popularity_Score'] = self.dish_data['Popularity_Score'].fillna(0)
    
    def add_expiry_ingredients(self, expiry_ingredients):
        """
        Add information about ingredients nearing expiry
        
        Args:
            expiry_ingredients: List of dicts with ingredient name, 
                                dishes it can be used in, and days until expiry
        """
        self.expiry_ingredients = expiry_ingredients
        
        self.dish_data['Expiry_Score'] = 0.0
        
        for ingredient in expiry_ingredients:
            expiry_urgency = max(0, (5 - ingredient['days_until_expiry'])) / 5
            
            for dish in ingredient['dishes']:
                if dish in self.dish_data['Name'].values:
                    mask = self.dish_data['Name'] == dish
                    self.dish_data.loc[mask, 'Expiry_Score'] += expiry_urgency
        
        max_score = self.dish_data['Expiry_Score'].max()
        if max_score > 0:
            self.dish_data['Expiry_Score'] = self.dish_data['Expiry_Score'] / max_score
    
    def optimize_selling_price(self, dish_name, min_profit_margin=0.2, max_price_increase=0.15):
        """
        Optimize the selling price for a specific dish
        
        Args:
            dish_name: Name of the dish to optimize
            min_profit_margin: Minimum acceptable profit margin
            max_price_increase: Maximum allowed increase from current price
            
        Returns:
            Optimized price for the dish
        """
        dish = self.dish_data[self.dish_data['Name'] == dish_name].iloc[0]
        current_price = dish['Selling Price']
        total_cost = dish['Total_Cost']
        
        min_price = total_cost / (1 - min_profit_margin)
        
        max_price = current_price * (1 + max_price_increase)
        
        dish_sales = self.sales_data[self.sales_data['Dish Name'] == dish_name]
        
        if len(dish_sales) > 0:
            price_performance = dish_sales.groupby('Unit Price (₹)').agg({
                'Quantity Sold': 'sum',
                'Total Revenue (₹)': 'sum'
            }).reset_index()
            
            best_price_idx = price_performance['Total Revenue (₹)'].idxmax()
            best_price = price_performance.iloc[best_price_idx]['Unit Price (₹)']
            
            optimized_price = max(min_price, min(best_price, max_price))
        else:
            default_price = total_cost * 1.5
            optimized_price = max(min_price, min(default_price, max_price))
        
        return round(optimized_price)
    
    def calculate_dish_score(self, row, profit_weight=0.5, popularity_weight=0.3, expiry_weight=0.2):
        """
        Calculate overall score for a dish based on multiple factors
        
        Args:
            row: DataFrame row with dish data
            profit_weight: Weight for profit margin in scoring
            popularity_weight: Weight for popularity in scoring
            expiry_weight: Weight for expiry ingredients in scoring
            
        Returns:
            Overall score for the dish
        """
        profit_score = row['Profit_Margin'] / self.dish_data['Profit_Margin'].max()
        
        score = (profit_weight * profit_score +
                 popularity_weight * row['Popularity_Score'] +
                 expiry_weight * row['Expiry_Score'])
        
        return score
    
    def recommend_todays_specials(self, num_dishes=3, expiry_ingredients=None):
        """
        Recommend dishes for today's specials with optimized prices
        
        Args:
            num_dishes: Number of dishes to recommend
            expiry_ingredients: List of ingredients nearing expiry
            
        Returns:
            List of dictionaries with dish details and optimized price
        """
        if expiry_ingredients:
            self.add_expiry_ingredients(expiry_ingredients)
        
        self.dish_data['Overall_Score'] = self.dish_data.apply(
            self.calculate_dish_score, axis=1
        )
        
        top_dishes = self.dish_data.sort_values('Overall_Score', ascending=False).head(num_dishes)
        
        recommendations = []
        for _, dish in top_dishes.iterrows():
            optimized_price = self.optimize_selling_price(dish['Name'])
            
            expected_profit = optimized_price - dish['Total_Cost']
            profit_margin = expected_profit / optimized_price
            
            recommendations.append({
                'dish_name': dish['Name'],
                'category': dish['Category'],
                'original_cost': dish['Total_Cost'],
                'original_price': dish['Selling Price'],
                'optimized_price': optimized_price,
                'expected_profit': expected_profit,
                'profit_margin': profit_margin,
                'score': dish['Overall_Score']
            })
            
        return recommendations


def main():
    optimizer = RestaurantCostOptimizer()

    expiry_ingredients = [
        {
            'name': 'Paneer',
            'days_until_expiry': 1,
            'dishes': ['Paneer Tikka', 'Palak Paneer', 'Matar Paneer', 'Kadai Paneer', 'Shahi Paneer']
        },
        {
            'name': 'Chicken',
            'days_until_expiry': 2,
            'dishes': ['Butter Chicken', 'Chicken Tikka Masala', 'Chicken Curry', 'Tandoori Chicken']
        },
        {
            'name': 'Mushrooms',
            'days_until_expiry': 1,
            'dishes': ['Crispy Mushroom Fry']
        }
    ]
    
    recommendations = optimizer.recommend_todays_specials(
        num_dishes=3,
        expiry_ingredients=expiry_ingredients
    )
    
    print("Today's Special Recommendations:")
    print("--------------------------------")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['dish_name']} ({rec['category']})")
        print(f"   Original Price: ₹{rec['original_price']:.2f}")
        print(f"   Optimized Price: ₹{rec['optimized_price']:.2f}")
        print(f"   Expected Profit: ₹{rec['expected_profit']:.2f} (Margin: {rec['profit_margin']*100:.1f}%)")
        print(f"   Score: {rec['score']:.3f}")
        print()
    
    return recommendations


if __name__ == "__main__":
    main()