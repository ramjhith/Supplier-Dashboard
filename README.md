# 🚀 Supplier Relationship Management (SRM) Dashboard

**Problem Statement P6**: Build an interactive dashboard to improve supplier reliability, track supplier performance, reduce delays, and optimize costs through real-time KPI monitoring and AI/ML predictions.

---

## 📊 Project Overview

This is a comprehensive Supplier Relationship Management (SRM) dashboard featuring:

### ✅ **8 Key Performance Indicators (KPIs)**
1. **On-Time Delivery Rate** (%) - Identifies unreliable suppliers
2. **Defect Rate** (%) - Flags low-quality suppliers
3. **Average Supplier Lead Time** (days) - Benchmarks performance
4. **Lead Time Variability** (std dev) - Highlights inconsistent suppliers
5. **Cost Variance** (%) - Detects cost overruns
6. **Supplier Risk Score** (0-100) - Composite risk assessment
7. **PO Acknowledgment Rate** (%) - Measures collaboration
8. **Response Time to Queries** (hours) - Assesses communication efficiency

### 🤖 **3 Machine Learning Models**
1. **Delay Prediction** (Random Forest)
   - Predicts probability of order delay
   - Features: OTD rate, order qty, expected lead time, month, past delays
   - Output: Probability (%)

2. **Defect Risk Prediction** (Logistic Regression)
   - Predicts probability of high defect rate (>5%)
   - Features: Historical defect rate, batch size, product category, audit recency
   - Output: Probability (%)

3. **Lead Time Category** (Random Forest)
   - Classifies delivery as Early, On-time, or Late
   - Features: Past lead times, supplier location, urgency, seasonality
   - Output: Category

### 📈 **Interactive Visualizations**
- **On-Time Delivery Rate by Supplier** (Bar Chart)
- **Defect Rate by Supplier** (Bar Chart)
- **Lead Time Trend** (Line Chart with trend)
- **Cost Variance Analysis** (Bar Chart)
- **Supplier Risk Scores** (Bar Chart)
- **Rejection Reasons** (Pie Chart)
- **Open Purchase Orders** (Data Table)

### 🎛️ **Interactive Features**
- **Supplier Filter** - View all or specific supplier data
- **Date Range Filter** - Analyze data by time period
- **Status Filter** - Filter by Delivered/Pending orders
- **Drill-Down** - Click supplier to see detailed predictions
- **Real-Time Updates** - All visualizations update dynamically

---

## 📁 Project Structure

```
P6_SupplierDashboard/
├── app.py                 # Main Dash application
├── database.py           # SQLite database setup & sample data
├── kpi_calculator.py     # KPI calculation engine
├── ml_models.py          # ML prediction models
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
├── run.sh               # Run script
├── README.md            # This file
└── supplier_data.db     # SQLite database (auto-generated)
```

---

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip or conda

### Quick Setup

#### **Option 1: Automated Setup (macOS/Linux)**
```bash
cd P6_SupplierDashboard
chmod +x setup.sh
./setup.sh
```

#### **Option 2: Manual Setup**
```bash
cd P6_SupplierDashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Running the Dashboard

### Start the Application
```bash
cd P6_SupplierDashboard
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

### Access the Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:8050/
```

---

## 📊 Sample Data

The dashboard automatically generates realistic sample data:
- **12 Suppliers** across different countries
- **100 Purchase Orders** (70% delivered, 30% pending)
- **Quality Records** with varying defect rates
- **Communication Logs** tracking response times
- **Cost and Lead Time Variations**

**Note**: Database is recreated on each app start. To persist data, modify `init_database()` in `database.py`.

---

## 🎯 Key Features Explained

### 1. **KPI Dashboard**
Displays 4 main metrics at the top:
- On-Time Delivery Rate (Green = >80%, Yellow = 60-80%, Red = <60%)
- Defect Rate (Green = <2%, Yellow = 2-4%, Red = >4%)
- Average Lead Time (in days)
- Risk Score (0-100, color-coded by risk level)

### 2. **Supplier Performance Charts**
- **Bar Charts**: Quickly identify top and bottom performers
- **Trend Line**: Visualize performance over time
- **Color Coding**: Instant visual feedback on performance

### 3. **ML Predictions** (Single Supplier Only)
When a specific supplier is selected:
- **Delay Risk %**: Tells you the probability next order will be late
- **Quality Risk %**: Probability of defects exceeding 5%
- **Lead Time Category**: Expected delivery performance

### 4. **Open POs Table**
Shows next 20 purchase orders with:
- Supplier name
- PO number
- Order & expected delivery dates
- Order quantity
- Current status

---

## 🤖 ML Model Details

### **Delay Prediction Model**
```
Algorithm: Random Forest Classifier (50 trees, max_depth=10)
Training: On historical supplier delivery data
Features:
  - Order quantity (numerical)
  - Expected lead time (numerical)
  - Order month (categorical)
  - Supplier OTD rate (numerical)
  - Past delay frequency (numerical)
Output: Probability of delay (0-100%)
```

### **Defect Risk Model**
```
Algorithm: Logistic Regression
Training: On quality records
Features:
  - Historical defect rate
  - Batch size
  - Product category (encoded)
  - Time since last audit
Output: Probability of high defect rate (0-100%)
Target: Defect rate > 5% = HIGH RISK
```

### **Lead Time Category Model**
```
Algorithm: Random Forest Classifier (50 trees, max_depth=10)
Training: On historical lead times
Features:
  - Order urgency (encoded)
  - Order month (numerical)
  - Supplier location (encoded)
  - Supplier average lead time
