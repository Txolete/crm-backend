"""
Master data initialization module
HOTFIX 9.4

This module provides functions to initialize all master data automatically on startup.
"""
from sqlalchemy.orm import Session
from app.models import (
    CfgStage, CfgStageProbability, CfgRegion,
    CfgCustomerType, CfgLeadSource, CfgContactRole, CfgTaskTemplate
)
from app.utils.audit import generate_id, get_iso_timestamp


# Master data from Excel LISTAS sheet
STAGES_DATA = [
    {"key": "new", "name": "Nuevo", "sort_order": 1, "outcome": "open", "is_terminal": 0, "probability": 0.05},
    {"key": "contacted", "name": "Contactado", "sort_order": 2, "outcome": "open", "is_terminal": 0, "probability": 0.10},
    {"key": "qualified", "name": "Cualificado", "sort_order": 3, "outcome": "open", "is_terminal": 0, "probability": 0.30},
    {"key": "proposal", "name": "Propuesta", "sort_order": 4, "outcome": "open", "is_terminal": 0, "probability": 0.50},
    {"key": "negotiation", "name": "Negociación", "sort_order": 5, "outcome": "open", "is_terminal": 0, "probability": 0.70},
    {"key": "won", "name": "Ganado", "sort_order": 6, "outcome": "won", "is_terminal": 1, "probability": 1.00},
    {"key": "lost", "name": "Perdido", "sort_order": 7, "outcome": "lost", "is_terminal": 1, "probability": 0.00}
]

REGIONS_ES = [
    "Álava", "Albacete", "Alicante", "Almería", "Asturias", "Ávila", "Badajoz", "Barcelona",
    "Burgos", "Cáceres", "Cádiz", "Cantabria", "Castellón", "Ciudad Real", "Córdoba",
    "A Coruña", "Cuenca", "Girona", "Granada", "Guadalajara", "Gipuzkoa", "Huelva",
    "Huesca", "Illes Balears", "Jaén", "León", "Lleida", "La Rioja", "Lugo", "Madrid",
    "Málaga", "Murcia", "Navarra", "Ourense", "Palencia", "Las Palmas", "Pontevedra",
    "Salamanca", "Santa Cruz de Tenerife", "Segovia", "Sevilla", "Soria", "Tarragona",
    "Teruel", "Toledo", "Valencia", "Valladolid", "Bizkaia", "Zamora", "Zaragoza",
    "Ceuta", "Melilla"
]

CUSTOMER_TYPES = [
    "Back office completo", "Back office operativo", "Productor", "Consultoría IT",
    "Consultoría negocio", "EPC / Ingeniería", "O&M / Operación y Mantenimiento",
    "Comercializadora / Energy Retail", "Otro"
]

LEAD_SOURCES = [
    {"name": "Comercial (outbound)", "category": "outbound"},
    {"name": "Contacto web (inbound)", "category": "inbound"},
    {"name": "Referencia / recomendación", "category": "referral"},
    {"name": "Partner / aliado", "category": "partner"},
    {"name": "Evento / feria", "category": "event"},
    {"name": "Inbound (otro)", "category": "inbound"},
    {"name": "Interno", "category": "internal"},
    {"name": "Comercial (outbound) - JAG", "category": "outbound"},
    {"name": "Comercial (outbound) - RP", "category": "outbound"}
]

CONTACT_ROLES = [
    "Decisor", "Sponsor", "Técnico", "Compras", "Finanzas",
    "Legal", "Operaciones", "Usuario", "Administrador"
]

TASK_TEMPLATES = [
    {"name": "Llamada de contacto", "default_due_days": 1},
    {"name": "Enviar email", "default_due_days": 1},
    {"name": "Concertar reunión", "default_due_days": 3},
    {"name": "Reunión (comercial)", "default_due_days": 7},
    {"name": "Reunión (técnica)", "default_due_days": 7},
    {"name": "Preparar propuesta", "default_due_days": 7},
    {"name": "Enviar propuesta", "default_due_days": 1},
    {"name": "Seguimiento de propuesta", "default_due_days": 3},
    {"name": "Negociación / ajustes", "default_due_days": 5},
    {"name": "Solicitar decisión / cierre", "default_due_days": 3},
    {"name": "Onboarding / kickoff", "default_due_days": 7}
]


