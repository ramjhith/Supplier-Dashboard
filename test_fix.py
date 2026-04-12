#!/usr/bin/env python3
import sys
print("Testing fixes...")
sys.stdout.flush()

try:
    from database import init_database, populate_sample_data
    print("✅ Database module imported")
    sys.stdout.flush()
    
    init_database()
    print("✅ Database initialized")
    sys.stdout.flush()
    
    populate_sample_data()
    print("✅ Sample data populated")
    sys.stdout.flush()
    
    from ml_models import SupplierMLModels
    print("✅ ML Models module imported")
    sys.stdout.flush()
    
    ml_models = SupplierMLModels()
    print("✅ ML Models instance created")
    sys.stdout.flush()
    
    ml_models.train_all_models()
    print("✅ ML models trained successfully!")
    sys.stdout.flush()
    print("\n✅ ALL TESTS PASSED - App is ready to run!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
