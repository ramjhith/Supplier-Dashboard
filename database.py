import sqlite3
import os
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np

DB_PATH = 'supplier_data.db'

def init_database():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop existing tables for clean start
    cursor.execute('DROP TABLE IF EXISTS CommunicationLogs')
    cursor.execute('DROP TABLE IF EXISTS QualityRecords')
    cursor.execute('DROP TABLE IF EXISTS Shipments')
    cursor.execute('DROP TABLE IF EXISTS PurchaseOrders')
    cursor.execute('DROP TABLE IF EXISTS Suppliers')
    
    # Suppliers Table
    cursor.execute('''
        CREATE TABLE Suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT,
            contact TEXT,
            risk_category TEXT DEFAULT 'Medium',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Purchase Orders Table
    cursor.execute('''
        CREATE TABLE PurchaseOrders (
            po_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            order_date DATE,
            expected_delivery_date DATE,
            actual_delivery_date DATE,
            quoted_cost REAL,
            actual_cost REAL,
            order_quantity INTEGER,
            product_category TEXT,
            urgency TEXT,
            acknowledged BOOLEAN DEFAULT 0,
            acknowledgment_time REAL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
        )
    ''')
    
    # Shipments Table
    cursor.execute('''
        CREATE TABLE Shipments (
            shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            shipment_date DATE,
            receipt_date DATE,
            delay_flag BOOLEAN,
            delay_days INTEGER,
            FOREIGN KEY (po_id) REFERENCES PurchaseOrders(po_id)
        )
    ''')
    
    # Quality Records Table
    cursor.execute('''
        CREATE TABLE QualityRecords (
            quality_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            po_id INTEGER,
            defect_rate REAL,
            rejection_reason TEXT,
            batch_size INTEGER,
            audit_date DATE,
            time_since_last_audit_days INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
            FOREIGN KEY (po_id) REFERENCES PurchaseOrders(po_id)
        )
    ''')
    
    # Communication Logs Table
    cursor.execute('''
        CREATE TABLE CommunicationLogs (
            comm_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            po_id INTEGER,
            communication_type TEXT,
            query_time TIMESTAMP,
            response_time REAL,
            resolved BOOLEAN,
            FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id),
            FOREIGN KEY (po_id) REFERENCES PurchaseOrders(po_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database schema created successfully!")

def populate_sample_data():
    """Generate realistic sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sample supplier names and locations
    suppliers_data = [
        ('Acme Manufacturing', 'USA - Texas'),
        ('Global Parts Ltd', 'China - Shanghai'),
        ('European Supply Co', 'Germany - Berlin'),
        ('Pacific Logistics', 'Japan - Tokyo'),
        ('Premium Materials Inc', 'USA - California'),
        ('Budget Components', 'India - Mumbai'),
        ('Tech Suppliers Asia', 'Vietnam - Ho Chi Minh'),
        ('Quality Parts EU', 'Poland - Warsaw'),
        ('Rapid Delivery Inc', 'Mexico - Mexico City'),
        ('Elite Materials', 'South Korea - Seoul'),
        ('Standard Parts LLC', 'Canada - Toronto'),
        ('Swift Supply Chain', 'Brazil - São Paulo'),
    ]
    
    # Insert suppliers
    for name, location in suppliers_data:
        cursor.execute('INSERT INTO Suppliers (name, location) VALUES (?, ?)', 
                      (name, location))
    
    conn.commit()
    
    # Generate Purchase Orders with realistic data
    product_categories = ['Electronics', 'Mechanical', 'Raw Materials', 'Packaging', 'Chemicals']
    urgency_levels = ['Low', 'Medium', 'High', 'Critical']
    
    base_date = datetime.now() - timedelta(days=180)
    
    for i in range(100):  # 100 purchase orders
        supplier_id = random.randint(1, 12)
        order_date = base_date + timedelta(days=random.randint(0, 180))
        expected_lead_time = random.choice([7, 14, 21, 30, 45, 60])
        expected_delivery = (order_date + timedelta(days=expected_lead_time)).date()
        
        # Some orders are delayed
        is_delayed = random.random() < 0.35  # 35% delayed
        delay_or_early = random.randint(-5, 20) if is_delayed else random.randint(-3, 3)
        actual_delivery = (datetime.combine(expected_delivery, datetime.min.time()) + timedelta(days=delay_or_early)).date()
        
        quoted_cost = random.uniform(5000, 50000)
        actual_cost = quoted_cost * random.uniform(0.95, 1.15)  # ±15% variance
        order_qty = random.randint(50, 500)
        
        acknowledged = random.random() < 0.85  # 85% acknowledged
        ack_time = random.uniform(2, 48) if acknowledged else None
        
        status = 'Delivered' if actual_delivery <= datetime.now().date() else 'Pending'
        
        cursor.execute('''
            INSERT INTO PurchaseOrders 
            (supplier_id, order_date, expected_delivery_date, actual_delivery_date, 
             quoted_cost, actual_cost, order_quantity, product_category, urgency, 
             acknowledged, acknowledgment_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (supplier_id, order_date.date(), expected_delivery, 
              actual_delivery, quoted_cost, actual_cost, order_qty,
              random.choice(product_categories), random.choice(urgency_levels),
              acknowledged, ack_time, status))
    
    conn.commit()
    
    # Generate Shipments
    cursor.execute('SELECT po_id, order_date, expected_delivery_date, actual_delivery_date FROM PurchaseOrders')
    pos = cursor.fetchall()
    
    for po_id, order_date, expected_del, actual_del in pos:
        shipment_date = datetime.strptime(str(order_date), '%Y-%m-%d') + timedelta(days=random.randint(2, 5))
        receipt_date = actual_del
        delay_days = (datetime.strptime(str(actual_del), '%Y-%m-%d') - 
                     datetime.strptime(str(expected_del), '%Y-%m-%d')).days
        delay_flag = delay_days > 0
        
        cursor.execute('''
            INSERT INTO Shipments 
            (po_id, shipment_date, receipt_date, delay_flag, delay_days)
            VALUES (?, ?, ?, ?, ?)
        ''', (po_id, shipment_date.date(), receipt_date, delay_flag, max(0, delay_days)))
    
    conn.commit()
    
    # Generate Quality Records
    cursor.execute('SELECT DISTINCT supplier_id FROM PurchaseOrders')
    suppliers = cursor.fetchall()
    
    for (supplier_id,) in suppliers:
        for _ in range(random.randint(3, 8)):
            defect_rate = random.choice([0.5, 1.2, 2.3, 3.1, 4.5, 5.8, 7.2])
            batch_size = random.randint(100, 1000)
            audit_date = base_date + timedelta(days=random.randint(0, 180))
            time_since_audit = random.randint(7, 90)
            
            cursor.execute('''
                INSERT INTO QualityRecords 
                (supplier_id, defect_rate, rejection_reason, batch_size, audit_date, time_since_last_audit_days)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (supplier_id, defect_rate, random.choice(['Dimensional', 'Surface', 'Missing', 'Defective']),
                  batch_size, audit_date.date(), time_since_audit))
    
    conn.commit()
    
    # Generate Communication Logs
    cursor.execute('SELECT po_id FROM PurchaseOrders')
    all_pos = cursor.fetchall()
    
    cursor.execute('SELECT supplier_id FROM PurchaseOrders GROUP BY supplier_id')
    all_suppliers = cursor.fetchall()
    
    for (supplier_id,) in all_suppliers:
        for _ in range(random.randint(2, 6)):
            query_time = base_date + timedelta(days=random.randint(0, 180))
            response_time = random.choice([2, 4, 8, 12, 24, 48])  # hours
            
            cursor.execute('''
                INSERT INTO CommunicationLogs 
                (supplier_id, communication_type, query_time, response_time, resolved)
                VALUES (?, ?, ?, ?, ?)
            ''', (supplier_id, random.choice(['Email', 'Phone', 'Chat', 'Portal']),
                  query_time, response_time, random.random() < 0.9))
    
    conn.commit()
    conn.close()
    print("Sample data populated successfully!")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_database()
    populate_sample_data()
