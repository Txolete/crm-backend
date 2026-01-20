# ⚡ ACTUALIZACIÓN URGENTE - 3 ARCHIVOS

## 🎯 PROBLEMA ENCONTRADO

La ruta `/config/stages` **NO EXISTE** en tu instalación.
Por eso da error 404.

---

## ✅ SOLUCIÓN (2 MINUTOS)

### **PASO 1: Cierra el servidor**
```
Presiona Ctrl+C en la ventana del servidor
```

---

### **PASO 2: Copia estos 3 archivos**

**Archivo 1: config.py** (NUEVO)
```
Desde: config.py (descargado)
Hacia: crm-backend/app/api/routes/config.py
```
⚠️ Este archivo NO EXISTE en tu instalación - créalo

**Archivo 2: main.py**
```
Desde: main.py (descargado)
Hacia: crm-backend/app/main.py
```
✅ Reemplaza el existente

**Archivo 3: test_api.html**
```
Desde: test_api.html (descargado)
Hacia: crm-backend/app/templates/test_api.html
```
✅ Reemplaza el existente

---

### **PASO 3: Reinicia el servidor**
```
START_CRM.bat
```

---

### **PASO 4: Prueba de nuevo**
```
http://localhost:8000/test
```

**AHORA DEBERÍAS VER:**
```
Test 1: Verificar Stages
✅ OK - 7 stages

Test 2: Verificar Accounts  
✅ OK - 0 accounts

Test 3: Crear Oportunidad
✅ Oportunidad creada!
```

---

## 📝 QUÉ HACE CADA ARCHIVO

**config.py:**
- Crea las rutas `/config/stages`, `/config/regions`, etc.
- **SIN ESTE ARCHIVO EL SISTEMA NO FUNCIONA**

**main.py:**
- Importa el nuevo router de config
- Lo registra en la aplicación

**test_api.html:**
- Maneja correctamente el formato de respuesta de accounts
- Mejores mensajes de error

---

## 🎯 CHECKLIST

- [ ] Cerré el servidor (Ctrl+C)
- [ ] Copié `config.py` a `app/api/routes/config.py`
- [ ] Copié `main.py` a `app/main.py`
- [ ] Copié `test_api.html` a `app/templates/test_api.html`
- [ ] Ejecuté `START_CRM.bat`
- [ ] Abrí `http://localhost:8000/test`
- [ ] Test 1 dice "✅ OK - 7 stages"

---

## 🆘 SI SIGUES VIENDO 404

Si después de copiar los archivos SIGUES viendo error 404:

1. **Verifica que config.py está en el lugar correcto:**
   ```
   crm-backend/app/api/routes/config.py
   ```

2. **Abre el archivo y verifica que empieza con:**
   ```python
   """
   Configuration API routes - Simple GET endpoints for frontend
   """
   from fastapi import APIRouter, Depends
   ```

3. **Reinicia el servidor COMPLETAMENTE:**
   - Cierra la ventana del servidor
   - Abre una NUEVA ventana
   - Ejecuta `START_CRM.bat`

4. **Mira los logs del servidor:**
   - ¿Hay errores rojos?
   - Envíame captura de los errores

---

## 📦 ALTERNATIVA: Instalación completa

Si no quieres copiar archivos individualmente:

1. **Guarda tu base de datos:**
   ```
   copy crm.db crm.db.backup
   ```

2. **Extrae:** `crm-backend-v1.0-FINAL.tar.gz` (nueva versión)

3. **Restaura tu BD:**
   ```
   copy crm.db.backup crm.db
   ```

4. **Arranca:**
   ```
   START_CRM.bat
   ```

---

## ✅ RESULTADO ESPERADO

Después de la actualización:

**Test 1:** `✅ OK - 7 stages` ← Esto es lo IMPORTANTE
**Test 2:** `✅ OK - 0 accounts` (normal, no has creado cuentas)
**Test 3:** Creará una cuenta y oportunidad de ejemplo

---

**IMPORTANTE:** El archivo `config.py` es CRÍTICO. Sin él, el sistema NO funciona.
