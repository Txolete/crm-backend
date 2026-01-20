# 🚀 INICIO RÁPIDO - CRM

## ⚡ PRIMERA VEZ (Solo hacer UNA vez)

### **Paso 1: Instalación completa**
```bash
# Doble clic en:
INSTALL.bat
```

Esto hará:
1. ✅ Crear entorno virtual de Python (si no existe)
2. ✅ Instalar todas las dependencias
3. ✅ Crear base de datos (crm.db)
4. ✅ Crear usuario admin (admin@example.com / admin123456)
5. ✅ Inicializar 7 Stages con probabilidades
6. ✅ Inicializar 52 Provincias españolas  
7. ✅ Inicializar 9 Tipos de cliente
8. ✅ Inicializar 9 Canales comerciales
9. ✅ Inicializar 9 Roles de contacto
10. ✅ Inicializar 11 Plantillas de tareas

**Resultado esperado:**
```
✅ SETUP COMPLETADO
   • 1 Usuario admin
   • 7 Stages con probabilidades
   • 52 Provincias españolas
   • 9 Tipos de cliente
   • 9 Canales comerciales
   • 9 Roles de contacto
   • 11 Plantillas de tareas

🔐 Credenciales:
   Email:    admin@example.com
   Password: admin123456

Siguiente paso: Ejecuta START_CRM.bat
```

---

### **Paso 2: Arrancar el servidor**
```bash
# Doble clic en:
START_CRM.bat
```

---

### **Paso 3: Abrir navegador**
```
http://localhost:8000
```

Login:
- Email: `admin@example.com`
- Password: `admin123456`

---

## 📝 USO DIARIO (Después del setup inicial)

```bash
# Arrancar
START_CRM.bat

# Detener (si necesitas)
STOP_CRM.bat
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### ❌ "No se encontró el entorno virtual"
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ "Error al cargar formulario de nueva oportunidad"
**Causa:** No ejecutaste `INSTALL.bat`  
**Solución:** Ejecuta `INSTALL.bat` primero

### ❌ "No aparecen provincias/tipos de cliente"
**Causa:** No ejecutaste `INSTALL.bat`  
**Solución:** Ejecuta `INSTALL.bat` primero

### ❌ "No puedo hacer login"
**Causa:** No ejecutaste `INSTALL.bat`  
**Solución:** Ejecuta `INSTALL.bat` primero

---

## 📦 ORDEN DE EJECUCIÓN

```
1️⃣ INSTALL.bat         (SOLO LA PRIMERA VEZ - Instala TODO)
2️⃣ START_CRM.bat       (CADA VEZ QUE QUIERAS USAR EL CRM)
3️⃣ Abrir navegador     (http://localhost:8000)
```

---

## ✅ VERIFICACIÓN

Después del setup, verifica que todo está OK:

1. **Abre:** `http://localhost:8000/docs`
2. **Busca:** `GET /config/stages`
3. **Click:** "Try it out" → "Execute"
4. **Resultado esperado:** Lista de 7 stages

Si ves los stages, ¡todo está bien! ✅

---

## 🔐 CREDENCIALES POR DEFECTO

```
Email:    admin@example.com
Password: admin123456
```

⚠️ Cambia la contraseña después del primer login

---

## 📞 AYUDA

Si algo no funciona:
1. ¿Ejecutaste `SETUP.bat` primero?
2. ¿El setup terminó sin errores?
3. ¿Ves el archivo `crm.db` en la carpeta?

Si todo lo anterior es SÍ y sigue fallando, envía el error completo.