Output: Category (Early / On-time / Late)
```

---

## 📈 Business Insights

### **How to Use the Dashboard**

1. **Identify Problem Suppliers**
   - Look at Supplier Risk Score chart
   - Red suppliers (>75 score) need immediate attention
   - Yellow suppliers (50-75) require monitoring

2. **Analyze Trends**
   - Use date filters to identify seasonal issues
   - Lead Time Trend shows if performance is improving/declining
   - Cost Variance reveals pricing issues

3. **Make Data-Driven Decisions**
   - Filter by supplier to see their detailed ML predictions
   - High delay risk (>60%) → expedite order or switch supplier
   - High quality risk (>50%) → schedule incoming inspection
   - Cost variance issues → renegotiate SLA

4. **Track Performance Improvements**
   - Monitor OTD improvements after supplier meetings
   - Track defect rate post-quality audits
   - Verify communication improvements via response times

---

## 🔗 Database Schema

### **Suppliers Table**
```sql
supplier_id (PRIMARY KEY)
name (UNIQUE)
location
contact
risk_category
created_date
```

### **PurchaseOrders Table**
```sql
po_id (PRIMARY KEY)
supplier_id (FOREIGN KEY)
order_date
expected_delivery_date
actual_delivery_date
quoted_cost / actual_cost
order_quantity
product_category
urgency (Low/Medium/High/Critical)
acknowledged
acknowledgment_time
status (Pending/Delivered)
```

### **Shipments Table**
```sql
shipment_id (PRIMARY KEY)
po_id (FOREIGN KEY)
shipment_date / receipt_date
delay_flag (BOOLEAN)
delay_days
```

### **QualityRecords Table**
```sql
quality_id (PRIMARY KEY)
supplier_id / po_id (FOREIGN KEYS)
defect_rate (%)
rejection_reason
batch_size
audit_date
time_since_last_audit_days
```

### **CommunicationLogs Table**
```sql
comm_id (PRIMARY KEY)
supplier_id (FOREIGN KEY)
communication_type (Email/Phone/Chat/Portal)
query_time / response_time
resolved (BOOLEAN)
```

---

## 🛠️ Customization

### Add New Suppliers
Edit `database.py`, modify `suppliers_data` list:
```python
suppliers_data = [
    ('New Supplier Name', 'Country - City'),
    # ... more suppliers
]
```

### Adjust KPI Weights
Edit `kpi_calculator.py`, modify `supplier_risk_score()`:
```python
# Change weights: (delay_risk * 0.4) + (defect_risk * 0.35) + (cost_risk * 0.25)
risk_score = (delay_risk * 0.5) + (defect_risk * 0.3) + (cost_risk * 0.2)
```

### Modify ML Model Parameters
Edit `ml_models.py`, adjust model hyperparameters:
```python
# Random Forest: change n_estimators, max_depth
self.delay_model = RandomForestClassifier(n_estimators=100, max_depth=15)
```

---

## 📋 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| dash | 2.14.2 | Web framework for dashboard |
| plotly | 5.17.0 | Interactive visualizations |
| pandas | 2.1.3 | Data manipulation |
| numpy | 1.24.3 | Numerical computing |
| scikit-learn | 1.3.2 | ML models & preprocessing |
| gunicorn | 21.2.0 | WSGI server (production) |

---

## 🐛 Troubleshooting

### Issue: "No module named 'dash'"
```bash
pip install dash==2.14.2
```

### Issue: Database locked error
- Delete `supplier_data.db` and restart the app
- App will auto-generate new database

### Issue: ML models not trained
- Check console for warning messages
- Ensure sample data was generated (>10 records)
- Restart the application

### Issue: Port 8050 already in use
```bash
python app.py --port=8051
```

---

## 📸 Dashboard Preview

**Top Section**: 4 KPI Cards showing overall metrics
**Middle Section**: 6 Interactive Charts
- OTD Rate by Supplier
- Defect Rate by Supplier
- Lead Time Trend
- Cost Variance
- Risk Scores
- Rejection Reasons

**Bottom Section**: 
- ML Predictions (when supplier is selected)
- Open PO Table (next 20 orders)

---

## 🎓 Learning Resources

- [Dash Documentation](https://dash.plotly.com/)
- [Plotly Charts](https://plotly.com/python/)
- [Scikit-learn Models](https://scikit-learn.org/stable/)
- [Pandas Data Manipulation](https://pandas.pydata.org/docs/)
- [SQLite Basics](https://www.sqlite.org/cli.html)

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the database schema
3. Check console logs for error messages
4. Verify all dependencies are installed: `pip list`

---

## 📝 Notes

- **Data Persistence**: Database is recreated on each app restart. To keep data, remove the drop table statements in `init_database()`.
- **Production Deployment**: Use Gunicorn instead of Flask dev server: `gunicorn app:server`
- **ML Model Update**: Models are retrained each time the app starts. For persistence, use `pickle` to save models.
- **Scalability**: For 1000+ suppliers, consider using PostgreSQL or MongoDB instead of SQLite.

---

## ✅ Checklist for P6 Completion

- [x] 8 KPIs calculated and displayed
- [x] 3 ML prediction models (Random Forest × 2, Logistic Regression)
- [x] Interactive Dash dashboard
- [x] Multiple visualizations (6+ charts)
- [x] Filters (supplier, date range, status)
- [x] Drill-down capability (ML predictions per supplier)
- [x] Realistic sample data (100 POs, 12 suppliers)
- [x] Complete database schema
- [x] Performance metrics & alerts
- [x] Production-ready code with documentation

---

**Created**: April 2026
**Status**: ✅ Complete & Ready for Demonstration
