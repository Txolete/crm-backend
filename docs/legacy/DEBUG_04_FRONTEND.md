# 🔍 PASO 4: Verificar Frontend (Navegador)

## IMPORTANTE
Ejecuta esto DESPUÉS de los pasos 1, 2 y 3.

---

## A. Verificar que dashboard.js se carga

1. **Abre el navegador:**
   ```
   http://localhost:8000
   ```

2. **Login con:**
   ```
   admin@example.com
   admin123456
   ```

3. **Presiona F12** (abre DevTools)

4. **Ve a pestaña "Network"**

5. **Recarga la página** (Ctrl+R)

6. **Busca "dashboard.js" en la lista**

7. **Click en "dashboard.js"**

8. **Ve a pestaña "Response"**

9. **Busca esta línea** (Ctrl+F):
   ```javascript
   window.showNewOpportunityModal
   ```

10. **¿La encuentras?**
    - ✅ SÍ → dashboard.js está cargado correctamente
    - ❌ NO → dashboard.js está corrupto o es versión antigua

---

## B. Verificar que loadKanbanData() funciona

1. **Estás en la pestaña Dashboard**

2. **En DevTools, ve a pestaña "Console"**

3. **Escribe y presiona Enter:**
   ```javascript
   loadKanbanData()
   ```

4. **¿Qué aparece?**
   
   **Si aparece:**
   ```
   Fetching kanban data...
   Kanban data loaded: X opportunities
   ```
   ✅ La función funciona

   **Si aparece:**
   ```
   ReferenceError: loadKanbanData is not defined
   ```
   ❌ La función no existe - dashboard.js no está cargado

   **Si aparece:**
   ```
   Error: ...
   ```
   ❌ Hay un error - copia el error completo

---

## C. Verificar llamada real a /kanban

1. **En DevTools, ve a pestaña "Network"**

2. **Click en el botón "Clear" (🚫) para limpiar**

3. **Ve a la pestaña "Kanban" en el CRM**

4. **En Network, busca la petición a "kanban"**

5. **Click en esa petición**

6. **Ve a pestaña "Response"**

7. **Copia la respuesta COMPLETA** y envíamela

---

## D. Verificar Console en pestaña Kanban

1. **Estás en la pestaña "Kanban" del CRM**

2. **En DevTools, ve a pestaña "Console"**

3. **¿Hay errores rojos?**

4. **Copia TODOS los mensajes** (errores y warnings)

---

## E. Verificar botón "Nueva Oportunidad"

1. **En la pestaña "Kanban"**

2. **DevTools → Console limpia** (click en 🚫)

3. **Click en "Nueva Oportunidad"**

4. **¿Qué aparece en Console?**

   **Si aparece:**
   ```
   showNewOpportunityModal called
   Fetching stages...
   Stages response status: 200
   ...
   ```
   ✅ La función funciona, sigue los mensajes

   **Si aparece:**
   ```
   Uncaught ReferenceError: showNewOpportunityModal is not defined
   ```
   ❌ La función no existe

   **Si no aparece NADA:**
   ❌ El onclick no está conectado

5. **Copia TODOS los mensajes de Console**

---

## F. Inspeccionar el HTML del botón

1. **En DevTools, ve a pestaña "Elements"**

2. **Presiona Ctrl+F**

3. **Busca:** `Nueva Oportunidad`

4. **Encuentra el botón**

5. **Mira el HTML del botón:**
   ```html
   <button ... onclick="showNewOpportunityModal()">
   ```

6. **¿Tiene el atributo onclick?**
   - ✅ SÍ → El HTML es correcto
   - ❌ NO → El HTML está mal, no tiene onclick

---

## RESUMEN - Envíame esta info:

```
A. dashboard.js cargado: SÍ / NO
B. loadKanbanData() funciona: SÍ / NO / Error: [error]
C. Respuesta de /kanban: [pega JSON completo]
D. Errores en Console (Kanban): [pega errores]
E. Al hacer click "Nueva Oportunidad": [pega mensajes]
F. Botón tiene onclick: SÍ / NO
```

---

## ⚠️ ATAJOS RÁPIDOS

**Verificación ultra-rápida en Console:**

```javascript
// 1. ¿Existe la función?
typeof window.showNewOpportunityModal
// Debería decir: "function"

// 2. ¿Qué devuelve /kanban?
fetch('/kanban?include_closed=true', {credentials:'include'})
  .then(r => r.json())
  .then(d => console.log('Kanban:', d.columns.map(c => c.stage_key + ':' + c.opportunities.length)))
// Debería mostrar: ["new:5", "contacted:3", ...]

// 3. ¿loadKanbanData existe?
typeof loadKanbanData
// Debería decir: "function"
```

Ejecuta estos 3 comandos en Console y envíame los resultados.
