"""
Exporta material_documents activos a un fichero pickle.
Uso: railway run --service crm-backend python scripts/export_materials.py /tmp/materials.pkl
"""
import sys, os
import pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app.models.material import MaterialDocument

out_path = sys.argv[1] if len(sys.argv) > 1 else "materials_export.pkl"
db = SessionLocal()
try:
    items = db.query(MaterialDocument).filter(MaterialDocument.status == "active").all()
    rows = []
    for m in items:
        rows.append({
            "name": m.name,
            "name_slug": m.name_slug,
            "version": m.version,
            "usage_note": m.usage_note,
            "file_name": m.file_name,
            "mime_type": m.mime_type,
            "file_size": m.file_size,
            "file_data": bytes(m.file_data) if m.file_data else b"",
        })
    with open(out_path, "wb") as f:
        pickle.dump(rows, f)
    print(f"Exported {len(rows)} materials to {out_path}")
finally:
    db.close()
