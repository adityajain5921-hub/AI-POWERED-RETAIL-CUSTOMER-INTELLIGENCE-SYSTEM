"""
Analytics and Machine Learning Engine for Retail Customer Segmentation,
Non-Contractual Churn Hazard Scoring, and Automated Offer Recommendations.
"""

from datetime import datetime
import pandas as pd
import numpy as np


class RetailIntelligenceEngine:
    def __init__(self, df_transactions):
        """
        Initializes with a transaction DataFrame containing:
        customer_id, customer_name, timestamp, amount, category, (optional phone, email)
        """
        self.df = df_transactions.copy()
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
        self.ref_date = self.df["timestamp"].max() + pd.Timedelta(days=1)
        self.customer_profiles = None
        self.kpis = None

    def process(self):
        """Runs the complete intelligence pipeline."""
        self._calculate_rfm_and_cycles()
        self._segment_customers()
        self._predict_churn()
        self._generate_offers()
        self._calculate_kpis()
        return self

    def _calculate_rfm_and_cycles(self):
        """Extracts Recency, Frequency, Monetary, and Inter-purchase cycle stats."""
        # Aggregate transactions by customer
        cust_list = []
        grouped = self.df.groupby("customer_id")

        for cid, group in grouped:
            sorted_group = group.sort_values("timestamp")
            name = sorted_group["customer_name"].iloc[-1] if "customer_name" in sorted_group.columns else f"Customer {cid}"
            phone = sorted_group["customer_phone"].iloc[-1] if "customer_phone" in sorted_group.columns else "N/A"
            email = sorted_group["customer_email"].iloc[-1] if "customer_email" in sorted_group.columns else "N/A"
            
            # Recency: days since last purchase
            last_date = sorted_group["timestamp"].max()
            recency_days = (self.ref_date - last_date).days
            
            # Frequency: count of distinct purchases
            frequency = len(sorted_group)
            
            # Monetary: total spend
            monetary = float(sorted_group["amount"].sum())
            avg_basket = float(sorted_group["amount"].mean())
            
            # Top category
            top_category = sorted_group["category"].mode().iloc[0] if "category" in sorted_group.columns else "General"
            
            # Calculate Inter-Purchase Cycle (days between transactions)
            if frequency >= 2:
                time_diffs = sorted_group["timestamp"].diff().dropna().dt.total_seconds() / (24 * 3600)
                mean_cycle = float(time_diffs.mean())
                std_cycle = float(time_diffs.std()) if len(time_diffs) > 1 else 5.0
                if np.isnan(std_cycle) or std_cycle == 0:
                    std_cycle = 5.0
            else:
                mean_cycle = None
                std_cycle = None

            cust_list.append({
                "customer_id": cid,
                "name": name,
                "phone": phone,
                "email": email,
                "last_purchase_date": last_date.strftime("%Y-%m-%d"),
                "recency_days": max(1, int(recency_days)),
                "frequency": int(frequency),
                "total_spend": round(monetary, 2),
                "avg_basket": round(avg_basket, 2),
                "top_category": top_category,
                "mean_cycle": mean_cycle,
                "std_cycle": std_cycle
            })

        self.customer_profiles = pd.DataFrame(cust_list)

        # Baseline cycle for 1-time shoppers (impute with global median repeat cycle)
        valid_cycles = self.customer_profiles["mean_cycle"].dropna()
        global_median_cycle = float(valid_cycles.median()) if len(valid_cycles) > 0 else 28.0

        self.customer_profiles["mean_cycle"] = self.customer_profiles["mean_cycle"].fillna(global_median_cycle)
        self.customer_profiles["std_cycle"] = self.customer_profiles["std_cycle"].fillna(8.0)

    def _segment_customers(self):
        """
        RFM Scoring and Persona Segmentation.
        Uses quintile binning and rule-based persona mapping.
        """
        df = self.customer_profiles

        # Rank quintiles (1-5 score, 5 is best)
        # For Recency: lower days = higher score
        try:
            r_scores = pd.qcut(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
        except Exception:
            # Fallback if few unique values
            r_scores = pd.cut(df["recency_days"], bins=5, labels=[5, 4, 3, 2, 1]).astype(int)

        try:
            f_scores = pd.qcut(df["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
        except Exception:
            f_scores = pd.cut(df["frequency"], bins=5, labels=[1, 2, 3, 4, 5]).astype(int)

        try:
            m_scores = pd.qcut(df["total_spend"], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
        except Exception:
            m_scores = pd.cut(df["total_spend"], bins=5, labels=[1, 2, 3, 4, 5]).astype(int)

        df["r_score"] = r_scores
        df["f_score"] = f_scores
        df["m_score"] = m_scores
        df["rfm_combined"] = df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)

        # Persona Assignment Logic
        def assign_persona(row):
            r, f, m = row["r_score"], row["f_score"], row["m_score"]

            if r >= 4 and f >= 4 and m >= 4:
                return "Champions & VIPs", "Top spenders, frequent shoppers with recent purchases. Highly loyal."
            elif r >= 3 and f >= 3 and m >= 2:
                return "Loyal Customers", "Consistent regular shoppers with reliable spending patterns."
            elif r >= 4 and f <= 2:
                return "New & Promising", "Recent first- or second-time shoppers with high potential."
            elif r <= 2 and (f >= 3 or m >= 4):
                return "At Risk (High Value)", "Previously active big spenders who haven't visited in a long time!"
            elif r == 3 and f >= 2:
                return "Needs Attention", "Average frequency shoppers whose return cycle is starting to slip."
            else:
                return "Hibernating / Inactive", "Infrequent buyers with prolonged absence. High danger of loss."

        personas = df.apply(assign_persona, axis=1)
        df["segment"] = [p[0] for p in personas]
        df["segment_desc"] = [p[1] for p in personas]

    def _predict_churn(self):
        """
        Non-contractual Retail Churn Hazard Scoring.
        Compares days since last purchase against personal historical cycle.
        """
        df = self.customer_profiles

        # Cycle ratio: How overdue is the customer compared to their normal cycle?
        cycle_ratio = df["recency_days"] / df["mean_cycle"]

        # Logistic probability curve:
        # If cycle_ratio == 1.0 (on schedule) -> Prob ~ 25%
        # If cycle_ratio == 2.0 (missed full cycle) -> Prob ~ 60%
        # If cycle_ratio >= 3.0 (missed 3 cycles) -> Prob > 85%
        raw_prob = 1.0 / (1.0 + np.exp(-1.4 * (cycle_ratio - 1.7)))
        
        # Penalize customers with only 1 lifetime transaction who haven't returned
        single_txn_penalty = (df["frequency"] == 1) & (df["recency_days"] > 45)
        raw_prob = np.where(single_txn_penalty, raw_prob * 1.25, raw_prob)

        # Protect recent Champions
        is_champion = df["segment"] == "Champions & VIPs"
        raw_prob = np.where(is_champion & (df["recency_days"] < 25), raw_prob * 0.4, raw_prob)

        churn_probs = np.clip(np.round(raw_prob * 100, 1), 5.0, 98.0)
        df["churn_probability"] = churn_probs

        # Categorize Churn Risk
        def risk_category(p):
            if p >= 65.0:
                return "High Risk", "red", "Likely to leave; urgent retention needed"
            elif p >= 35.0:
                return "Medium Risk", "amber", "Slipping away; proactive offer suggested"
            else:
                return "Low Risk", "emerald", "Healthy active customer"

        risks = df["churn_probability"].apply(risk_category)
        df["churn_status"] = [r[0] for r in risks]
        df["churn_badge_color"] = [r[1] for r in risks]
        df["churn_risk_reason"] = [r[2] for r in risks]

    def _generate_offers(self):
        """
        Prescriptive Offer Engine:
        Creates tailored retention campaigns matching customer segment,
        churn risk, and preferred product category.
        """
        df = self.customer_profiles

        offers = []
        messages = []

        for _, row in df.iterrows():
            seg = row["segment"]
            churn_p = row["churn_probability"]
            cat = row["top_category"]
            cname = row["name"].split()[0]
            cid = row["customer_id"]

            if seg == "Champions & VIPs":
                offer_title = "VIP Gold Lounge & Double Points"
                offer_tag = "VIP Loyalty"
                discount = "0% (Value-Add Perks)"
                action = f"Free exclusive gift + 2x reward points on your next purchase over Rs 5,000 in {cat}."
                code = f"VIP-{cid[-4:]}"
                msg = f"Hi {cname}! Thank you for being one of our top patrons. Enjoy Double Reward Points and a complimentary gift on your next visit to our {cat} section. Code: {code}."

            elif seg == "Loyal Customers":
                offer_title = "Cross-Category Basket Booster"
                offer_tag = "Upsell & Reward"
                discount = "Rs 500 Off Rs 3,000+"
                action = f"Rs 500 off when you shop Rs 3,000+ across {cat} and new collections."
                code = f"LOYAL-{cid[-4:]}"
                msg = f"Hey {cname}, we appreciate your loyalty! Here is an exclusive Rs 500 off coupon on purchases of Rs 3,000 or more. Use code: {code} on your next visit."

            elif seg == "New & Promising":
                offer_title = "2nd-Visit Welcome Incentive"
                offer_tag = "Conversion"
                discount = "15% Off"
                action = f"15% off any item in {cat} valid for 10 days."
                code = f"HELLO-{cid[-4:]}"
                msg = f"Hi {cname}! We loved having you at our store. Enjoy 15% off your next purchase in {cat}. Valid for the next 10 days with code: {code}."

            elif seg == "At Risk (High Value)":
                offer_title = "Priority 'We Miss You' Win-Back"
                offer_tag = "Urgent Retention"
                discount = "20% Off + Free Delivery"
                action = f"20% discount on {cat} + personal styling perk. Expires in 7 days."
                code = f"COMEBACK-{cid[-4:]}"
                msg = f"Dear {cname}, we miss seeing you! We have reserved a special 20% savings pass on {cat} just for you. Visit us this week and show code: {code}."

            elif seg == "Needs Attention":
                offer_title = "Re-Engagement Perk"
                offer_tag = "Gentle Nudge"
                discount = "10% Off or Rs 500 Gift"
                action = f"10% off your next basket over Rs 2,000 in {cat}."
                code = f"NUDGE-{cid[-4:]}"
                msg = f"Hello {cname}, it's been a little while! Check out our new {cat} arrivals with 10% off using code: {code}."

            else:  # Hibernating / Inactive
                offer_title = "Final Reactivation Blowout"
                offer_tag = "Win-Back"
                discount = "Flat Rs 750 Off Rs 2,500+"
                action = f"Flat Rs 750 coupon to reactivate dormant account."
                code = f"REACTIVATE-{cid[-4:]}"
                msg = f"Hi {cname}, we would love to welcome you back! Take a flat Rs 750 off any purchase over Rs 2,500 with code: {code} this weekend only."

            offers.append({
                "title": offer_title,
                "tag": offer_tag,
                "discount": discount,
                "action": action,
                "promo_code": code
            })
            messages.append(msg)

        df["suggested_offer_title"] = [o["title"] for o in offers]
        df["suggested_offer_tag"] = [o["tag"] for o in offers]
        df["suggested_discount"] = [o["discount"] for o in offers]
        df["suggested_offer_detail"] = [o["action"] for o in offers]
        df["suggested_promo_code"] = [o["promo_code"] for o in offers]
        df["suggested_sms_message"] = messages

    def _calculate_kpis(self):
        """Calculates store-level overview statistics."""
        df = self.customer_profiles
        total_customers = len(df)
        total_revenue = float(df["total_spend"].sum())
        avg_spend_per_customer = float(df["total_spend"].mean())
        
        # High-risk customers count and revenue at risk
        high_risk_df = df[df["churn_status"] == "High Risk"]
        high_risk_count = len(high_risk_df)
        high_risk_pct = round((high_risk_count / total_customers) * 100, 1) if total_customers > 0 else 0
        revenue_at_risk = float(high_risk_df["total_spend"].sum())

        # Loyal customer count
        loyal_count = len(df[df["segment"].isin(["Champions & VIPs", "Loyal Customers"])])
        loyal_pct = round((loyal_count / total_customers) * 100, 1) if total_customers > 0 else 0

        # Segment distribution breakdown
        seg_counts = df["segment"].value_counts().to_dict()
        seg_revenue = df.groupby("segment")["total_spend"].sum().round(2).to_dict()

        # Churn risk distribution breakdown
        churn_dist = df["churn_status"].value_counts().to_dict()

        self.kpis = {
            "total_customers": total_customers,
            "total_revenue": round(total_revenue, 2),
            "avg_spend_per_customer": round(avg_spend_per_customer, 2),
            "high_risk_customers": high_risk_count,
            "churn_rate_pct": high_risk_pct,
            "revenue_at_risk": round(revenue_at_risk, 2),
            "loyal_customers": loyal_count,
            "loyal_pct": loyal_pct,
            "segment_distribution": seg_counts,
            "segment_revenue": seg_revenue,
            "churn_distribution": churn_dist,
            "total_transactions": len(self.df)
        }

    def get_summary_payload(self):
        """Returns JSON-serializable dictionary for dashboard frontend."""
        return {
            "kpis": self.kpis,
            "customers": self.customer_profiles.to_dict(orient="records"),
            "segments": sorted(list(self.customer_profiles["segment"].unique())),
            "categories": sorted(list(self.df["category"].unique())) if "category" in self.df.columns else []
        }
