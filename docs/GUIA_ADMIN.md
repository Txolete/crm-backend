# 🔧 GUÍA DE ADMINISTRACIÓN CRM - INSTALACIÓN Y OPERACIÓN

**CRM Seguimiento Clientes**  
**Versión:** 0.7.0  
**Audiencia:** Administradores de sistema, responsables IT

---

## ÍNDICE

1. [Instalación Paso a Paso](#1-instalación-paso-a-paso)
2. [Configuración Inicial](#2-configuración-inicial)
3. [Primera Ejecución](#3-primera-ejecución)
4. [Operación Diaria](#4-operación-diaria)
5. [Backups y Recuperación](#5-backups-y-recuperación)
6. [Gestión de Usuarios](#6-gestión-de-usuarios)
7. [Configuración Avanzada](#7-configuración-avanzada)
8. [Acceso Red Local](#8-acceso-red-local)
9. [Troubleshooting](#9-troubleshooting)
10. [Actualizaciones](#10-actualizaciones)
11. [Integración Futura](#11-integración-futura)

---

## 1. INSTALACIÓN PASO A PASO

### 1.1 Requisitos del Sistema

**Hardware mínimo:**
- Procesador: Intel i3 o superior (2+ cores)
- RAM: 4 GB (8 GB recomendado)
- Disco: 10 GB libres (para DB + backups)
- Red: Conexión a internet (para instalación)

**Software requerido:**
- Windows 10/11 (64-bit)
- Python 3.8 o superior
- Navegador: Chrome, Edge o Firefox (actualizado)

**Puertos:**
- 8000: CRM application (configurable)

---

### 1.2 Instalar Python

**Si ya tienes Python instalado:**
1. Abre CMD (Win+R → `cmd`)
2. Ejecuta: `python --version`
3. Si muestra Python 3.8+ → continúa al paso 1.3
4. Si no → sigue instalación

**Instalar Python 3.11 (recomendado):**

1. **Descargar:**
   - Ir a: https://www.python.org/downloads/
   - Click "Download Python 3.11.X"

2. **Instalar:**
   - Ejecutar instalador descargado
   - ⚠️ **IMPORTANTE:** Marcar checkbox "Add Python to PATH"
   - Click "Install Now"
   - Esperar instalación (2-3 minutos)
   - Click "Close"

3. **Verificar:**
   ```cmd
   python --version
   ```
   Debe mostrar: `Python 3.11.X`

**Troubleshooting:**
- Si `python` no se reconoce → no marcaste "Add to PATH"
- Solución: Desinstalar y reinstalar marcando checkbox

---

### 1.3 Descargar el CRM

**Opción A: Desde archivo ZIP**

1. Recibir `crm-backend-paso9-FINAL.tar.gz` o `.zip`
2. Extraer a ubicación definitiva, por ejemplo:
   ```
   C:\CRM\
   ```
3. Verificar estructura:
   ```
   C:\CRM\
   ├── app\
   ├── data\
   ├── docs\
   ├── START_CRM.bat
   ├── STOP_CRM.bat
   ├── BACKUP_DB.bat
   ├── RESTORE_DB.bat
   └── .env.example
   ```

**Opción B: Desde Git (futuro)**
```cmd
cd C:\
git clone https://github.com/empresa/crm-backend CRM
cd CRM
```

---

### 1.4 Estructura de Carpetas

```
C:\CRM\
├── app\                    # Código fuente (NO MODIFICAR)
│   ├── api\
│   ├── models\
│   ├── schemas\
│   ├── utils\
│   ├── automations\
│   ├── middleware\
│   ├── templates\
│   └── static\
├── data\                   # Datos persistentes
│   ├── backups\           # Backups automáticos (se crea auto)
│   ├── uploads\           # Archivos subidos (se crea auto)
│   └── reports\           # Reportes (futuro)
├── logs\                   # Logs de aplicación (se crea auto)
│   ├── app.log            # Log general
│   └── error.log          # Solo errores
├── docs\                   # Documentación
│   ├── MANUAL_USUARIO_PARTE1.md
│   ├── MANUAL_USUARIO_PARTE2.md
│   └── GUIA_ADMIN.md (este archivo)
├── venv\                   # Virtual environment (se crea auto)
├── crm.db                  # Base de datos SQLite (se crea auto)
├── .env                    # Configuración (CREAR DESDE .env.example)
├── .env.example            # Plantilla configuración
├── requirements.txt        # Dependencias Python
├── START_CRM.bat          # ⭐ SCRIPT ARRANQUE
├── STOP_CRM.bat           # Script parada
├── BACKUP_DB.bat          # Script backup
└── RESTORE_DB.bat         # Script restore
```

---

## 2. CONFIGURACIÓN INICIAL

### 2.1 Crear Archivo .env

**Paso 1: Copiar plantilla**

En Windows Explorer:
1. Ir a `C:\CRM\`
2. Copiar `.env.example`
3. Pegar en misma carpeta
4. Renombrar copia a `.env`

**Desde CMD:**
```cmd
cd C:\CRM
copy .env.example .env
```

---

### 2.2 Configurar SECRET_KEY (OBLIGATORIO)

**Paso 1: Generar clave segura**

```cmd
cd C:\CRM
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Output ejemplo:
```
xK7mP9vR2nL4qWzJ8bY6cT5fG3hN1dS0aE
```

**Paso 2: Editar .env**

1. Abrir `C:\CRM\.env` con Notepad
2. Buscar línea:
   ```
   SECRET_KEY=your-secret-key-change-this-in-production
   ```
3. Reemplazar con tu clave generada:
   ```
   SECRET_KEY=xK7mP9vR2nL4qWzJ8bY6cT5fG3hN1dS0aE
   ```
4. Guardar y cerrar

⚠️ **IMPORTANTE:**
- NUNCA compartas esta clave
- Usa una clave diferente en cada instalación
- NO la subas a Git/repositorios públicos

---

### 2.3 Configurar Email (Opcional)

**Si quieres notificaciones por email:**

#### Gmail Setup

**Paso 1: Habilitar 2FA en Gmail**
1. Ir a: https://myaccount.google.com/security
2. Click "Verificación en dos pasos"
3. Activar si no está activado

**Paso 2: Generar App Password**
1. Ir a: https://myaccount.google.com/apppasswords
2. Seleccionar "Correo"
3. Seleccionar "Otro (nombre personalizado)"
4. Escribir: "CRM Seguimiento"
5. Click "Generar"
6. Copiar contraseña de 16 caracteres (ejemplo: `xxxx xxxx xxxx xxxx`)

**Paso 3: Configurar en .env**

Editar `C:\CRM\.env`:

```bash
# EMAIL NOTIFICATIONS
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_TLS=true
SMTP_FROM_NAME=CRM Notifications
SMTP_FROM_EMAIL=tu-email@gmail.com
EMAIL_DASHBOARD_URL=http://localhost:8000/dashboard
```

**Si NO quieres emails:**
```bash
EMAIL_ENABLED=false
```

#### Outlook/Office 365 Setup

```bash
EMAIL_ENABLED=true
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=tu-email@empresa.com
SMTP_PASSWORD=tu-password
SMTP_TLS=true
SMTP_FROM_NAME=CRM Notifications
SMTP_FROM_EMAIL=tu-email@empresa.com
```

---

### 2.4 Otras Configuraciones (Opcional)

**Automatizaciones:**
```bash
AUTOMATIONS_ENABLED=true          # true/false
AUTO_RUN_TIME=07:00               # HH:MM (24h)
AUTO_NO_ACTIVITY_DAYS=14          # días sin actividad
AUTO_PROPOSAL_NO_ACTIVITY_DAYS=7  # días propuestas
```

**Base de datos:**
```bash
DATABASE_URL=sqlite:///./crm.db   # No cambiar (por ahora)
```

**CORS (acceso red local):**
```bash
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
# Si acceso red: añadir ,http://192.168.1.50:8000
```

---

## 3. PRIMERA EJECUCIÓN

### 3.1 Arrancar CRM

**Método 1: Doble click (recomendado)**

1. En Windows Explorer, ir a `C:\CRM\`
2. Doble click en `START_CRM.bat`
3. Se abre ventana negra (CMD)
4. Esperar 3-5 minutos (primera vez)

**Qué hace START_CRM.bat:**
```
[1/5] Verificar Python
[2/5] Crear virtual environment (primera vez)
[3/5] Activar venv
[4/5] Instalar dependencias (primera vez: 3-5 min)
[5/5] Arrancar servidor
```

**Primera ejecución (lenta):**
```
[1/5] Python detected
Python 3.11.0

[2/5] Creating virtual environment...
Virtual environment created successfully!

[3/5] Activating virtual environment...

[4/5] Installing dependencies...
This may take a few minutes on first run...
Installing: fastapi, sqlalchemy, uvicorn...
[████████████████████] 100%
Dependencies installed successfully!

[5/5] Starting CRM application...

======================================================================
CRM IS STARTING
======================================================================

Access the CRM at: http://localhost:8000

The browser will open automatically in 5 seconds...

Press Ctrl+C to stop the server
======================================================================

INFO: Started server process
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Siguientes ejecuciones (rápidas: 5-10 seg):**
```
[1/5] Python detected
[2/5] Virtual environment found
[3/5] Activating virtual environment...
[4/5] Dependencies already installed
[5/5] Starting CRM application...
...
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### 3.2 Verificar que Funciona

**Paso 1: Navegador se abre automáticamente**
- URL: http://localhost:8000
- Pantalla de login debe aparecer

**Paso 2: Login inicial**
- Email: `admin@example.com`
- Password: `admin123`
- Click "Iniciar Sesión"

**Paso 3: Dashboard aparece**
- Si ves el dashboard con KPIs → ✅ Instalación exitosa

**Paso 4: Cambiar password admin**
1. Click en usuario (esquina superior derecha)
2. "Cambiar contraseña" (próximamente)
3. O usar endpoint: `POST /admin/users/{user_id}/password`

---

### 3.3 Verificar Health

**En navegador:**
```
http://localhost:8000/health
```

**Debe mostrar:**
```json
{
  "status": "healthy",
  "version": "0.7.0",
  "checks": {
    "database": {"status": "ok"},
    "scheduler": {"status": "running"},
    "email": {"enabled": true, "configured": true},
    "automations": {"enabled": true}
  }
}
```

---

### 3.4 Primera Inicialización Base de Datos

**Se crea automáticamente:**
- Al arrancar por primera vez, se crea `crm.db`
- Se crean todas las tablas
- Se crea usuario admin por defecto

**Verificar:**
```cmd
dir C:\CRM\crm.db
```

Debe existir archivo `crm.db` (tamaño ~200-500 KB)

---

## 4. OPERACIÓN DIARIA

### 4.1 Arrancar CRM

**Cada mañana:**
1. Doble click `START_CRM.bat`
2. Esperar 5-10 segundos
3. Ventana CMD queda abierta (NO CERRAR)
4. Trabajar normalmente en navegador

**Mantener ventana CMD abierta:**
- Minimizar (NO cerrar)
- Si cierras ventana → CRM se detiene
- Usuarios pierden acceso

---

### 4.2 Parar CRM

**Opción A: STOP_CRM.bat**
1. Doble click `STOP_CRM.bat`
2. Confirma que proceso se detuvo

**Opción B: Ctrl+C en ventana START_CRM**
1. Click en ventana CMD donde corre CRM
2. Presionar `Ctrl+C`
3. Confirmar con `S` (Sí)

**Opción C: Cerrar ventana**
- Simplemente cierra la ventana CMD
- Menos limpio pero funciona

---

### 4.3 Reiniciar CRM

**Cuándo reiniciar:**
- Después de cambiar .env
- Después de actualizar versión
- Si hay comportamiento extraño

**Cómo:**
1. `STOP_CRM.bat` (o Ctrl+C)
2. Esperar 5 segundos
3. `START_CRM.bat`

---

### 4.4 Monitoreo Básico

**Logs en tiempo real:**

Abrir segunda ventana CMD:
```cmd
cd C:\CRM\logs
type app.log
```

Para ver nuevas líneas:
```cmd
powershell Get-Content app.log -Wait -Tail 50
```

**Errores:**
```cmd
type logs\error.log
```

**Health check:**
```
http://localhost:8000/health
```
Revisar cada mañana

---

## 5. BACKUPS Y RECUPERACIÓN

### 5.1 Backup Manual

**Ejecutar backup:**
```cmd
cd C:\CRM
BACKUP_DB.bat
```

**Resultado:**
```
==================================================================
CRM DATABASE BACKUP
==================================================================

Backing up database...
Source: crm.db
Target: data\backups\crm_20260108_190000.db

SUCCESS: Database backed up successfully!
Backup size: 5 MB

Cleaning old backups (keeping last 30)...
Found 28 backup(s)
No cleanup needed.

==================================================================
BACKUP COMPLETED SUCCESSFULLY
==================================================================
```

**Ubicación backups:**
```
C:\CRM\data\backups\
├── crm_20260108_190000.db
├── crm_20260107_190000.db
├── crm_20260106_190000.db
└── ...
```

---

### 5.2 Backup Automático (Recomendado)

**Configurar con Programador de Tareas de Windows:**

**Paso 1: Abrir Task Scheduler**
1. Win+R → `taskschd.msc` → Enter
2. O buscar "Programador de tareas" en inicio

**Paso 2: Crear tarea**
1. Panel derecho → "Crear tarea básica..."
2. Nombre: `CRM Backup Diario`
3. Descripción: `Backup automático base de datos CRM`
4. Siguiente

**Paso 3: Desencadenador**
1. Seleccionar: "Diariamente"
2. Siguiente
3. Hora de inicio: `19:00:00` (7 PM)
4. Repetir cada: `1` días
5. Siguiente

**Paso 4: Acción**
1. Seleccionar: "Iniciar un programa"
2. Siguiente
3. Programa/script: `C:\CRM\BACKUP_DB.bat`
4. Agregar argumentos: `auto`
5. Iniciar en: `C:\CRM`
6. Siguiente

**Paso 5: Configuración avanzada**
1. Finalizar
2. Doble click en tarea creada
3. Tab "General":
   - ✅ Ejecutar tanto si el usuario inició sesión como si no
   - ✅ Ejecutar con los privilegios más elevados
4. Tab "Configuración":
   - ✅ Permitir ejecutar tarea a petición
   - ✅ Si la tarea en ejecución no finaliza cuando se solicite, forzar su detención
5. OK

**Paso 6: Verificar**
1. Click derecho en tarea
2. "Ejecutar"
3. Revisar que backup se creó en `C:\CRM\data\backups\`

**Troubleshooting:**
- Si no ejecuta: revisar permisos
- Si falla: revisar logs en Task Scheduler → Historial

---

### 5.3 Restaurar desde Backup

**Cuándo restaurar:**
- Datos corruptos
- Importación errónea masiva
- Cambio accidental que quieres revertir

**Proceso:**

**Paso 1: Parar CRM**
```cmd
STOP_CRM.bat
```

**Paso 2: Ejecutar RESTORE**
```cmd
RESTORE_DB.bat
```

**Paso 3: Seleccionar backup**
```
==================================================================
CRM DATABASE RESTORE
==================================================================

Available backups:

[1] crm_20260108_190000.db
[2] crm_20260107_190000.db
[3] crm_20260106_190000.db
...

==================================================================

Enter backup number to restore (or Q to quit): 2

Selected backup: crm_20260107_190000.db

==================================================================
WARNING: This will replace your current database!
==================================================================

Current database: crm.db
Backup to restore: data\backups\crm_20260107_190000.db

Are you SURE you want to continue? (YES/no): YES
```

**Paso 4: Confirmación**
- Escribir exactamente: `YES` (mayúsculas)
- NO aceptará: "yes", "si", "y"

**Paso 5: Proceso**
```
==================================================================
STARTING RESTORE PROCESS
==================================================================

Step 1: Creating safety backup of current database...
  SUCCESS: Safety backup created
  Location: data\backups\crm_before_restore_20260108_195030.db

Step 2: Restoring database from backup...
  SUCCESS: Database restored successfully!

==================================================================
RESTORE COMPLETED SUCCESSFULLY
==================================================================

IMPORTANT: Restart the CRM application for changes to take effect.
```

**Paso 6: Arrancar CRM**
```cmd
START_CRM.bat
```

**Paso 7: Verificar**
- Login al CRM
- Verifica que datos son los esperados
- Si está mal → puedes restaurar otro backup o el safety backup

---

### 5.4 Buenas Prácticas Backups

**Frecuencia:**
- Automático diario: 19:00
- Manual antes de:
  - Importaciones grandes
  - Actualizaciones
  - Cambios masivos configuración

**Retención:**
- Automático: 30 días (configurable en BACKUP_DB.bat)
- Importante: copiar fuera de servidor periódicamente

**Backup offline:**
```cmd
# Copiar a USB/red cada semana
xcopy C:\CRM\data\backups D:\Backups_CRM\ /E /Y
```

**Testing restore:**
- Probar restore 1 vez al mes
- Asegura que backups son válidos

---

## 6. GESTIÓN DE USUARIOS

### 6.1 Crear Usuario (API)

**Usando CURL:**
```bash
# Login como admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  -c cookies.txt

# Crear usuario
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name":"Juan Pérez",
    "email":"juan@empresa.com",
    "password":"password123",
    "role":"sales"
  }'
```

**Roles disponibles:**
- `admin`: acceso total
- `sales`: CRM completo, sin gestión usuarios/config
- `viewer`: solo lectura

---

### 6.2 Listar Usuarios

```bash
curl http://localhost:8000/admin/users -b cookies.txt
```

Response:
```json
{
  "users": [
    {
      "id": "user_abc123",
      "name": "Admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    },
    {
      "id": "user_def456",
      "name": "Juan Pérez",
      "email": "juan@empresa.com",
      "role": "sales",
      "is_active": true
    }
  ]
}
```

---

### 6.3 Desactivar Usuario

```bash
curl -X PUT http://localhost:8000/admin/users/user_def456/deactivate \
  -b cookies.txt
```

**Efecto:**
- Usuario no puede hacer login
- Sesiones activas se invalidan
- Datos históricos se mantienen

---

### 6.4 Reactivar Usuario

```bash
curl -X PUT http://localhost:8000/admin/users/user_def456/activate \
  -b cookies.txt
```

---

### 6.5 Reset Password

```bash
curl -X POST http://localhost:8000/admin/users/user_def456/reset-password \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"new_password":"newpass123"}'
```

**Comunicar al usuario:**
```
Asunto: Reset contraseña CRM

Hola Juan,

Tu contraseña del CRM ha sido reseteada.

Nueva contraseña temporal: newpass123

Por favor cámbiala al iniciar sesión.

URL: http://192.168.1.50:8000
```

---

## 7. CONFIGURACIÓN AVANZADA

### 7.1 Variables .env Completas

```bash
# ==================================================================
# DATABASE
# ==================================================================
DATABASE_URL=sqlite:///./crm.db

# ==================================================================
# SECURITY
# ==================================================================
SECRET_KEY=tu-clave-generada-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ==================================================================
# CORS
# ==================================================================
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# ==================================================================
# AUTOMATIONS
# ==================================================================
AUTOMATIONS_ENABLED=true
AUTO_RUN_TIME=07:00
AUTO_NO_ACTIVITY_DAYS=14
AUTO_PROPOSAL_NO_ACTIVITY_DAYS=7
AUTO_OVERDUE_DEDUP_DAYS=7
AUTO_FOLLOWUP_DEDUP_DAYS=14

# ==================================================================
# EMAIL
# ==================================================================
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_TLS=true
SMTP_FROM_NAME=CRM Notifications
SMTP_FROM_EMAIL=tu-email@gmail.com
EMAIL_DASHBOARD_URL=http://localhost:8000/dashboard
```

---

### 7.2 Cambiar Puerto

**Por defecto:** 8000

**Cambiar a 9000:**

Editar `START_CRM.bat`, última línea:
```batch
REM Cambiar de:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info

REM A:
uvicorn app.main:app --host 0.0.0.0 --port 9000 --log-level info
```

Actualizar .env:
```bash
ALLOWED_ORIGINS=http://localhost:9000
EMAIL_DASHBOARD_URL=http://localhost:9000/dashboard
```

---

### 7.3 Ajustar Automatizaciones

**Cambiar hora ejecución:**
```bash
AUTO_RUN_TIME=06:30  # 6:30 AM en vez de 7:00
```

**Cambiar thresholds:**
```bash
AUTO_NO_ACTIVITY_DAYS=7    # Más agresivo (antes 14)
AUTO_PROPOSAL_NO_ACTIVITY_DAYS=3  # Muy agresivo (antes 7)
```

**Desactivar completamente:**
```bash
AUTOMATIONS_ENABLED=false
```

**Reiniciar CRM después de cambios .env**

---

### 7.4 Logs: Cambiar Retención

Editar `app/utils/logging_config.py`:

```python
# Cambiar de 10MB y 30 backups
app_handler = logging.handlers.RotatingFileHandler(
    'logs/app.log',
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=30,
    ...
)

# A: 5MB y 60 backups
app_handler = logging.handlers.RotatingFileHandler(
    'logs/app.log',
    maxBytes=5 * 1024 * 1024,   # 5MB
    backupCount=60,
    ...
)
```

---

## 8. ACCESO RED LOCAL

### 8.1 Obtener IP Local

**Método 1: CMD**
```cmd
ipconfig
```

Buscar sección "Adaptador de Ethernet" o "Adaptador de LAN inalámbrica":
```
Dirección IPv4. . . . . . . . . : 192.168.1.50
```

**Método 2: Panel de Control**
1. Panel de Control → Redes e Internet
2. Centro de redes y recursos compartidos
3. Click en tu red
4. Detalles
5. Ver "Dirección IPv4"

**Tu IP local:** `192.168.1.50` (ejemplo)

---

### 8.2 Configurar CORS

Editar `.env`:

```bash
ALLOWED_ORIGINS=http://localhost:8000,http://192.168.1.50:8000
```

**Si tienes múltiples IPs:**
```bash
ALLOWED_ORIGINS=http://localhost:8000,http://192.168.1.50:8000,http://192.168.1.100:8000
```

---

### 8.3 Configurar Firewall Windows

**Permitir puerto 8000:**

**Método 1: GUI**
1. Win+R → `wf.msc` → Enter (Firewall avanzado)
2. Click "Reglas de entrada" (izquierda)
3. Click "Nueva regla..." (derecha)
4. Tipo de regla: "Puerto" → Siguiente
5. Protocolo: TCP
6. Puertos locales específicos: `8000`
7. Siguiente
8. Acción: "Permitir la conexión"
9. Siguiente
10. Perfiles: marcar Dominio, Privado, Público
11. Siguiente
12. Nombre: `CRM Application Port 8000`
13. Finalizar

**Método 2: CMD (admin)**
```cmd
netsh advfirewall firewall add rule name="CRM Port 8000" dir=in action=allow protocol=TCP localport=8000
```

---

### 8.4 Testing Acceso Red

**Desde otro PC en la red:**

1. Abrir navegador
2. Ir a: `http://192.168.1.50:8000`
3. Debe aparecer login CRM

**Troubleshooting:**
- No carga → verificar firewall
- "No se puede acceder" → verificar IP correcta
- "CORS error" → actualizar ALLOWED_ORIGINS en .env

---

### 8.5 Comunicación a Usuarios

**Email plantilla:**

```
Asunto: Acceso al CRM Seguimiento Clientes

Hola equipo,

El nuevo CRM ya está disponible. 

ACCESO:
URL: http://192.168.1.50:8000
Usuario: tu-email@empresa.com
Contraseña: (enviada por separado)

IMPORTANTE:
- Acceso SOLO desde red interna de la empresa
- NO funciona desde casa (sin VPN)
- Usa Chrome o Edge actualizado

DOCUMENTACIÓN:
- Manual de usuario: adjunto
- Dudas: contactar con [nombre admin]

PRIMER LOGIN:
1. Abre el navegador
2. Ve a http://192.168.1.50:8000
3. Ingresa tus credenciales
4. Cambia tu contraseña (recomendado)

Cualquier problema, contactar inmediatamente.

Saludos,
[Nombre Admin]
```

---

[CONTINÚA EN SIGUIENTE MENSAJE...]
