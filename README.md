# RetailPulse AI: Retail Customer Segregation & Churn Intelligence

An end-to-end prototype software designed for retail store owners to:
1. **Segregate Customers** based on their purchasing habits using **RFM (Recency, Frequency, Monetary) Clustering**.
2. **Predict Churn Hazard** by identifying customers about to leave vs. loyal regulars.
3. **Prescribe Margin-Optimized Retention Offers** tailored to each customer segment with ready-to-send SMS/WhatsApp campaign templates.

---

## 🎓 Academic Framework & Methodology (For College Presentation)

### 1. Customer Segmentation: RFM Quintile Matrix
Retail transactions are non-contractual (customers don't explicitly cancel an account; they simply stop visiting). To quantify purchasing habits, the engine calculates:
* **Recency ($R$):** Days since the customer's last store purchase relative to the reference date.
* **Frequency ($F$):** Total number of distinct purchases / visits.
* **Monetary ($M$):** Total lifetime spend (₹).

Each dimension is binned into quintiles ($1$ to $5$ score, where $5$ is best).
From this, customers are segregated into 6 actionable personas:
- **Champions & VIPs ($R \ge 4, F \ge 4, M \ge 4$):** High spend, high frequency, recent shoppers.
- **Loyal Customers ($R \ge 3, F \ge 3, M \ge 2$):** Consistent repeat buyers.
- **New & Promising ($R \ge 4, F \le 2$):** Recent buyers needing 2nd-purchase nurture.
- **At-Risk High-Value ($R \le 2, F \ge 3 \text{ or } M \ge 4$):** Previously big spenders who have gone silent!
- **Needs Attention ($R = 3, F \ge 2$):** Slipping visit intervals.
- **Hibernating / Inactive ($R \le 2, F \le 2$):** Low engagement, prolonged absence.

---

### 2. Churn Prediction: Inter-Purchase Cycle Hazard Model
Instead of treating churn as a static cutoff (e.g., "inactive for 30 days"), the algorithm calculates each customer's individual historical visit frequency cycle:
$$\bar{T}_{\text{cycle}} = \frac{1}{N-1} \sum_{i=1}^{N-1} (t_{i+1} - t_i)$$
The churn hazard ratio is defined as:
$$\text{Cycle Ratio} = \frac{\text{Recency}}{\bar{T}_{\text{cycle}}}$$
If a customer usually visits every $10$ days, a $30$-day absence is a severe churn signal ($\text{Ratio} = 3.0$). For a customer who normally visits every $60$ days, a $30$-day gap is normal ($\text{Ratio} = 0.5$).
The hazard is converted into a calibrated probability $P(\text{churn}) \in [5\%, 98\%]$ using a logistic sigmoid curve with penalty adjustments for single-visit drop-offs.

---

### 3. Prescriptive Offer Recommendation Engine
Giving discounts to VIPs wastes store profit margins. Giving loyalty points to churning customers fails to bring them back.
The engine matches offers strategically:
* **VIPs & Champions:** Value-add perks (0% margin loss: Double points, exclusive gift bag, VIP lounge access).
* **Loyal Shoppers:** Basket boosters (₹500 off ₹3,000+ across complementary departments).
* **New Shoppers:** Second-purchase habit builder (15% off next visit within 10 days).
* **At-Risk (High Spenders):** High-urgency win-back coupon (20% off favorite category with 7-day expiration).
* **Hibernating / Dormant:** Re-activation clearance promo (Flat ₹750 off ₹2,500+).

---

## 🚀 How to Run the Prototype

You now have **two versions** ready to run depending on your presentation audience:

### 1. Simple College Version (Bare-Bones & Authentic)
- **Batch File**: Double-click **`run_dashboard_simple.bat`**
- **URL**: `http://127.0.0.1:5000`
- **Features**: Clean, straightforward student UI with numbered tabs, standard tables, and easy-to-explain styling.

### 2. Modern SaaS Version (High-Effort Enterprise Demo)
- **Batch File**: Double-click **`run_dashboard_modern.bat`**
- **URL**: `http://127.0.0.1:5000/modern`
- **Features**: Sleek Tailwind CSS UI, interactive bubble scatter plot, persona cards, and Lucide icons.

*(You can also seamlessly toggle between both versions directly using the button in the top navigation bar!)*

---

## 📝 How to Add New Customers & Transactions

There are 3 ways to add customer data into the software:

### Method 1: Interactive UI Modal (Best for College Live Demo)
1. Open the dashboard at `http://127.0.0.1:5000`.
2. Click the green **`+ Add Customer`** button in the top navigation bar.
3. Enter the customer's name, phone, product category, and spend amount.
4. Choose their shopping behavior:
   - **Regular Repeat Shopper, Visited Recently** (Tests VIP / Loyal classification).
   - **First-Time Buyer, Visited This Week** (Tests New & Promising conversion).
   - **High-Value Shopper, Inactive 90+ Days** (Tests Churn Early Warning & Win-Back Offer!).
5. Click **"Add & Classify Customer"**. The dashboard instantly re-computes the entire store's metrics and opens that customer's diagnostics card on screen!

---

### Method 2: Upload a Custom POS CSV
1. Click **"Upload POS CSV"** in the top navigation.
2. Select any CSV file containing these required columns:
   - `customer_id` (e.g. `CUST-1001`)
   - `timestamp` (e.g. `2026-10-15 14:30:00`)
   - `amount` (e.g. `84.50`)
   *(Optional columns: `customer_name`, `category`, `customer_phone`)*
3. Click **"Process CSV"** to load it.

---

### Method 3: Edit the CSV Directly in Excel or VS Code
1. Open `sample_transactions.csv` in Excel or any text editor.
2. Add rows at the bottom following the existing columns:
   ```csv
   TXN-9999,CUST-2001,John Doe,+91 99999 00000,john@example.com,2026-11-05 14:00:00,Electronics & Gadgets,2,240.00,Credit Card
   ```
3. Save the file and refresh your browser.

---

## 🖥️ What to Demonstrate to Your Professor

1. **Executive KPI Header:**
   - Point out **"Revenue at Risk"** (e.g. ~₹8,00,000+) vs. **"Gross Spend"**. Explain that retail owners care most about the financial impact of customer loss.
2. **Customer Segmentation Tab:**
   - Show the **RFM Bubble Scatter Chart** (Recency vs Spend, sized by Frequency).
   - Explain how customers naturally separate into VIPs, Loyal regulars, and slipping cohorts.
3. **Churn Radar Tab:**
   - Filter by **"High Risk Only"**.
   - Show how the algorithm detects customers whose days of inactivity exceed their normal purchase cycle.
4. **AI Offer Recommendation Engine:**
   - Show how different promotional strategies and ready-to-send SMS/WhatsApp copy are generated for each segment.
   - Click **"Export Campaign CSV"** to demonstrate integration readiness for marketing tools.
5. **Customer Directory & Individual Drilldown:**
   - Click on any customer to show their deep profile: RFM score breakdown ($R/F/M$), churn diagnostic explanation, and their personalized offer.
6. **Live Data Controls:**
   - Click **"Regenerate Demo Data"** to show real-time dynamic re-calculation.
   - Show the **"Upload POS CSV"** feature to demonstrate that real store transaction data can be ingested.
