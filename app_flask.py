from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from database import init_database, populate_sample_data, get_db_connection
from kpi_calculator import KPICalculator
from ml_models import SupplierMLModels
import json

app = Flask(__name__)

# Initialize database and models at startup
print("Initializing database...")
init_database()
populate_sample_data()

print("Training ML models...")
ml_models = SupplierMLModels()
ml_models.train_all_models()

# ============= HELPER FUNCTIONS =============

def get_suppliers():
    """Get all suppliers"""
    conn = get_db_connection()
    suppliers = pd.read_sql_query('SELECT supplier_id, name FROM Suppliers ORDER BY name', conn)
    conn.close()
    return suppliers.to_dict('records')

def get_kpis_data(supplier_id='all', start_date=None, end_date=None):
    """Get KPI data"""
    conn = get_db_connection()
    kpi_calc = KPICalculator()
    
    if supplier_id == 'all':
        all_kpis = kpi_calc.get_all_suppliers_kpis()
        conn.close()
        return all_kpis.to_dict('records')
    else:
        kpis = kpi_calc.get_all_kpis_for_supplier(int(supplier_id))
        conn.close()
        return kpis

def get_charts_data(supplier_id='all', start_date=None, end_date=None, status_filter='all'):
    """Get chart data"""
    conn = get_db_connection()
    
    where_clause = "WHERE 1=1"
    params = []
    
    if supplier_id != 'all':
        where_clause += " AND po.supplier_id = ?"
        params.append(supplier_id)
    
    if status_filter != 'all':
        where_clause += " AND po.status = ?"
        params.append(status_filter)
    
    if start_date:
        where_clause += " AND po.order_date >= ?"
        params.append(start_date)
    
    if end_date:
        where_clause += " AND po.order_date <= ?"
        params.append(end_date)
    
    charts = {}
    
    # OTD Chart
    try:
        otd_query = f'''
            SELECT s.name, 
                   SUM(CASE WHEN COALESCE(ship.delay_flag, 0) = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as otd
            FROM PurchaseOrders po
            JOIN Suppliers s ON po.supplier_id = s.supplier_id
            LEFT JOIN Shipments ship ON po.po_id = ship.po_id
            {where_clause} AND po.status = 'Delivered'
            GROUP BY s.name
            ORDER BY otd DESC
        '''
        otd_data = pd.read_sql_query(otd_query, conn, params=params)
        charts['otd'] = {
            'labels': otd_data['name'].tolist(),
            'data': otd_data['otd'].tolist()
        }
    except:
        charts['otd'] = {'labels': [], 'data': []}
    
    # Defect Chart
    try:
        defect_query = f'''
            SELECT s.name, AVG(qr.defect_rate) as defect_rate
            FROM PurchaseOrders po
            JOIN Suppliers s ON po.supplier_id = s.supplier_id
            LEFT JOIN QualityRecords qr ON po.supplier_id = qr.supplier_id
            {where_clause}
            GROUP BY s.name
            ORDER BY defect_rate DESC
        '''
        defect_data = pd.read_sql_query(defect_query, conn, params=params)
        charts['defect'] = {
            'labels': defect_data['name'].tolist(),
            'data': defect_data['defect_rate'].fillna(0).tolist()
        }
    except:
        charts['defect'] = {'labels': [], 'data': []}
    
    # Lead Time Trend
    try:
        lt_query = f'''
            SELECT DATE(po.order_date) as date, 
                   AVG(julianday(po.actual_delivery_date) - julianday(po.order_date)) as avg_lt
            FROM PurchaseOrders po
            {where_clause} AND po.status = 'Delivered'
            GROUP BY DATE(po.order_date)
            ORDER BY date
            LIMIT 30
        '''
        lt_data = pd.read_sql_query(lt_query, conn, params=params)
        charts['lead_time'] = {
            'labels': lt_data['date'].tolist(),
            'data': lt_data['avg_lt'].tolist()
        }
    except:
        charts['lead_time'] = {'labels': [], 'data': []}
    
    # Cost Variance
    try:
        cost_query = f'''
            SELECT s.name, AVG(((po.actual_cost - po.quoted_cost) / po.quoted_cost) * 100) as cost_var
            FROM PurchaseOrders po
            JOIN Suppliers s ON po.supplier_id = s.supplier_id
            {where_clause} AND po.quoted_cost > 0
            GROUP BY s.name
            ORDER BY ABS(cost_var) DESC
        '''
        cost_data = pd.read_sql_query(cost_query, conn, params=params)
        charts['cost'] = {
            'labels': cost_data['name'].tolist(),
            'data': cost_data['cost_var'].fillna(0).tolist()
        }
    except:
        charts['cost'] = {'labels': [], 'data': []}
    
    # Supplier Risk Score
    try:
        from kpi_calculator import KPICalculator
        kpi_calc = KPICalculator()
        
        if supplier_id != 'all':
            supplier_name = pd.read_sql_query(
                'SELECT name FROM Suppliers WHERE supplier_id = ?',
                conn, params=[int(supplier_id)]
            )
            if len(supplier_name) > 0:
                risk_data = kpi_calc.get_all_kpis_for_supplier(int(supplier_id))
                charts['risk_score'] = {
                    'labels': [supplier_name['name'].values[0]],
                    'data': [risk_data['Supplier Risk Score (0-100)']],
                    'riskLevel': 'High' if risk_data['Supplier Risk Score (0-100)'] > 60 else 'Medium' if risk_data['Supplier Risk Score (0-100)'] > 30 else 'Low'
                }
            else:
                charts['risk_score'] = {'labels': [], 'data': [], 'riskLevel': 'N/A'}
        else:
            all_kpis = kpi_calc.get_all_suppliers_kpis()
            charts['risk_score'] = {
                'labels': all_kpis['Supplier'].tolist(),
                'data': all_kpis['Supplier Risk Score (0-100)'].tolist(),
                'riskLevel': 'Mixed'
            }
    except Exception as e:
        print(f"Error in risk score chart: {e}")
        charts['risk_score'] = {'labels': [], 'data': [], 'riskLevel': 'N/A'}
    
    conn.close()
    return charts

