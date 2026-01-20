"""
Script de inicialización para Railway
Crea usuario admin si no existe
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, init_db, engine
from app.models.user import User
from app.utils.auth import get_password_hash
from app.utils.audit import generate_id, get_iso_timestamp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_railway_db():
    """
    Inicializa la base de datos en Railway
    - Crea todas las tablas
    - Crea usuario admin si no existe
    - Crea configuración inicial
    """
    logger.info("🚀 Inicializando base de datos en Railway...")
    
    # Crear todas las tablas
    logger.info("📋 Creando tablas...")
    init_db()
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Verificar si ya existe un usuario admin
        admin_exists = db.query(User).filter(User.role == "admin").first()
        
        if not admin_exists:
            logger.info("👤 Creando usuario admin...")
            
            # Obtener credenciales de variables de entorno o usar defaults
            admin_email = os.getenv("ADMIN_EMAIL", "admin@empresa.com")
            admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
            admin_name = os.getenv("ADMIN_NAME", "Administrador")
            
            # Crear usuario admin
            timestamp = get_iso_timestamp()
            admin_user = User(
                id=generate_id(),
                name=admin_name,
                email=admin_email,
                password_hash=get_password_hash(admin_password),
                role="admin",
                is_active=True,
                created_at=timestamp,
                updated_at=timestamp
            )
            
            db.add(admin_user)
            db.commit()
            
            logger.info(f"✅ Usuario admin creado:")
            logger.info(f"   Email: {admin_email}")
            logger.info(f"   Password: {admin_password}")
            logger.info(f"   ⚠️  CAMBIA LA CONTRASEÑA DESPUÉS DEL PRIMER LOGIN")
        else:
            logger.info("✅ Usuario admin ya existe")
        
        # Crear configuración inicial si no existe
        from app.models.config import CfgStage, CfgStageProbability
        
        stages_exist = db.query(CfgStage).count() > 0
        
        if not stages_exist:
            logger.info("⚙️  Creando configuración inicial...")
            
            # Crear stages por defecto
            timestamp = get_iso_timestamp()
            stages = [
                {"key": "new", "name": "New", "sort_order": 10, "outcome": "open", "probability": 0.05},
                {"key": "contacted", "name": "Contacted", "sort_order": 20, "outcome": "open", "probability": 0.10},
                {"key": "qualified", "name": "Qualified", "sort_order": 30, "outcome": "open", "probability": 0.30},
                {"key": "proposal", "name": "Proposal", "sort_order": 40, "outcome": "open", "probability": 0.50},
                {"key": "negotiation", "name": "Negotiation", "sort_order": 50, "outcome": "open", "probability": 0.70},
                {"key": "won", "name": "Won", "sort_order": 90, "outcome": "won", "probability": 1.00, "terminal": True},
                {"key": "lost", "name": "Lost", "sort_order": 95, "outcome": "lost", "probability": 0.00, "terminal": True}
            ]
            
            for stage_data in stages:
                stage = CfgStage(
                    id=generate_id(),
                    key=stage_data["key"],
                    name=stage_data["name"],
                    sort_order=stage_data["sort_order"],
                    outcome=stage_data["outcome"],
                    is_terminal=stage_data.get("terminal", False),
                    is_active=True,
                    created_at=timestamp,
                    updated_at=timestamp
                )
                db.add(stage)
                db.flush()
                
                # Crear probabilidad
                prob = CfgStageProbability(
                    stage_id=stage.id,
                    probability=stage_data["probability"],
                    created_at=timestamp,
                    updated_at=timestamp
                )
                db.add(prob)
            
            db.commit()
            logger.info("✅ Configuración inicial creada")
        else:
            logger.info("✅ Configuración ya existe")
        
        logger.info("🎉 Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    initialize_railway_db()
