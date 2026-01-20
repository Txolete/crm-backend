# CRM - VERSIÓN FINAL v1.0

## 🎯 INSTALACIÓN Y USO - PASOS EXACTOS

### **🔴 PASO 1: INSTALACIÓN COMPLETA (SOLO LA PRIMERA VEZ)**

Ejecuta **UNA SOLA VEZ:**
```bash
# Doble clic en:
INSTALL.bat
```

Este script hace TODO automáticamente:
1. Crea el entorno virtual de Python (venv)
2. Instala todas las dependencias necesarias
3. Crea la base de datos
4. Crea el usuario admin
5. Inicializa todos los datos maestros

**Espera a ver este mensaje:**
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

**Si NO ves este mensaje, algo falló. NO continúes al paso 2.**

---

### **🟢 PASO 2: ARRANCAR EL SERVIDOR**

```bash
# Doble clic en:
START_CRM.bat
```

**Espera a ver:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Deja esta ventana abierta** (es el servidor corriendo).

---

### **🔵 PASO 3: ABRIR NAVEGADOR**

Abre Chrome o Edge y ve a:
```
http://localhost:8000
```

**Login:**
- Email: `admin@example.com`
- Password: `admin123456`

---

## ✅ VERIFICACIÓN POST-SETUP

### **Test 1: Verificar stages**

1. Abre: `http://localhost:8000/docs`
2. Busca: `GET /config/stages`
3. Click: "Try it out" → "Execute"
4. **Debe devolver:** Lista de 7 stages

**Si NO devuelve stages:**
- ❌ El instalación falló
- ✅ Ejecuta `INSTALL.bat` de nuevo

---

### **Test 2: Verificar provincias**

1. En `http://localhost:8000/docs`
2. Busca: `GET /config/regions`
3. Click: "Try it out" → "Execute"
4. **Debe devolver:** Lista de 52 provincias

**Si NO devuelve provincias:**
- ❌ El instalación falló
- ✅ Ejecuta `INSTALL.bat` de nuevo

---

### **Test 3: Verificar login**

1. Abre: `http://localhost:8000/login`
2. Email: `admin@example.com`
3. Password: `admin123456`
4. Click: "Iniciar Sesión"
5. **Debe redirigir a:** Dashboard

**Si el login falla:**
- ❌ El instalación no creó el usuario
- ✅ Ejecuta `INSTALL.bat` de nuevo

---

## 🔧 FUNCIONALIDADES DISPONIBLES

### **Dashboard**
- KPIs: Pipeline total, ponderado, cerrado anual
- Gráficos de objetivos y pacing
- Overview de tareas

### **Kanban**
- Vista por stages
- Drag & drop
- ✅ **Botón "Nueva Oportunidad"** - Funcional
- Filtros por canal, provincia, tipo cliente

### **Importar Excel**
- ✅ **Botón "Importar Excel"** - Visible en navbar
- Formato: IMPORT_NORMALIZADO_CRM.xlsx
- Validación automática

### **Configuración**
- 52 Provincias españolas
- 9 Tipos de cliente
- 9 Canales comerciales
- 9 Roles de contacto
- 11 Plantillas de tareas

---

## ❌ PROBLEMAS COMUNES

### **"Error al cargar formulario de nueva oportunidad"**

**Causa:** No has ejecutado `SETUP.bat`

**Solución:**
1. Cierra el servidor (STOP_CRM.bat)
2. Ejecuta `INSTALL.bat`
3. Arranca el servidor (START_CRM.bat)
4. Prueba de nuevo

---

### **"No aparece botón Importar Excel"**

El botón **SÍ está** en la parte superior derecha del dashboard.

**Si no lo ves:**
1. Presiona `Ctrl + F5` (recarga la página)
2. Verifica que estás logueado
3. El botón está a la izquierda del nombre de usuario

---

### **"No puedo crear oportunidad - No hay cuentas"**

**Solución:**
1. Ve a `http://localhost:8000/docs`
2. Busca: `POST /accounts`
3. Click: "Try it out"
4. Pon en el body:
```json
{
  "name": "Cuenta de Prueba",
  "status": "active"
}
```
5. Click: "Execute"
6. Ahora intenta crear la oportunidad de nuevo

---

### **"No se creó el usuario admin"**

**Solución:**
1. Elimina `crm.db` (si existe)
2. Ejecuta `INSTALL.bat` de nuevo
3. Verifica que dice "✅ SETUP COMPLETADO"

---

## 📂 ARCHIVOS IMPORTANTES

```
crm-backend/
├── INSTALL.bat         ← Ejecutar SOLO LA PRIMERA VEZ (instala TODO)
├── START_CRM.bat       ← Arrancar servidor (uso diario)
├── STOP_CRM.bat        ← Detener servidor
├── setup.py            ← Script de inicialización (llamado por INSTALL.bat)
├── requirements.txt    ← Dependencias de Python
├── crm.db              ← Base de datos (se crea con INSTALL.bat)
├── .env                ← Configuración
├── INICIO_RAPIDO.md    ← Guía rápida
└── README.md           ← Documentación completa
```

---

## 🔄 USO DIARIO

Después del setup inicial, cada día solo necesitas:

```bash
1. START_CRM.bat
2. Abrir http://localhost:8000
3. Trabajar en el CRM
4. STOP_CRM.bat (cuando termines)
```

---

## 📋 CHECKLIST DE SETUP

- [ ] Ejecuté `SETUP.bat`
- [ ] Vi el mensaje "✅ SETUP COMPLETADO"
- [ ] Vi las credenciales del admin
- [ ] Ejecuté `START_CRM.bat`
- [ ] Vi "Application startup complete"
- [ ] Abrí `http://localhost:8000`
- [ ] Hice login con `admin@example.com` / `admin123456`
- [ ] Veo el dashboard correctamente
- [ ] El botón "Nueva Oportunidad" funciona
- [ ] El botón "Importar Excel" está visible

**Si TODO está marcado ✅ → El sistema está funcionando correctamente**

---

## 🆘 ÚLTIMA OPCIÓN

Si NADA funciona después de seguir todos los pasos:

1. Elimina TODO
2. Extrae el ZIP de nuevo
3. Ejecuta `INSTALL.bat`
4. Ejecuta `START_CRM.bat`
5. Login

**Si sigue sin funcionar, envía:**
- Captura de pantalla del error
- Contenido de la ventana de `SETUP.bat`
- Contenido de la ventana de `START_CRM.bat`

---

## 🎉 RESUMEN

**Primera vez:**
1. `SETUP.bat` (UNA VEZ)
2. `START_CRM.bat`
3. Login

**Uso diario:**
1. `START_CRM.bat`
2. Login
3. Trabajar
4. `STOP_CRM.bat`

**¡Listo!** 🚀
