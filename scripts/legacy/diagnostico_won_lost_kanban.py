"""
Diagnóstico - ¿Por qué no aparecen won/lost en Kanban?
"""
import sys
sys.path.insert(0, '/home/claude/crm-backend')

from app.database import get_db
from app.models.opportunity import Opportunity
from app.models.config import CfgStage

print("="*70)
print("DIAGNÓSTICO - Won/Lost en Kanban")
print("="*70)

db = next(get_db())

try:
    # 1. Verificar stages won/lost
    print("\n1. STAGES WON/LOST EN BASE DE DATOS:")
    stages = db.query(CfgStage).filter(
        CfgStage.outcome.in_(['won', 'lost'])
    ).all()
    
    if not stages:
        print("   ❌ NO hay stages con outcome='won' o 'lost'")
        print("   PROBLEMA: Necesitas stages ganado/perdido en cfg_stages")
    else:
        print(f"   ✅ {len(stages)} stages encontrados:")
        for stage in stages:
            print(f"      - {stage.name} (key={stage.key}, outcome={stage.outcome}, is_active={stage.is_active})")
    
    # 2. Verificar oportunidades cerradas
    print("\n2. OPORTUNIDADES CERRADAS:")
    won_opps = db.query(Opportunity).filter(
        Opportunity.close_outcome == 'won',
        Opportunity.status == 'active'
    ).all()
    
    lost_opps = db.query(Opportunity).filter(
        Opportunity.close_outcome == 'lost',
        Opportunity.status == 'active'
    ).all()
    
    print(f"   - Ganadas (won): {len(won_opps)}")
    print(f"   - Perdidas (lost): {len(lost_opps)}")
    
    if len(won_opps) == 0 and len(lost_opps) == 0:
        print("   ⚠️ No hay oportunidades cerradas todavía")
    
    # 3. Verificar stage_id de oportunidades cerradas
    print("\n3. STAGE_ID DE OPORTUNIDADES CERRADAS:")
    
    if won_opps:
        print("   Ganadas:")
        for opp in won_opps[:3]:
            stage = db.query(CfgStage).filter(CfgStage.id == opp.stage_id).first()
            stage_info = f"{stage.name} (outcome={stage.outcome})" if stage else "Stage no encontrado"
            print(f"      - {opp.id[:8]}... → stage_id={opp.stage_id[:8]}... → {stage_info}")
    
    if lost_opps:
        print("   Perdidas:")
        for opp in lost_opps[:3]:
            stage = db.query(CfgStage).filter(CfgStage.id == opp.stage_id).first()
            stage_info = f"{stage.name} (outcome={stage.outcome})" if stage else "Stage no encontrado"
            print(f"      - {opp.id[:8]}... → stage_id={opp.stage_id[:8]}... → {stage_info}")
    
    # 4. Verificar que stages won/lost están activos
    print("\n4. VERIFICAR is_active DE STAGES WON/LOST:")
    for stage in stages:
        if stage.is_active == 1:
            print(f"   ✅ {stage.name} está activo")
        else:
            print(f"   ❌ {stage.name} está INACTIVO (no aparecerá en Kanban)")
    
    # 5. Resumen
    print("\n" + "="*70)
    print("RESUMEN:")
    
    if not stages:
        print("❌ PROBLEMA 1: No hay stages won/lost en cfg_stages")
        print("   SOLUCIÓN: Crear stages con outcome='won' y 'lost'")
    elif any(s.is_active == 0 for s in stages):
        print("❌ PROBLEMA 2: Stages won/lost están inactivos")
        print("   SOLUCIÓN: Activar stages con UPDATE cfg_stages SET is_active=1")
    elif len(won_opps) == 0 and len(lost_opps) == 0:
        print("⚠️ INFO: No hay oportunidades cerradas todavía")
        print("   SIGUIENTE: Cerrar una oportunidad y verificar")
    else:
        # Verificar que las oportunidades tienen el stage_id correcto
        wrong_stage = False
        for opp in won_opps + lost_opps:
            stage = db.query(CfgStage).filter(CfgStage.id == opp.stage_id).first()
            if stage and stage.outcome != opp.close_outcome:
                print(f"❌ PROBLEMA 3: Oportunidad {opp.id[:8]}... tiene close_outcome={opp.close_outcome}")
                print(f"   pero stage_id apunta a stage con outcome={stage.outcome}")
                wrong_stage = True
        
        if not wrong_stage:
            print("✅ Todo parece correcto")
            print("   Oportunidades cerradas tienen stages correctos")
            print("   Deberían aparecer en Kanban con include_closed=true")
    
    print("="*70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
