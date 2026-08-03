"""
Importa materiales desde un pickle exportado previamente.
Si ya existe un material activo con el mismo name_slug, lo retira antes (regla del sistema).
Uso: railway run --service crm-backend python scripts/import_materials.py /tmp/materials.pkl
"""
import sys, os
import pickle
import uuid
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app.models.material import MaterialDocument

in_path = sys.argv[1] if len(sys.argv) > 1 else "materials_export.pkl"
with open(in_path, "rb") as f:
    rows = pickle.load(f)

db = SessionLocal()
now = datetime.now(timezone.utc)
imported = 0
try:
    for r in rows:
        slug = r["name_slug"]
        prev_active = db.query(MaterialDocument).filter(
            MaterialDocument.name_slug == slug,
            MaterialDocument.status == "active",
        ).all()
        for p in prev_active:
            p.status = "retired"
            p.retired_at = now
        m = MaterialDocument(
            id=str(uuid.uuid4()),
            name=r["name"],
            name_slug=slug,
            version=r["version"],
            usage_note=r.get("usage_note"),
            file_name=r["file_name"],
            mime_type=r["mime_type"],
            file_size=r["file_size"],
            file_data=r["file_data"],
            status="active",
            uploaded_at=now,
        )
        db.add(m)
        imported += 1
    db.commit()
    print(f"Imported {imported} materials")
finally:
    db.close()
