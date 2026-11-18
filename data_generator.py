"""
Generates realistic POS (Point-of-Sale) transaction data for retail stores.
Includes customer demographics, transaction timestamps, categories, and amounts.
"""

import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

CATEGORIES = [
    {"name": "Apparel & Fashion", "min_spend": 800, "max_spend": 6500},
    {"name": "Footwear & Accessories", "min_spend": 900, "max_spend": 5500},
    {"name": "Beauty & Personal Care", "min_spend": 450, "max_spend": 2800},
    {"name": "Electronics & Gadgets", "min_spend": 1500, "max_spend": 18000},
    {"name": "Home & Lifestyle", "min_spend": 600, "max_spend": 4800},
]

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Sneha", "Aditya", "Neha",
    "Rahul", "Pooja", "Kabir", "Tanvi", "Arjun", "Ishita", "Siddharth", "Rhea",
    "Amit", "Divya", "Karan", "Simran", "Varun", "Meera", "Gaurav", "Kavya",
    "Manish", "Sunita", "Harsh", "Deepika", "Nikhil", "Shreya", "Rajesh", "Anita",
    "Akash", "Swati", "Suresh", "Pallavi", "Vivek", "Kriti", "Alok", "Juhi",
    "Marcus", "Elena", "Liam", "Sophia", "Noah", "Olivia", "James", "Emma"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Mehta", "Singh", "Reddy", "Nair",
    "Deshmukh", "Chopra", "Joshi", "Bhatia", "Kapoor", "Malhotra", "Iyer", "Rao",
    "Smith", "Johnson", "Davis", "Taylor", "Miller", "Wilson", "Anderson"
]

PAYMENT_METHODS = ["Credit Card", "UPI / Mobile Pay", "Debit Card", "Cash"]


def generate_retail_dataset(num_customers=120, max_transactions=800, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    # Base reference date: today
    now = datetime(2026, 11, 9, 10, 0, 0)
    
    customers = []
    for i in range(1, num_customers + 1):
        cid = f"CUST-{1000 + i}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone = f"+91 {random.randint(90000, 99999)} {random.randint(10000, 99999)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        
        # Customer loyalty profile tendency:
        # 1. VIP (Frequent, recent, high spend) - 15%
        # 2. Regular / Loyal (Consistent, recent, medium spend) - 30%
        # 3. New Shoppers (1-2 recent visits) - 20%
        # 4. Slipping / At-Risk (Past frequent, but inactive lately) - 20%
        # 5. Churned (Old visits, haven't returned for months) - 15%
        profile_rand = random.random()
        if profile_rand < 0.15:
            profile = "VIP"
            tx_count = random.randint(8, 16)
            recency_days = random.randint(1, 14)
            avg_cycle = random.randint(7, 20)
            spend_multiplier = 1.6
        elif profile_rand < 0.45:
            profile = "Loyal"
            tx_count = random.randint(5, 10)
            recency_days = random.randint(5, 30)
            avg_cycle = random.randint(15, 35)
            spend_multiplier = 1.1
        elif profile_rand < 0.65:
            profile = "New"
            tx_count = random.randint(1, 3)
            recency_days = random.randint(2, 25)
            avg_cycle = random.randint(20, 45)
            spend_multiplier = 0.9
        elif profile_rand < 0.85:
            profile = "At-Risk"
            tx_count = random.randint(4, 9)
            recency_days = random.randint(65, 120)  # Long inactivity!
            avg_cycle = random.randint(14, 28)     # Used to visit every 2-3 weeks!
            spend_multiplier = 1.2
        else:
            profile = "Churned"
            tx_count = random.randint(1, 4)
            recency_days = random.randint(130, 240) # Very long absence
            avg_cycle = random.randint(30, 60)
            spend_multiplier = 0.8

        customers.append({
            "customer_id": cid,
            "name": name,
            "phone": phone,
            "email": email,
            "profile": profile,
            "tx_count": tx_count,
            "recency_days": recency_days,
            "avg_cycle": avg_cycle,
            "spend_multiplier": spend_multiplier
        })

    transactions = []
    tx_id_counter = 5001

    for cust in customers:
        # Build transaction sequence back from the most recent date
        last_date = now - timedelta(days=cust["recency_days"], hours=random.randint(1, 10))
        current_date = last_date
        
        # Customer preferred category
        pref_cat = random.choice(CATEGORIES)

        for t_idx in range(cust["tx_count"]):
            # Mix in preferred category mostly
            cat = pref_cat if random.random() < 0.7 else random.choice(CATEGORIES)
            base_amount = random.uniform(cat["min_spend"], cat["max_spend"])
            total_amount = round(base_amount * cust["spend_multiplier"], 2)
            quantity = random.randint(1, 4)

            transactions.append({
                "transaction_id": f"TXN-{tx_id_counter}",
                "customer_id": cust["customer_id"],
                "customer_name": cust["name"],
                "customer_phone": cust["phone"],
                "customer_email": cust["email"],
                "timestamp": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                "category": cat["name"],
                "items_count": quantity,
                "amount": total_amount,
                "payment_method": random.choice(PAYMENT_METHODS)
            })
            tx_id_counter += 1

            # Step back in time by inter-purchase interval + jitter
            step_days = max(2, int(np.random.normal(cust["avg_cycle"], 4)))
            current_date = current_date - timedelta(days=step_days, hours=random.randint(0, 12))

    df_tx = pd.DataFrame(transactions)
    # Sort chronologically
    df_tx["timestamp"] = pd.to_datetime(df_tx["timestamp"])
    df_tx = df_tx.sort_values("timestamp").reset_index(drop=True)
    return df_tx


if __name__ == "__main__":
    df = generate_retail_dataset()
    df.to_csv("sample_transactions.csv", index=False)
    print(f"Generated {len(df)} transactions across {df['customer_id'].nunique()} unique customers.")
