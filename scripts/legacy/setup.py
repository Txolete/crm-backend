"""
SETUP INICIAL DEL CRM - VERSION SIMPLE
Ejecutar SOLO LA PRIMERA VEZ
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print(" SETUP INICIAL DEL CRM ".center(80, "="))
print("="*80 + "\n")

# Importar después de añadir al path
from app.database import SessionLocal, init_db
from app.models.user import User
from app.models import (
    CfgStage, CfgStageProbability, CfgRegion, CfgCustomerType,
    CfgLeadSource, CfgContactRole, CfgTaskTemplate
)
from app.utils.security import hash_password
from app.utils.audit import generate_id, get_iso_timestamp

print("📦 Creando estructura de base de datos...")
init_db()
print("   ✅ Tablas creadas\n")

db = SessionLocal()

try:
    timestamp = get_iso_timestamp()
    
    # ===== 1. USUARIO ADMIN =====
    print("👤 Creando usuario admin...")
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User(
            id=generate_id(),
            name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("admin123456"),
            role="admin",
            is_active=1,
            created_at=timestamp,
            updated_at=timestamp
        )
        db.add(admin)
        db.commit()
        print("   ✅ Admin creado")
    else:
        print("   ℹ️  Admin ya existe")
    
    # ===== 2. STAGES =====
    print("\n📊 Creando stages...")
    stages = [
        ("new", "Nuevo", 1, "open", 0, 0.05),
        ("contacted", "Contactado", 2, "open", 0, 0.10),
        ("qualified", "Cualificado", 3, "open", 0, 0.30),
        ("proposal", "Propuesta", 4, "open", 0, 0.50),
        ("negotiation", "Negociación", 5, "open", 0, 0.70),
        ("won", "Ganado", 6, "won", 1, 1.00),
        ("lost", "Perdido", 7, "lost", 1, 0.00)
    ]
    
    for key, name, order, outcome, terminal, prob in stages:
        if not db.query(CfgStage).filter(CfgStage.key == key).first():
            sid = generate_id()
            db.add(CfgStage(
                id=sid, key=key, name=name, sort_order=order,
                outcome=outcome, is_terminal=terminal, is_active=1,
                created_at=timestamp, updated_at=timestamp
            ))
            db.add(CfgStageProbability(
                stage_id=sid, probability=prob,
                created_at=timestamp, updated_at=timestamp
            ))
    db.commit()
    print("   ✅ 7 stages creados")
    
    # ===== 3. PROVINCIAS =====
    print("\n🗺️  Creando provincias...")
    provincias = [
        "Álava", "Albacete", "Alicante", "Almería", "Asturias", "Ávila", "Badajoz",
        "Barcelona", "Burgos", "Cáceres", "Cádiz", "Cantabria", "Castellón",
        "Ciudad Real", "Córdoba", "A Coruña", "Cuenca", "Girona", "Granada",
        "Guadalajara", "Gipuzkoa", "Huelva", "Huesca", "Illes Balears", "Jaén",
        "León", "Lleida", "La Rioja", "Lugo", "Madrid", "Málaga", "Murcia",
        "Navarra", "Ourense", "Palencia", "Las Palmas", "Pontevedra", "Salamanca",
        "Santa Cruz de Tenerife", "Segovia", "Sevilla", "Soria", "Tarragona",
        "Teruel", "Toledo", "Valencia", "Valladolid", "Bizkaia", "Zamora",
        "Zaragoza", "Ceuta", "Melilla"
    ]
    
    for i, p in enumerate(provincias, 1):
        if not db.query(CfgRegion).filter(CfgRegion.name == p).first():
            db.add(CfgRegion(
                id=generate_id(), name=p, country_code="ES",
                is_active=1, sort_order=i,
                created_at=timestamp, updated_at=timestamp
            ))
    db.commit()
    print(f"   ✅ {len(provincias)} provincias creadas")
    
    # ===== 4. TIPOS DE CLIENTE =====
    print("\n🏢 Creando tipos de cliente...")
    tipos = [
        "Back office completo", "Back office operativo", "Productor",
        "Consultoría IT", "Consultoría negocio", "EPC / Ingeniería",
        "O&M / Operación y Mantenimiento", "Comercializadora / Energy Retail", "Otro"
    ]
    
    for i, t in enumerate(tipos, 1):
        if not db.query(CfgCustomerType).filter(CfgCustomerType.name == t).first():
            db.add(CfgCustomerType(
                id=generate_id(), name=t, is_active=1, sort_order=i,
                created_at=timestamp, updated_at=timestamp
            ))
    db.commit()
    print(f"   ✅ {len(tipos)} tipos creados")
    
    # ===== 5. CANALES =====
    print("\n📢 Creando canales comerciales...")
    canales = [
        ("Comercial (outbound)", "outbound"),
        ("Contacto web (inbound)", "inbound"),
        ("Referencia / recomendación", "referral"),
        ("Partner / aliado", "partner"),
        ("Evento / feria", "event"),
        ("Inbound (otro)", "inbound"),
        ("Interno", "internal"),
        ("Comercial (outbound) - JAG", "outbound"),
        ("Comercial (outbound) - RP", "outbound")
    ]
    
    for i, (name, cat) in enumerate(canales, 1):
        if not db.query(CfgLeadSource).filter(CfgLeadSource.name == name).first():
            db.add(CfgLeadSource(
                id=generate_id(), name=name, category=cat,
                is_active=1, sort_order=i,
                created_at=timestamp, updated_at=timestamp
            ))
    db.commit()
    print(f"   ✅ {len(canales)} canales creados")
    
    # ===== 6. ROLES =====
    print("\n👥 Creando roles de contacto...")
    roles = ["Decisor", "Sponsor", "Técnico", "Compras", "Finanzas",
             "Legal", "Operaciones", "Usuario", "Administrador"]
    
    for i, r in enumerate(roles, 1):
        if not db.query(CfgContactRole).filter(CfgContactRole.name == r).first():
            db.add(CfgContactRole(
                id=generate_id(), name=r, is_active=1, sort_order=i,
                created_at=timestamp, updated_at=timestamp
            ))
    db.commit()
    print(f"   ✅ {len(roles)} roles creados")
    
    # ===== 7. TAREAS =====
    print("\n✅ Creando plantillas de tareas...")
    tareas = [
        ("Llamada de contacto", 1), ("Enviar email", 1),
        ("Concertar reunión", 3), ("Reunión (comercial)", 7),
        ("Reunión (técnica)", 7), ("Preparar propuesta", 7),
        ("Enviar propuesta", 1), ("Seguimiento de propuesta", 3),
        ("Negociación / ajustes", 5), ("Solicitar decisión / cierre", 3),
        ("Onboarding / kickoff", 7)
    ]
    
    for i, (name, days) in enumerate(tareas, 1):
        if not db.query(CfgTaskTemplate).filter(CfgTaskTemplate.name == name).first():
            db.add(CfgTaskTemplate(
                id=generate_id(), name=name, default_due_days=days,
                is_active=1, sort_order=i,
                created_at=timestamp, updated_at=timestamp
            ))
    db.commit()
    print(f"   ✅ {len(tareas)} plantillas creadas")
    
    # ===== RESUMEN =====
    print("\n" + "="*80)
    print(" ✅ SETUP COMPLETADO ".center(80, "="))
    print("="*80)
    print("\n📊 Datos inicializados:")
    print("   • 1 Usuario admin")
    print("   • 7 Stages con probabilidades")
    print("   • 52 Provincias españolas")
    print("   • 9 Tipos de cliente")
    print("   • 9 Canales comerciales")
    print("   • 9 Roles de contacto")
    print("   • 11 Plantillas de tareas")
    print("\n🔐 Credenciales:")
    print("   Email:    admin@example.com")
    print("   Password: admin123456")
    print("\n🚀 Siguiente paso:")
    print("   Ejecuta: START_CRM.bat")
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
