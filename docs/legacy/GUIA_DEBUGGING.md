# 🔧 GUÍA MAESTRA DE DEBUGGING - PASO A PASO

## 🎯 OBJETIVO
Identificar EXACTAMENTE dónde está el problema sin adivinar.

---

## 📋 PROCESO COMPLETO (30 minutos)

### **FASE 1: Backend (10 minutos)**

#### **PASO 1: Verificar Base de Datos**
```bash
# En la carpeta crm-backend:
call venv\Scripts\activate.bat
python debug_01_database.py
```

**¿Qué buscar?**
- ✅ Total opportunities: debe ser > 0
- ✅ Distribución por stage: debe mostrar oportunidades en cada stage
- ❌ Si dice "stage_id INVÁLIDO" → PROBLEMA IDENTIFICADO

**Envíame:** El output completo de este script

---

#### **PASO 2: Verificar APIs**
```bash
# Asegúrate que el servidor está corriendo en OTRA ventana
python debug_02_apis.py
```

**¿Qué buscar?**
- ✅ GET /config/stages: debe devolver 7 stages
- ✅ GET /opportunities: debe devolver X opportunities
- ✅ GET /kanban: debe devolver opportunities > 0
- ❌ Si GET /kanban tiene 0 opps pero GET /opportunities tiene datos → PROBLEMA EN KANBAN

**Envíame:** El output completo de este script

---

#### **PASO 3: Debug Profundo Kanban**
```bash
python debug_03_kanban_deep.py
```

**¿Qué buscar?**
- Compara "SQL directa" vs "Endpoint /kanban"
- Si SQL tiene datos pero endpoint no → BUG en kanban.py
- Si ambos tienen 0 → Problema en BD

**Envíame:** El output completo de este script

---

### **FASE 2: Frontend (10 minutos)**

#### **PASO 4: Verificar en Navegador**

**A. Abrir herramientas de desarrollo:**
1. Abre: http://localhost:8000
2. Login: admin@example.com / admin123456
3. Presiona **F12**
4. Ve a pestaña **Console**

**B. Ejecutar comandos de verificación:**

Copia estos 3 comandos en Console (uno por uno) y envíame los resultados:

```javascript
// 1. ¿Existe showNewOpportunityModal?
typeof window.showNewOpportunityModal

// 2. ¿Qué devuelve /kanban?
fetch('/kanban?include_closed=true', {credentials:'include'})
  .then(r => r.json())
  .then(d => {
    console.log('Total columns:', d.columns.length)
    console.log('Opps por columna:', d.columns.map(c => c.stage_key + ':' + c.opportunities.length))
    console.log('Total opps:', d.columns.reduce((sum, c) => sum + c.opportunities.length, 0))
  })

// 3. ¿Existe loadKanbanData?
typeof loadKanbanData
```

**Envíame:** Los resultados de estos 3 comandos

---

#### **PASO 5: Verificar botón "Nueva Oportunidad"**

1. **Ve a pestaña "Kanban"** en el CRM
2. **Console limpia** (click en 🚫 en DevTools)
3. **Click en "Nueva Oportunidad"**
4. **Mira Console**

**Envíame:** 
- ¿Aparecen mensajes en Console?
- Si sí, copia TODOS los mensajes
- Si no, el onclick no funciona

---

### **FASE 3: Análisis (5 minutos)**

Con la información de las FASES 1 y 2, podemos identificar EXACTAMENTE dónde está el problema:

| Síntoma | Causa | Solución |
|---------|-------|----------|
| BD tiene opps, API /opportunities las ve, pero API /kanban NO | Bug en kanban.py filtrado | Arreglar lógica de filtrado |
| BD tiene opps, API /kanban las ve, pero UI vacío | Bug en dashboard.js o carga | Verificar loadKanbanData() |
| typeof showNewOpportunityModal = undefined | dashboard.js no cargado | Verificar que se copió correctamente |
| Console muestra "Status 404" al crear opp | Falta config.py | Copiar config.py |
| BD NO tiene opps | Importación falló | Reimportar Excel |

---

## ⚡ OPCIÓN RÁPIDA (5 minutos)

Si no quieres ejecutar todos los scripts, ejecuta estos 3 comandos en Console del navegador:

```javascript
// COMANDO 1: Verificar funciones existen
console.log('showNewOpportunityModal:', typeof window.showNewOpportunityModal)
console.log('loadKanbanData:', typeof loadKanbanData)

// COMANDO 2: Probar /kanban directamente
fetch('/kanban?include_closed=true', {credentials:'include'})
  .then(r => r.json())
  .then(d => console.log('Kanban tiene', d.columns.reduce((sum, c) => sum + c.opportunities.length, 0), 'opps'))

// COMANDO 3: Ver errores
console.log('Errores anteriores:', performance.getEntriesByType('resource').filter(r => r.name.includes('dashboard.js')))
```

**Envíame:** Los resultados de estos 3 comandos

---

## 🎯 ¿QUÉ NECESITO DE TI?

**OPCIÓN A (Completa):** Ejecuta PASOS 1, 2, 3 y envíame los outputs

**OPCIÓN B (Rápida):** Ejecuta los 3 comandos de "OPCIÓN RÁPIDA" en Console y envíamelos

Con cualquiera de las dos opciones, podré decirte EXACTAMENTE cuál es el problema.

---

## 📦 ARCHIVOS CREADOS

1. `debug_01_database.py` - Verifica BD
2. `debug_02_apis.py` - Verifica APIs
3. `debug_03_kanban_deep.py` - Compara SQL vs API
4. `DEBUG_COMPLETO.bat` - Ejecuta los 3 scripts
5. `DEBUG_04_FRONTEND.md` - Guía frontend
6. Esta guía maestra

---

**Con este proceso sistemático, encontraremos el problema REAL en menos de 30 minutos.**

¿Empezamos por el PASO 1? 🔍
