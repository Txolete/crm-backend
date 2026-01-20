"""
Script de verificación - Comprueba que todo esté inicializado correctamente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models import CfgStage, CfgRegion, CfgCustomerType, CfgLeadSource, CfgContactRole, CfgTaskTemplate

print("\n" + "="*70)
print("VERIFICACIÓN DEL SISTEMA")
print("="*70 + "\n")

db = SessionLocal()

try:
    # Check user
    users = db.query(User).count()
    print(f"👤 Usuarios:           {users}")
    
    if users > 0:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if admin:
            print(f"   ✅ Admin existe: {admin.email}")
        else:
            print(f"   ❌ Admin NO encontrado")
    
    # Check stages
    stages = db.query(CfgStage).count()
    print(f"\n📊 Stages:             {stages}")
    if stages > 0:
        print("   ✅ Stages inicializados")
    else:
        print("   ❌ NO hay stages")
    
    # Check regions
    regions = db.query(CfgRegion).count()
    print(f"\n🗺️  Provincias:         {regions}")
    if regions > 0:
        print("   ✅ Provincias inicializadas")
    else:
        print("   ❌ NO hay provincias")
    
    # Check customer types
    types = db.query(CfgCustomerType).count()
    print(f"\n🏢 Tipos de cliente:   {types}")
    if types > 0:
        print("   ✅ Tipos inicializados")
    else:
        print("   ❌ NO hay tipos")
    
    # Check lead sources
    sources = db.query(CfgLeadSource).count()
    print(f"\n📢 Canales:            {sources}")
    if sources > 0:
        print("   ✅ Canales inicializados")
    else:
        print("   ❌ NO hay canales")
    
    # Check contact roles
    roles = db.query(CfgContactRole).count()
    print(f"\n👥 Roles de contacto:  {roles}")
    if roles > 0:
        print("   ✅ Roles inicializados")
    else:
        print("   ❌ NO hay roles")
    
    # Check task templates
    tasks = db.query(CfgTaskTemplate).count()
    print(f"\n✅ Plantillas tareas:  {tasks}")
    if tasks > 0:
        print("   ✅ Plantillas inicializadas")
    else:
        print("   ❌ NO hay plantillas")
    
    print("\n" + "="*70)
    
    # Summary
    total = users + stages + regions + types + sources + roles + tasks
    if total > 0:
        print("✅ SISTEMA INICIALIZADO CORRECTAMENTE")
        print("\nPuedes arrancar el servidor con: START_CRM.bat")
    else:
        print("❌ SISTEMA NO INICIALIZADO")
        print("\nEjecuta: INSTALL.bat")
    
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
finally:
    db.close()
