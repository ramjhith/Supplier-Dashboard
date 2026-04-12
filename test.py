"""
Test script to verify all components of the SRM Dashboard work correctly
Run this before launching the full app to ensure everything is functional
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("=" * 60)
    print("🧪 Testing Imports")
    print("=" * 60)
    
    required_packages = {
        'dash': 'Dash',
        'plotly': 'Plotly',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'sklearn': 'Scikit-learn',
        'sqlite3': 'SQLite3'
    }
    
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"✅ {name:<20} - OK")
        except ImportError as e:
            print(f"❌ {name:<20} - FAILED: {e}")
            return False
    
    print()
    return True

def test_database():
    """Test database initialization and data generation"""
    print("=" * 60)
    print("🧪 Testing Database")
    print("=" * 60)
    
    try:
        from database import init_database, populate_sample_data, get_db_connection
        
        print("✅ Initializing database...")
        init_database()
        
        print("✅ Populating sample data...")
        populate_sample_data()
        
        print("✅ Testing connection...")
        conn = get_db_connection()
        
        # Check tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = {'Suppliers', 'PurchaseOrders', 'Shipments', 'QualityRecords', 'CommunicationLogs'}
        missing_tables = expected_tables - set(tables)
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ All tables created: {', '.join(sorted(tables))}")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM Suppliers")
        supplier_count = cursor.fetchone()[0]
        print(f"✅ Suppliers: {supplier_count}")
        
        cursor.execute("SELECT COUNT(*) FROM PurchaseOrders")
        po_count = cursor.fetchone()[0]
        print(f"✅ Purchase Orders: {po_count}")
        
        cursor.execute("SELECT COUNT(*) FROM QualityRecords")
        quality_count = cursor.fetchone()[0]
        print(f"✅ Quality Records: {quality_count}")
        
        conn.close()
        print()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_kpi_calculator():
    """Test KPI calculation engine"""
    print("=" * 60)
    print("🧪 Testing KPI Calculator")
    print("=" * 60)
    
    try:
        from kpi_calculator import KPICalculator
        
        calc = KPICalculator()
        
        # Get all suppliers KPIs
        kpis_df = calc.get_all_suppliers_kpis()
        
        print(f"✅ Calculated KPIs for {len(kpis_df)} suppliers")
        print(f"✅ KPI columns: {', '.join(kpis_df.columns[:8])}")
        
        # Test individual KPI calculation
        if len(kpis_df) > 0:
            supplier_id = kpis_df['Supplier ID'].values[0]
            
            otd = calc.on_time_delivery_rate(supplier_id)
            print(f"✅ Sample OTD Rate: {otd:.2f}%")
            
            defect = calc.defect_rate(supplier_id)
            print(f"✅ Sample Defect Rate: {defect:.2f}%")
            
            risk = calc.supplier_risk_score(supplier_id)
            print(f"✅ Sample Risk Score: {risk:.2f}/100")
        
        calc.close()
        print()
        return True
        
    except Exception as e:
        print(f"❌ KPI Calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ml_models():
    """Test ML model training and predictions"""
    print("=" * 60)
    print("🧪 Testing ML Models")
    print("=" * 60)
    
    try:
        from ml_models import SupplierMLModels
        
        models = SupplierMLModels()
        
        print("✅ Training Delay Prediction model...")
        models.train_delay_prediction_model()
        
        print("✅ Training Defect Risk model...")
        models.train_defect_prediction_model()
        
        print("✅ Training Lead Time Category model...")
        models.train_lead_time_prediction_model()
        
        # Test predictions
        if models.delay_model:
            delay_prob = models.predict_delay_probability(1, 100, 20, 4)
            print(f"✅ Sample Delay Prediction: {delay_prob}%")
        
        if models.defect_model:
            defect_prob = models.predict_defect_risk_probability(1, 200, 'Electronics', 30)
            print(f"✅ Sample Defect Risk Prediction: {defect_prob}%")
        
        if models.lead_time_model:
            lt_cat = models.predict_lead_time_category(1, 'High', 4, 'USA - Texas')
            print(f"✅ Sample Lead Time Prediction: {lt_cat}")
        
        models.close()
        print()
        return True
        
    except Exception as e:
        print(f"❌ ML Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🧪 SRM DASHBOARD TEST SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("KPI Calculator", test_kpi_calculator),
        ("ML Models", test_ml_models),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print()
    
    if all(results.values()):
        print("🎉 ALL TESTS PASSED! Dashboard is ready to run.")
        print()
        print("📌 Next steps:")
        print("   1. chmod +x run.sh")
        print("   2. ./run.sh")
        print("   3. Open http://127.0.0.1:8050/ in your browser")
        return 0
    else:
        print("❌ SOME TESTS FAILED! Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