def get_open_pos(supplier_id='all', limit=15):
    """Get open purchase orders"""
    conn = get_db_connection()
    
    where_clause = "WHERE 1=1"
    params = []
    
    if supplier_id != 'all':
        where_clause += " AND po.supplier_id = ?"
        params.append(supplier_id)
    
    query = f'''
        SELECT s.name, po.po_id, po.order_date, po.expected_delivery_date, 
               po.order_quantity, po.status
        FROM PurchaseOrders po
        JOIN Suppliers s ON po.supplier_id = s.supplier_id
        {where_clause}
        ORDER BY po.expected_delivery_date ASC
        LIMIT {limit}
    '''
    
    pos = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return pos.to_dict('records')

def get_ml_predictions(supplier_id):
    """Get ML predictions for supplier"""
    try:
        conn = get_db_connection()
        supplier_name = pd.read_sql_query(
            'SELECT name, location FROM Suppliers WHERE supplier_id = ?', 
            conn, 
            params=[supplier_id]
        )
        
        if len(supplier_name) == 0:
            conn.close()
            return None
        
        name = supplier_name['name'].values[0]
        location = supplier_name['location'].values[0]
        
        recent_po = pd.read_sql_query('''
            SELECT order_quantity, 
                   julianday(expected_delivery_date) - julianday(order_date) as expected_lt,
                   strftime('%m', order_date) as month,
                   product_category
            FROM PurchaseOrders
            WHERE supplier_id = ?
            ORDER BY order_date DESC
            LIMIT 1
        ''', conn, params=[supplier_id])
        
        conn.close()
        
        if len(recent_po) == 0:
            return None
        
        qty = recent_po['order_quantity'].values[0]
        exp_lt = recent_po['expected_lt'].values[0]
        month = int(recent_po['month'].values[0])
        category = recent_po['product_category'].values[0]
        
        ml_models_local = SupplierMLModels()
        ml_models_local.train_all_models()
        
        delay_prob = ml_models_local.predict_delay_probability(supplier_id, qty, exp_lt, month) or 0
        defect_prob = ml_models_local.predict_defect_risk_probability(supplier_id, qty, category, 30) or 0
        lt_cat = ml_models_local.predict_lead_time_category(supplier_id, 'Medium', month, location) or 'Unknown'
        
        return {
            'supplier_name': name,
            'delay_risk': round(delay_prob, 2),
            'quality_risk': round(defect_prob, 2),
            'lead_time': lt_cat
        }
    except Exception as e:
        print(f"Error in ML predictions: {e}")
        return None

