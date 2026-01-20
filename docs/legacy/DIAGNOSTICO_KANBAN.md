# 🔍 DIAGNÓSTICO - Oportunidades no aparecen en Kanban

## ⚡ DIAGNÓSTICO EN 2 MINUTOS

### **PASO 1: Actualiza estos 2 archivos**

1. **`diagnostico_opp.html`** → `app/templates/diagnostico_opp.html` (NUEVO)
2. **`main.py`** → `app/main.py` (reemplazar)

### **PASO 2: Reinicia el servidor**
```bash
# Ctrl+C para cerrar
START_CRM.bat
```

### **PASO 3: Abre página de diagnóstico**
```
http://localhost:8000/diagnostico
```

### **PASO 4: Haz click en los 3 botones:**
1. **"Cargar todas las oportunidades"**
2. **"Cargar Kanban"**
3. **"Verificar /config/stages"**

### **PASO 5: Envíame la info**

Copia lo que veas en cada sección y envíamelo.

---

## 🎯 LO QUE VA A REVELAR

### **Test 1: Cargar todas las oportunidades**

**Si dice "✅ Encontradas 18 oportunidades":**
- Las oportunidades SÍ se importaron
- El problema está en el Kanban o en los stages

**Si dice "⚠️ No hay oportunidades":**
- El Excel NO se importó correctamente
- O las oportunidades tienen status != 'active'

---

### **Test 2: Cargar Kanban**

**Si dice "✅ Kanban tiene 18 oportunidades":**
- El Kanban SÍ funciona
- El problema es el frontend (dashboard.js)

**Si dice "⚠️ Kanban no tiene oportunidades":**
- Las oportunidades tienen status != 'active', O
- Los stage_id no son válidos, O
- Hay un problema con la query del Kanban

---

### **Test 3: Verificar stages**

**Si dice "✅ OK - 7 stages":**
- La ruta /config/stages funciona
- El problema de "crear oportunidad" está en otro lado

**Si dice "❌ Error 404":**
- NO copiaste el archivo `config.py`
- Copia `config.py` a `app/api/routes/config.py`
- Reinicia el servidor

---

## 🔧 SOLUCIONES SEGÚN RESULTADO

### **Escenario A: Test 1 dice "No hay oportunidades"**

**Problema:** El Excel no se importó o las oportunidades tienen status incorrecto.

**Solución:**
1. Importa el Excel de nuevo
2. Si sigue fallando, envíame el error exacto

---

### **Escenario B: Test 1 OK, Test 2 dice "Kanban vacío"**

**Problema:** Las oportunidades tienen stage_id inválido o status != 'active'

**Solución:** 
Te enviaré un script SQL para corregir los stage_ids

---

### **Escenario C: Test 1 y 2 OK, pero Kanban en UI vacío**

**Problema:** El JavaScript del dashboard no carga correctamente

**Solución:**
1. Presiona Ctrl+F5 en el navegador (limpia caché)
2. Abre F12 → Console
3. Ve a pestaña Kanban
4. Envíame los errores que aparezcan

---

### **Escenario D: Test 3 dice "404"**

**Problema:** No actualizaste `config.py`

**Solución:**
1. Copia `config.py` a `app/api/routes/config.py`
2. Reinicia servidor
3. Prueba test 3 de nuevo

---

## 📝 MENSAJE ERROR "CREAR OPORTUNIDAD"

**Dime exactamente qué mensaje ves cuando intentas crear oportunidad:**

¿Es uno de estos?

A) "❌ Error: Status 404"
B) "❌ Error al cargar stages"
C) "❌ No se pudieron cargar los stages"
D) "❌ stages.filter is not a function"
E) Otro (¿cuál?)

**Y también:**

Abre F12 → Console, intenta crear oportunidad, y envíame TODO lo que aparezca en Console.

---

## 🎯 RESUMEN

**Para ayudarte necesito que:**

1. Abras: `http://localhost:8000/diagnostico`
2. Hagas click en los 3 botones
3. Me envíes CAPTURAS o el texto de lo que muestra
4. Me digas el mensaje EXACTO cuando intentas crear oportunidad
5. Me envíes la Console del navegador (F12)

**Con esto sabré EXACTAMENTE qué está pasando.**

---

## 📦 ARCHIVOS NECESARIOS

1. **`diagnostico_opp.html`** (página de diagnóstico - NUEVA)
2. **`main.py`** (con ruta /diagnostico)
3. **`config.py`** (si aún no lo copiaste)

---

**Esto nos dirá en 30 segundos dónde está el problema exacto.** 🔍
