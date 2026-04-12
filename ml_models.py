import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score
import pickle
from database import get_db_connection

class SupplierMLModels:
    """Machine Learning models for supplier predictions"""
    
    def __init__(self):
        self.delay_model = None
        self.defect_model = None
        self.lead_time_model = None
        self.label_encoders = {}
        self.conn = None
    
    def prepare_delay_prediction_data(self):
        """Prepare data for Delay Prediction model
        Features: OTD rate, order qty, expected lead time, month, past delay frequency"""
        
        conn = get_db_connection()
        
        query = '''
            SELECT 
                po.supplier_id,
                po.order_quantity,
                (julianday(po.expected_delivery_date) - julianday(po.order_date)) as expected_lead_time,
                strftime('%m', po.order_date) as month,
                COALESCE(s.delay_flag, 0) as delay_flag
            FROM PurchaseOrders po
            LEFT JOIN Shipments s ON po.po_id = s.po_id
            WHERE po.status = 'Delivered'
        '''
        
        df = pd.read_sql_query(query, conn)
        
        # Add OTD rate per supplier
        supplier_otd = pd.read_sql_query('''
            SELECT 
                po.supplier_id,
                SUM(CASE WHEN COALESCE(s.delay_flag, 0) = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as otd_rate
            FROM PurchaseOrders po
            LEFT JOIN Shipments s ON po.po_id = s.po_id
            WHERE po.status = 'Delivered'
            GROUP BY po.supplier_id
        ''', conn)
        
        df = df.merge(supplier_otd, on='supplier_id', how='left')
        
        # Add past delay frequency
        supplier_delay_freq = df.groupby('supplier_id')['delay_flag'].mean().reset_index()
        supplier_delay_freq.columns = ['supplier_id', 'past_delay_frequency']
        
        df = df.merge(supplier_delay_freq, on='supplier_id', how='left')
        
        # Fill NaNs
        df = df.fillna(0)
        df['month'] = pd.to_numeric(df['month'])
        conn.close()
        
        return df
    
    def prepare_defect_prediction_data(self):
        """Prepare data for Defect Risk Prediction
        Features: Historical defect rate, batch size, product category, time since last audit"""
        
        conn = get_db_connection()
        
        query = '''
            SELECT 
                po.supplier_id,
                po.product_category,
                qr.batch_size,
                qr.time_since_last_audit_days,
                qr.defect_rate
            FROM PurchaseOrders po
            LEFT JOIN QualityRecords qr ON po.supplier_id = qr.supplier_id
            WHERE qr.defect_rate IS NOT NULL
        '''
        
        df = pd.read_sql_query(query, conn)
        
        # Add historical defect rate per supplier
        supplier_avg_defect = pd.read_sql_query('''
            SELECT supplier_id, AVG(defect_rate) as avg_defect_rate
            FROM QualityRecords
            GROUP BY supplier_id
        ''', conn)
        
        df = df.merge(supplier_avg_defect, on='supplier_id', how='left')
        
        # Create target: defect_rate > 5% = high risk
        df['high_defect_risk'] = (df['defect_rate'] > 5).astype(int)
        
        # Encode categorical
        if 'product_category' in df.columns:
            le = LabelEncoder()
            df['product_category_encoded'] = le.fit_transform(df['product_category'].fillna('Unknown'))
            self.label_encoders['product_category'] = le
        
        df = df.fillna(0)
        conn.close()
        
        return df
    
    def prepare_lead_time_prediction_data(self):
        """Prepare data for Lead Time Category Prediction
        Features: Past lead times, supplier distance (location), order urgency, seasonality
        Target: Early, On-time, Late"""
        
        conn = get_db_connection()
        
        query = '''
            SELECT 
                po.supplier_id,
                po.urgency,
                strftime('%m', po.order_date) as month,
                (julianday(po.actual_delivery_date) - julianday(po.expected_delivery_date)) as delay_days,
                (julianday(po.actual_delivery_date) - julianday(po.order_date)) as actual_lead_time
            FROM PurchaseOrders po
            WHERE po.status = 'Delivered'
        '''
        
        df = pd.read_sql_query(query, conn)
        
        # Get supplier location info
        locations = pd.read_sql_query('''
            SELECT supplier_id, location FROM Suppliers
        ''', conn)
        
        df = df.merge(locations, on='supplier_id', how='left')
        
        # Add past lead time average per supplier
        supplier_avg_lt = pd.read_sql_query('''
            SELECT supplier_id, 
                   AVG(julianday(actual_delivery_date) - julianday(order_date)) as avg_lead_time
            FROM PurchaseOrders
            WHERE status = 'Delivered'
            GROUP BY supplier_id
        ''', conn)
        
        df = df.merge(supplier_avg_lt, on='supplier_id', how='left')
        
        # Create target categories
        df['lead_time_category'] = pd.cut(df['delay_days'], 
                                         bins=[-float('inf'), -2, 2, float('inf')],
                                         labels=['Early', 'On-time', 'Late'])
        
        # Encode urgency
        le_urgency = LabelEncoder()
        df['urgency_encoded'] = le_urgency.fit_transform(df['urgency'].fillna('Medium'))
        self.label_encoders['urgency'] = le_urgency
        
        # Encode location
        le_location = LabelEncoder()
        df['location_encoded'] = le_location.fit_transform(df['location'].fillna('Unknown'))
        self.label_encoders['location'] = le_location
        
        # Encode lead time category
        le_category = LabelEncoder()
        df['lead_time_category_encoded'] = le_category.fit_transform(df['lead_time_category'].astype(str))
        self.label_encoders['lead_time_category'] = le_category
        
        df['month'] = pd.to_numeric(df['month'])
        # Fill NaN for numeric columns only, skip categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mean() if df[col].mean() == df[col].mean() else 0)
        
        conn.close()
        return df
    
    def train_delay_prediction_model(self):
        """Train Random Forest model for delay prediction"""
        df = self.prepare_delay_prediction_data()
        
        if len(df) < 10:
            print("Insufficient data for delay model training")
            return
        
        X = df[['order_quantity', 'expected_lead_time', 'month', 'otd_rate', 'past_delay_frequency']]
        y = df['delay_flag']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest
        self.delay_model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
        self.delay_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.delay_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        
        print(f"Delay Model - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
    
    def train_defect_prediction_model(self):
        """Train Logistic Regression model for defect risk prediction"""
        df = self.prepare_defect_prediction_data()
        
        if len(df) < 10:
            print("Insufficient data for defect model training")
            return
        
        X = df[['avg_defect_rate', 'batch_size', 'product_category_encoded', 'time_since_last_audit_days']]
        y = df['high_defect_risk']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Logistic Regression
        self.defect_model = LogisticRegression(random_state=42, max_iter=1000)
        self.defect_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.defect_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        
        print(f"Defect Model - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
    
    def train_lead_time_prediction_model(self):
        """Train Random Forest model for lead time category prediction"""
        df = self.prepare_lead_time_prediction_data()
        
        if len(df) < 10:
            print("Insufficient data for lead time model training")
            return
        
        X = df[['urgency_encoded', 'month', 'location_encoded', 'avg_lead_time']]
        y = df['lead_time_category_encoded']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest
        self.lead_time_model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
        self.lead_time_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.lead_time_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0, average='weighted')
        recall = recall_score(y_test, y_pred, zero_division=0, average='weighted')
        
        print(f"Lead Time Model - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
    
    def train_all_models(self):
        """Train all three models"""
        print("Training ML models...")
        self.train_delay_prediction_model()
        self.train_defect_prediction_model()
        self.train_lead_time_prediction_model()
        print("All models trained successfully!")
    
    def predict_delay_probability(self, supplier_id, order_quantity, expected_lead_time, month):
        """Predict probability of delay for a PO"""
        if self.delay_model is None:
            return None
        
        # Get supplier OTD and past delay frequency
        supplier_data = pd.read_sql_query('''
            SELECT 
                SUM(CASE WHEN s.delay_flag = 0 THEN 1 ELSE 0 END) / COUNT(*) * 100 as otd_rate,
                SUM(s.delay_flag) / COUNT(*) as past_delay_freq
            FROM PurchaseOrders po
            LEFT JOIN Shipments s ON po.po_id = s.po_id
            WHERE po.supplier_id = ? AND po.status = 'Delivered'
        ''', get_db_connection(), params=[supplier_id])
        
        otd_rate = supplier_data['otd_rate'].values[0] or 50
        past_delay_freq = supplier_data['past_delay_freq'].values[0] or 0.3
        
        X = np.array([[order_quantity, expected_lead_time, month, otd_rate, past_delay_freq]])
        probability = self.delay_model.predict_proba(X)[0][1] * 100
        
        return round(probability, 2)
    
    def predict_defect_risk_probability(self, supplier_id, batch_size, product_category, time_since_audit):
        """Predict probability of high defect rate"""
        if self.defect_model is None:
            return None
        
        # Get supplier average defect rate
        conn = get_db_connection()
        supplier_defect = pd.read_sql_query('''
            SELECT AVG(defect_rate) as avg_defect FROM QualityRecords WHERE supplier_id = ?
        ''', conn, params=[supplier_id])
        conn.close()
        
        avg_defect = supplier_defect['avg_defect'].values[0] or 2.0
        
        # Encode product category
        try:
            product_encoded = self.label_encoders['product_category'].transform([product_category])[0]
        except:
            product_encoded = 0
        
        X = np.array([[avg_defect, batch_size, product_encoded, time_since_audit]])
        probability = self.defect_model.predict_proba(X)[0][1] * 100
        
        return round(probability, 2)
    
    def predict_lead_time_category(self, supplier_id, urgency, month, location):
        """Predict lead time category"""
        if self.lead_time_model is None:
            return None
        
        # Get supplier average lead time
        conn = get_db_connection()
        supplier_lt = pd.read_sql_query('''
            SELECT AVG(julianday(actual_delivery_date) - julianday(order_date)) as avg_lt
            FROM PurchaseOrders WHERE supplier_id = ? AND status = 'Delivered'
        ''', conn, params=[supplier_id])
        conn.close()
        
        avg_lt = supplier_lt['avg_lt'].values[0] or 20
        
        # Encode categorical features
        urgency_encoded = self.label_encoders['urgency'].transform([urgency])[0]
        location_encoded = self.label_encoders['location'].transform([location])[0]
        
        X = np.array([[urgency_encoded, month, location_encoded, avg_lt]])
        prediction_encoded = self.lead_time_model.predict(X)[0]
        category = self.label_encoders['lead_time_category'].inverse_transform([prediction_encoded])[0]
        
        return category
    
    def close(self):
        pass  # Connections are closed after use in each method
