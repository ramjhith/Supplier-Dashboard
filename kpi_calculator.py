import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import get_db_connection

class KPICalculator:
    """Calculate all 8 KPIs for suppliers"""
    
    def __init__(self):
        self.conn = get_db_connection()
    
    def on_time_delivery_rate(self, supplier_id=None):
        """KPI 1: (Orders delivered on time / Total orders) × 100"""
        if supplier_id:
            query = '''
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN s.delay_flag = 0 THEN 1 ELSE 0 END) as on_time
                FROM PurchaseOrders po
                JOIN Shipments s ON po.po_id = s.po_id
                WHERE po.supplier_id = ? AND po.status = 'Delivered'
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = '''
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN s.delay_flag = 0 THEN 1 ELSE 0 END) as on_time
                FROM PurchaseOrders po
                JOIN Shipments s ON po.po_id = s.po_id
                WHERE po.status = 'Delivered'
            '''
            result = pd.read_sql_query(query, self.conn)
        
        if result['total'].values[0] == 0:
            return 0
        return (result['on_time'].values[0] / result['total'].values[0]) * 100
    
    def defect_rate(self, supplier_id=None):
        """KPI 2: (Rejected quantity / Total received quantity) × 100"""
        if supplier_id:
            query = '''
                SELECT AVG(defect_rate) as avg_defect FROM QualityRecords WHERE supplier_id = ?
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = 'SELECT AVG(defect_rate) as avg_defect FROM QualityRecords'
            result = pd.read_sql_query(query, self.conn)
        
        return result['avg_defect'].values[0] or 0
    
    def average_lead_time(self, supplier_id=None):
        """KPI 3: Average days from PO placement to receipt"""
        if supplier_id:
            query = '''
                SELECT AVG((julianday(actual_delivery_date) - julianday(order_date))) as avg_days
                FROM PurchaseOrders 
                WHERE supplier_id = ? AND status = 'Delivered'
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = '''
                SELECT AVG((julianday(actual_delivery_date) - julianday(order_date))) as avg_days
                FROM PurchaseOrders WHERE status = 'Delivered'
            '''
            result = pd.read_sql_query(query, self.conn)
        
        return result['avg_days'].values[0] or 0
    
    def lead_time_variability(self, supplier_id=None):
        """KPI 4: Standard deviation of lead times per supplier"""
        if supplier_id:
            query = '''
                SELECT (julianday(actual_delivery_date) - julianday(order_date)) as lead_time
                FROM PurchaseOrders 
                WHERE supplier_id = ? AND status = 'Delivered'
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = '''
                SELECT (julianday(actual_delivery_date) - julianday(order_date)) as lead_time
                FROM PurchaseOrders WHERE status = 'Delivered'
            '''
            result = pd.read_sql_query(query, self.conn)
        
        if len(result) < 2:
            return 0
        return result['lead_time'].std()
    
    def cost_variance(self, supplier_id=None):
        """KPI 5: ((Actual cost - Quoted cost) / Quoted cost) × 100"""
        if supplier_id:
            query = '''
                SELECT AVG(((actual_cost - quoted_cost) / quoted_cost) * 100) as avg_variance
                FROM PurchaseOrders 
                WHERE supplier_id = ? AND quoted_cost > 0
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = '''
                SELECT AVG(((actual_cost - quoted_cost) / quoted_cost) * 100) as avg_variance
                FROM PurchaseOrders WHERE quoted_cost > 0
            '''
            result = pd.read_sql_query(query, self.conn)
        
        return result['avg_variance'].values[0] or 0
    
    def supplier_risk_score(self, supplier_id):
        """KPI 6: Weighted composite (delay frequency + defect rate + cost variance)
        Range: 0-100, higher = more risk"""
        
        otd = self.on_time_delivery_rate(supplier_id)
        defect = self.defect_rate(supplier_id)
        cost_var = abs(self.cost_variance(supplier_id))
        
        # Normalize to 0-100 scale
        delay_risk = (100 - otd)  # 0-100
        defect_risk = min(defect * 10, 100)  # scale defect rate
        cost_risk = min(cost_var, 100)  # cap at 100
        
        # Weighted average: 40% delay, 35% defect, 25% cost
        risk_score = (delay_risk * 0.4) + (defect_risk * 0.35) + (cost_risk * 0.25)
        
        return round(min(risk_score, 100), 2)
    
    def po_acknowledgment_rate(self, supplier_id=None):
        """KPI 7: (POs acknowledged within 24h / Total POs) × 100"""
        if supplier_id:
            query = '''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN acknowledged = 1 AND acknowledgment_time <= 24 THEN 1 ELSE 0 END) as acked_24h
                FROM PurchaseOrders
                WHERE supplier_id = ?
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = '''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN acknowledged = 1 AND acknowledgment_time <= 24 THEN 1 ELSE 0 END) as acked_24h
                FROM PurchaseOrders
            '''
            result = pd.read_sql_query(query, self.conn)
        
        if result['total'].values[0] == 0:
            return 0
        return (result['acked_24h'].values[0] / result['total'].values[0]) * 100
    
    def response_time_to_queries(self, supplier_id=None):
        """KPI 8: Average hours taken by supplier to respond to critical requests"""
        if supplier_id:
            query = '''
                SELECT AVG(response_time) as avg_response
                FROM CommunicationLogs
                WHERE supplier_id = ?
            '''
            result = pd.read_sql_query(query, self.conn, params=[supplier_id])
        else:
            query = 'SELECT AVG(response_time) as avg_response FROM CommunicationLogs'
            result = pd.read_sql_query(query, self.conn)
        
        return result['avg_response'].values[0] or 0
    
    def get_all_kpis_for_supplier(self, supplier_id):
        """Get all 8 KPIs for a specific supplier"""
        return {
            'On-Time Delivery Rate (%)': round(self.on_time_delivery_rate(supplier_id), 2),
            'Defect Rate (%)': round(self.defect_rate(supplier_id), 2),
            'Avg Lead Time (days)': round(self.average_lead_time(supplier_id), 2),
            'Lead Time Variability (std dev)': round(self.lead_time_variability(supplier_id), 2),
            'Cost Variance (%)': round(self.cost_variance(supplier_id), 2),
            'Supplier Risk Score (0-100)': self.supplier_risk_score(supplier_id),
            'PO Acknowledgment Rate (%)': round(self.po_acknowledgment_rate(supplier_id), 2),
            'Response Time to Queries (hours)': round(self.response_time_to_queries(supplier_id), 2)
        }
    
    def get_all_suppliers_kpis(self):
        """Get KPIs for all suppliers"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT supplier_id, name FROM Suppliers')
        suppliers = cursor.fetchall()
        
        all_kpis = []
        for supplier_id, name in suppliers:
            kpi_dict = self.get_all_kpis_for_supplier(supplier_id)
            kpi_dict['Supplier'] = name
            kpi_dict['Supplier ID'] = supplier_id
            all_kpis.append(kpi_dict)
        
        return pd.DataFrame(all_kpis)
    
    def close(self):
        self.conn.close()