# ============= ROUTES =============

@app.route('/')
def index():
    """Main dashboard page"""
    suppliers = get_suppliers()
    return render_template('index.html', suppliers=suppliers)

@app.route('/api/suppliers')
def api_suppliers():
    """Get suppliers API"""
    suppliers = get_suppliers()
    return jsonify(suppliers)

@app.route('/api/kpis')
def api_kpis():
    """Get KPIs API"""
    supplier_id = request.args.get('supplier_id', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    kpis = get_kpis_data(supplier_id, start_date, end_date)
    return jsonify(kpis)

@app.route('/api/charts')
def api_charts():
    """Get charts data API"""
    supplier_id = request.args.get('supplier_id', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'all')
    
    charts = get_charts_data(supplier_id, start_date, end_date, status)
    return jsonify(charts)

@app.route('/api/open-pos')
def api_open_pos():
    """Get open POs API"""
    supplier_id = request.args.get('supplier_id', 'all')
    limit = request.args.get('limit', 15, type=int)
    
    pos = get_open_pos(supplier_id, limit)
    return jsonify(pos)

@app.route('/api/ml-predictions/<int:supplier_id>')
def api_ml_predictions(supplier_id):
    """Get ML predictions API"""
    predictions = get_ml_predictions(supplier_id)
    if predictions:
        return jsonify(predictions)
    return jsonify({'error': 'No predictions available'}), 404

@app.route('/api/summary')
def api_summary():
    """Get summary statistics"""
    supplier_id = request.args.get('supplier_id', 'all')
    
    conn = get_db_connection()
    kpi_calc = KPICalculator()
    
    if supplier_id == 'all':
        all_kpis = kpi_calc.get_all_suppliers_kpis()
        summary = {
            'otd': round(all_kpis['On-Time Delivery Rate (%)'].mean(), 1),
            'defect': round(all_kpis['Defect Rate (%)'].mean(), 1),
            'lead_time': round(all_kpis['Avg Lead Time (days)'].mean(), 0),
            'risk_score': round(all_kpis['Supplier Risk Score (0-100)'].mean(), 0)
        }
    else:
        kpis = kpi_calc.get_all_kpis_for_supplier(int(supplier_id))
        summary = {
            'otd': round(kpis['On-Time Delivery Rate (%)'], 1),
            'defect': round(kpis['Defect Rate (%)'], 1),
            'lead_time': round(kpis['Avg Lead Time (days)'], 0),
            'risk_score': round(kpis['Supplier Risk Score (0-100)'], 0)
        }
    
    conn.close()
    return jsonify(summary)

# ============= RUN APP =============

if __name__ == '__main__':
    print("\n" + "="*70)
    print("Supplier Relationship Management Dashboard - Flask Edition")
    print("="*70)
    print("\nDashboard ready!")
    print("Open your browser and go to: http://127.0.0.1:5000/")
    print("\n" + "="*70 + "\n")
    app.run(debug=False, port=5000, host='127.0.0.1')