def initialize_all_master_data(db: Session, logger):
    """Initialize all master data - called from startup"""
    timestamp = get_iso_timestamp()
    counts = {}
    
    # 1. Stages
    count = 0
    for stage_data in STAGES_DATA:
        existing = db.query(CfgStage).filter(CfgStage.key == stage_data["key"]).first()
        if not existing:
            stage_id = generate_id()
            stage = CfgStage(
                id=stage_id, key=stage_data["key"], name=stage_data["name"],
                sort_order=stage_data["sort_order"], outcome=stage_data["outcome"],
                is_terminal=stage_data["is_terminal"], is_active=1,
                created_at=timestamp, updated_at=timestamp
            )
            db.add(stage)
            prob = CfgStageProbability(
                stage_id=stage_id, probability=stage_data["probability"],
                created_at=timestamp, updated_at=timestamp
            )
            db.add(prob)
            count += 1
    counts['stages'] = count
    
    # 2. Regions
    count = 0
    for idx, region_name in enumerate(REGIONS_ES, 1):
        existing = db.query(CfgRegion).filter(CfgRegion.name == region_name).first()
        if not existing:
            db.add(CfgRegion(
                id=generate_id(), name=region_name, country_code="ES",
                is_active=1, sort_order=idx,
                created_at=timestamp, updated_at=timestamp
            ))
            count += 1
    counts['regions'] = count
    
    # 3. Customer Types
    count = 0
    for idx, type_name in enumerate(CUSTOMER_TYPES, 1):
        existing = db.query(CfgCustomerType).filter(CfgCustomerType.name == type_name).first()
        if not existing:
            db.add(CfgCustomerType(
                id=generate_id(), name=type_name, is_active=1, sort_order=idx,
                created_at=timestamp, updated_at=timestamp
            ))
            count += 1
    counts['customer_types'] = count
    
    # 4. Lead Sources
    count = 0
    for idx, source_data in enumerate(LEAD_SOURCES, 1):
        existing = db.query(CfgLeadSource).filter(CfgLeadSource.name == source_data["name"]).first()
        if not existing:
            db.add(CfgLeadSource(
                id=generate_id(), name=source_data["name"],
                category=source_data.get("category"), is_active=1, sort_order=idx,
                created_at=timestamp, updated_at=timestamp
            ))
            count += 1
    counts['lead_sources'] = count
    
    # 5. Contact Roles
    count = 0
    for idx, role_name in enumerate(CONTACT_ROLES, 1):
        existing = db.query(CfgContactRole).filter(CfgContactRole.name == role_name).first()
        if not existing:
            db.add(CfgContactRole(
                id=generate_id(), name=role_name, is_active=1, sort_order=idx,
                created_at=timestamp, updated_at=timestamp
            ))
            count += 1
    counts['contact_roles'] = count
    
    # 6. Task Templates
    count = 0
    for idx, template_data in enumerate(TASK_TEMPLATES, 1):
        existing = db.query(CfgTaskTemplate).filter(CfgTaskTemplate.name == template_data["name"]).first()
        if not existing:
            db.add(CfgTaskTemplate(
                id=generate_id(), name=template_data["name"],
                default_due_days=template_data.get("default_due_days"),
                is_active=1, sort_order=idx,
                created_at=timestamp, updated_at=timestamp
            ))
            count += 1
    counts['task_templates'] = count
    
    db.commit()
    
    logger.info(f"   → Created: {counts['stages']} stages, {counts['regions']} regions, "
                f"{counts['customer_types']} customer types, {counts['lead_sources']} lead sources, "
                f"{counts['contact_roles']} contact roles, {counts['task_templates']} task templates")
    
    return counts
