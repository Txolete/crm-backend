# 📘 MANUAL DE USUARIO - CRM SEGUIMIENTO CLIENTES

**Versión:** 0.7.0  
**Fecha:** Enero 2026  
**Audiencia:** Usuarios comerciales, ventas, dirección

---

## ÍNDICE

1. [Introducción](#1-introducción)
2. [Inicio Rápido](#2-inicio-rápido)
3. [Dashboard - Vista General](#3-dashboard---vista-general)
4. [Kanban - Gestión Visual](#4-kanban---gestión-visual)
5. [Gestión de Datos](#5-gestión-de-datos)
6. [Import Excel](#6-import-excel)
7. [Configuración](#7-configuración)
8. [Automatizaciones y Email](#8-automatizaciones-y-email)
9. [Consejos y Mejores Prácticas](#9-consejos-y-mejores-prácticas)
10. [Solución de Problemas](#10-solución-de-problemas)
11. [Soporte](#11-soporte)

---

## 1. INTRODUCCIÓN

### 1.1 Objetivo del Sistema

El **CRM Seguimiento Clientes** es una herramienta diseñada para:

- **Centralizar** toda la información comercial en un solo lugar
- **Visualizar** el estado de las oportunidades en tiempo real
- **Automatizar** tareas rutinarias y recordatorios
- **Analizar** el pipeline y la conversión de ventas
- **Mejorar** el seguimiento y la coordinación del equipo comercial

### 1.2 Alcance

**Módulos incluidos:**
- ✅ Dashboard con KPIs y gráficos
- ✅ Kanban visual de oportunidades
- ✅ Gestión de cuentas, contactos, oportunidades y tareas
- ✅ Importación masiva desde Excel
- ✅ Configuración de catálogos
- ✅ Automatizaciones diarias
- ✅ Notificaciones por email

**Características principales:**
- Acceso web desde cualquier navegador
- Multi-usuario con roles (admin, sales, viewer)
- Historial completo de actividades
- Base de datos local (SQLite) o servidor (PostgreSQL)
- Sin necesidad de instalación de software adicional

### 1.3 Roles de Usuario

**Admin:**
- Acceso total al sistema
- Gestión de usuarios
- Configuración de catálogos
- Importación de datos
- Ejecución manual de automatizaciones

**Sales:**
- Acceso completo a CRM
- Crear/editar cuentas, oportunidades, tareas
- Importación de datos
- NO puede gestionar usuarios ni configuración

**Viewer:**
- Solo lectura
- Ver dashboard, kanban, oportunidades
- NO puede crear ni editar

---

## 2. INICIO RÁPIDO

### 2.1 Primer Acceso

**URL:** http://localhost:8000

**Pantalla de Login:**
- Email: tu email corporativo
- Password: contraseña asignada

**Credenciales por defecto (primera instalación):**
- Admin: `admin@example.com` / `admin123`
- ⚠️ **Cambiar contraseña inmediatamente después del primer login**

### 2.2 Qué Hacer Cada Día

**Flujo diario recomendado:**

1. **Revisar email** (07:30 AM)
   - Revisa el resumen diario de tareas enviado automáticamente
   - Identifica tareas vencidas y próximas

2. **Abrir el CRM** (08:00 AM)
   - Click en tab **"Mis Tareas"** del dashboard
   - Prioriza tareas vencidas (rojo) y próximas (amarillo)

3. **Actualizar Kanban** (durante el día)
   - Mueve tarjetas según avance real
   - Añade actividades después de cada interacción
   - Crea nuevas tareas de seguimiento

4. **Cerrar oportunidades** (cuando corresponda)
   - Marca como Won (ganadas) o Lost (perdidas)
   - Registra razón de cierre y valor final

5. **Revisar Dashboard** (final del día)
   - Verifica que todo esté actualizado
   - Revisa KPIs de pipeline y conversión

### 2.3 Navegación Principal

**Barra superior:**
- Logo CRM (volver a inicio)
- Dashboard (icono 📊)
- Configuración (icono ⚙️, solo admin)
- Usuario actual (esquina derecha)
- Logout (cerrar sesión)

**Tabs del Dashboard:**
- **Overview:** KPIs, gráficos, análisis
- **Kanban:** Vista de tarjetas por etapa
- **Mis Tareas:** Semáforo de tareas (vencidas, próximas, futuras)

---

## 3. DASHBOARD - VISTA GENERAL

### 3.1 KPIs Principales

El dashboard muestra 6 KPIs clave:

**KPI A - Pipeline Total:**
- Suma del valor esperado de todas las oportunidades abiertas
- Fórmula: `SUM(expected_value) WHERE close_outcome='open'`
- Color: azul
- Interpretación: "cuánto tenemos en juego"

**KPI B - Pipeline Ponderado:**
- Pipeline ajustado por probabilidad de cierre
- Fórmula: `SUM(expected_value * probability) WHERE close_outcome='open'`
- Color: verde
- Interpretación: "cuánto esperamos cerrar realmente"

**KPI C - Cerrado Anual:**
- Total ganado en el año actual
- Fórmula: `SUM(won_value) WHERE close_outcome='won' AND year=current`
- Color: verde brillante
- Interpretación: "cuánto hemos ganado este año"

**Target Anual:**
- Objetivo configurado para el año
- Click en "Editar Targets" para modificar
- Se divide en: target_pipeline_total, target_pipeline_weighted, target_closed

**Pacing Mensual:**
- `Target / 12` = objetivo promedio por mes
- Compara el ritmo actual vs objetivo
- Color rojo si estamos por debajo, verde si por encima

**Conversión (C/A):**
- `(Cerrado / Pipeline Total) * 100`
- Porcentaje de conversión histórica
- Ayuda a estimar probabilidades futuras

### 3.2 Filtros

**Filtros disponibles:**
- **Canal:** filtrar por lead source (LinkedIn, Web, Referidos, etc)
- **Tipo Cliente:** filtrar por customer type (Empresa, Pyme, etc)
- **Provincia:** filtrar por región geográfica
- **Owner:** filtrar por responsable comercial
- **Año:** seleccionar año fiscal

**Cómo aplicar filtros:**
1. Selecciona valores en los desplegables
2. Click "Aplicar"
3. Dashboard se actualiza automáticamente
4. Los KPIs y gráficos reflejan el filtro
5. Click "Reset" para limpiar filtros

**Indicador de filtros activos:**
- Aparece un mensaje debajo de los filtros
- Ejemplo: "Filtrando por: Canal=LinkedIn, Provincia=Madrid"

### 3.3 Gráficos

**Gráfico 1: Pacing - Cerrado Acumulado**
- Línea del tiempo (eje X: meses, eje Y: EUR)
- Compara cerrado acumulado vs objetivo
- Línea azul: real acumulado
- Línea roja: objetivo teórico (lineal)
- Identifica si vamos adelantados o atrasados

**Gráfico 2: Pipeline por Stage**
- Barras horizontales
- Muestra el valor total en cada etapa
- Colores según outcome (open=azul, won=verde, lost=rojo)
- Identifica dónde se concentra el pipeline

**Gráfico 3: Pipeline por Canal**
- Gráfico circular (pie chart)
- Distribución por lead source
- Colores distintos para cada canal
- Identifica canales más productivos

**Gráfico 4: Conversión Mensual (C/A)**
- Línea del tiempo (eje X: meses, eje Y: %)
- Evolución de la tasa de conversión
- Identifica tendencias de mejora/empeoramiento

**Interacción:**
- Hover sobre elementos para ver valores exactos
- Click en leyenda para ocultar/mostrar series

---

## 4. KANBAN - GESTIÓN VISUAL

### 4.1 Vista Kanban

**Columnas (stages):**
1. **New** (5%) - Nuevas oportunidades sin contactar
2. **Contacted** (10%) - Primer contacto realizado
3. **Qualified** (30%) - Oportunidad calificada
4. **Proposal** (50%) - Propuesta enviada
5. **Negotiation** (70%) - Negociación avanzada
6. **Won** (100%) - Ganadas (ocultas por defecto)
7. **Lost** (0%) - Perdidas (ocultas por defecto)

**Tarjetas:**
Cada tarjeta muestra:
- Nombre de la cuenta (bold)
- Valor esperado (EUR)
- Valor ponderado o %
- Próxima tarea (título + fecha)
- Badges: canal, provincia

**Colores:**
- Azul: oportunidades abiertas
- Verde: won
- Rojo: lost
- Amarillo: task próxima a vencer
- Rojo: task vencida

### 4.2 Drag & Drop

**Mover oportunidades:**
1. Click y mantén sobre una tarjeta
2. Arrastra a la columna destino
3. Suelta
4. El sistema actualiza automáticamente:
   - stage_id
   - Crea activity "Status change: [old] → [new]"
   - Registra en audit log

**Reglas:**
- No se puede mover a columnas ocultas (won/lost) por drag&drop
- Para cerrar, usa el drawer (botones Won/Lost)

### 4.3 Opportunity Drawer

**Abrir drawer:**
- Click en cualquier tarjeta del kanban
- Se abre panel lateral derecho

**Secciones del drawer:**

**1. Información básica:**
- Nombre cuenta (editable)
- Stage actual
- Valor esperado (editable)
- Valor ponderado (calculado o override)
- Forecast close month
- Owner (responsable)

**2. Contactos:**
- Lista de contactos asociados
- Nombre, rol, email, teléfono
- Botón "Añadir contacto"

**3. Tareas:**
- Lista de tareas abiertas y cerradas
- Título, due date, asignado a
- Check para marcar como completada
- Botón "Nueva tarea"

**4. Timeline de actividades:**
- Historial completo de interacciones
- Tipos: call, email, meeting, note, status_change, system
- Timestamp + usuario + resumen
- Las más recientes arriba

**Acciones del drawer:**

**Botón "Won" (verde):**
- Marca oportunidad como ganada
- Pide: won_value (valor final), close_date
- Cierra oportunidad (close_outcome='won')
- Actualiza KPI C

**Botón "Lost" (rojo):**
- Marca oportunidad como perdida
- Pide: lost_reason (motivo de pérdida)
- Cierra oportunidad (close_outcome='lost')
- Oculta del kanban

**Botón "Actualizar":**
- Guarda cambios en campos editables
- Crea audit log

**Botón "Cerrar" (X):**
- Cierra el drawer sin guardar cambios pendientes

### 4.4 Filtros del Kanban

**Búsqueda:**
- Campo de texto libre
- Busca por nombre de cuenta
- Actualización en tiempo real

**Checkbox "Ocultar cerradas":**
- Oculta columnas Won y Lost
- Foco en pipeline activo

**Botón "Nueva Oportunidad":**
- Abre modal para crear oportunidad
- Campos: cuenta, nombre, stage, valor esperado, forecast

---

## 5. GESTIÓN DE DATOS

### 5.1 Cuentas (Accounts)

**Qué es una cuenta:**
- Empresa u organización cliente/prospecto
- Entidad principal del CRM
- Contiene: contactos, oportunidades

**Campos de cuenta:**
- **Nombre:** razón social (requerido)
- **Provincia:** región geográfica
- **Tipo Cliente:** categoría (Empresa, Pyme, etc)
- **Canal:** lead source (de dónde viene)
- **Owner:** responsable comercial

**Crear cuenta:**
1. Click "Nueva Oportunidad" en kanban
2. Selecciona cuenta existente o crea nueva
3. Si creas nueva: ingresa nombre y datos

**Editar cuenta:**
1. Abre opportunity drawer
2. Click en nombre de cuenta
3. Modifica campos
4. Guardar

**Baja lógica:**
- Las cuentas no se eliminan físicamente
- Marcar como status='archived'
- Solo admin puede archivar

### 5.2 Contactos (Contacts)

**Qué es un contacto:**
- Persona física en una cuenta
- Rol específico (Gerente, Compras, Técnico, etc)
- Emails y teléfonos

**Campos de contacto:**
- **Nombre:** first_name + last_name
- **Rol:** contact role (Gerente, Compras, etc)
- **Email(s):** uno o más, uno primary
- **Teléfono(s):** uno o más, uno primary
- **Cuenta:** a qué empresa pertenece

**Crear contacto:**
1. Desde opportunity drawer
2. Click "Añadir contacto"
3. Completa formulario
4. Guardar

**Email/Teléfono principal:**
- Marca checkbox "Principal"
- Se usa para comunicaciones principales

### 5.3 Oportunidades (Opportunities)

**Qué es una oportunidad:**
- Posibilidad concreta de venta
- Asociada a una cuenta
- Tiene stage, valor, probabilidad

**Campos clave:**
- **Account:** cuenta asociada (requerido)
- **Name:** nombre descriptivo (opcional, auto-genera si vacío)
- **Stage:** etapa actual (requerido)
- **Expected Value:** valor esperado EUR (requerido)
- **Weighted Value Override:** forzar valor ponderado (opcional)
- **Probability Override:** forzar % probabilidad (opcional)
- **Forecast Close Month:** mes esperado de cierre (YYYY-MM)
- **Owner:** responsable comercial
- **Close Outcome:** open / won / lost
- **Won Value:** valor final si ganada
- **Lost Reason:** motivo si perdida

**Crear oportunidad:**
1. Click "Nueva Oportunidad" en kanban
2. Selecciona o crea cuenta
3. Nombre (opcional)
4. Stage inicial
5. Valor esperado
6. Forecast month
7. Crear

**Valores ponderados:**
- Si NO hay override: `weighted_value = expected_value * probability`
- Probability viene de cfg_stage_probabilities
- Si hay override: usa el valor manual

**Cerrar oportunidad:**
- **Won:** botón verde en drawer, ingresar won_value
- **Lost:** botón rojo en drawer, ingresar lost_reason
- Las cerradas se ocultan del kanban (checkbox "ocultar cerradas")

### 5.4 Tareas (Tasks)

**Qué es una tarea:**
- Acción específica a realizar
- Asociada a una oportunidad
- Due date y asignado

**Campos de tarea:**
- **Title:** descripción breve (requerido)
- **Due Date:** fecha límite
- **Status:** open / done
- **Assigned To:** usuario responsable
- **Opportunity:** oportunidad asociada

**Crear tarea:**
1. Desde opportunity drawer
2. Click "Nueva tarea"
3. Título + due date + asignado
4. Guardar

**Marcar como completada:**
- Checkbox en listado de tareas
- Cambia status='done'

**Tareas automáticas:**
- El sistema crea tareas automáticas:
  - "Seguimiento pendiente" (si no hay actividad 14 días)
  - "Seguimiento propuesta" (propuestas sin actividad 7 días)

### 5.5 Actividades (Activities)

**Qué es una actividad:**
- Registro de interacción o evento
- Historial completo en timeline
- No se edita ni elimina (solo lectura)

**Tipos de actividad:**
- **call:** llamada telefónica
- **email:** email enviado/recibido
- **meeting:** reunión presencial/virtual
- **note:** nota interna
- **status_change:** cambio de stage
- **system:** actividad automática del sistema

**Crear actividad:**
1. Desde opportunity drawer
2. Scroll a "Timeline"
3. Click "Nueva actividad"
4. Tipo + resumen
5. Occurred at (timestamp)
6. Guardar

**Actividades automáticas:**
- Cambio de stage (drag&drop)
- Overdue tasks (diarias)
- Follow-ups automáticos

---

## 6. IMPORT EXCEL

### 6.1 Formato Esperado

**Archivo:** `IMPORT_NORMALIZADO_CRM.xlsx`  
**Sheet:** `DATA`  
**1 fila = 1 oportunidad**

**Columnas requeridas:**
- account_name (texto)
- expected_value_eur (número)
- stage_key (texto: new, contacted, qualified, proposal, negotiation)

**Columnas opcionales:**
- region_name (provincia)
- customer_type_name (tipo cliente)
- lead_source_name (canal)
- lead_source_detail (detalle canal)
- contact_first_name
- contact_last_name
- contact_role_name
- contact_email
- contact_phone
- forecast_close_month (YYYY-MM)
- activity_summary
- next_step_title
- next_step_date (YYYY-MM-DD)
- owner_email

**Ejemplo:**

```
account_name | expected_value_eur | stage_key | region_name | contact_first_name | contact_email
ACME Corp    | 50000              | qualified | Madrid      | Juan               | juan@acme.com
Tech Inc     | 75000              | proposal  | Barcelona   | Maria              | maria@tech.com
```

### 6.2 Proceso de Importación

**Paso 1: Preparar archivo**
- Usa plantilla IMPORT_NORMALIZADO_CRM.xlsx
- Completa todas las filas
- Guarda como .xlsx (no .xls ni .csv)

**Paso 2: Subir archivo**
1. Dashboard → botón "Import Excel"
2. Click "Seleccionar archivo"
3. Busca tu .xlsx
4. Seleccionar

**Paso 3: Dry Run (recomendado)**
- Checkbox "Dry Run" marcado
- Click "Importar"
- Revisa reporte:
  - ✅ Filas válidas
  - ⚠️ Warnings (valores fuera de catálogo)
  - ❌ Errores (filas inválidas)
- NO se guarda nada en BD

**Paso 4: Importación real**
- Desmarca "Dry Run"
- Click "Importar"
- El sistema:
  - Crea/actualiza accounts (upsert por nombre)
  - Crea opportunities
  - Crea contactos (si existen datos)
  - Crea activities (si hay summary)
  - Crea tasks (si hay next_step)

**Paso 5: Revisar reporte**
- Muestra resumen:
  - Accounts creados/actualizados
  - Opportunities creadas
  - Contacts creados
  - Warnings y errores

### 6.3 Reglas de Importación

**Upsert de Accounts:**
- Si existe account con ese nombre → actualiza datos
- Si NO existe → crea nuevo account
- Comparación case-insensitive: "ACME" = "acme"

**Valores de catálogo:**
- Si región/tipo/canal existe en cfg_* → usa ese ID
- Si NO existe → guarda en *_other_text + genera warning
- Ejemplo: region_name="Galicia" pero no existe en catálogo
  - Se guarda en region_other_text="Galicia"
  - Warning: "Region 'Galicia' not found in catalog"

**Contactos:**
- Solo crea si existen: contact_first_name O contact_email
- Si faltan datos, no crea contacto
- Role: usa contact_role_name si existe en catálogo

**Activities:**
- Solo crea si activity_summary no está vacío
- Tipo: "note" por defecto
- occurred_at: fecha de import

**Tasks:**
- Solo crea si next_step_title no está vacío
- due_date: usa next_step_date si existe
- status: "open"

### 6.4 Warnings Comunes

**Warning: "Region 'XXX' not found"**
- Solución: Añade la provincia en Configuración antes de importar
- O acepta que se guarde como "other" y migra manualmente después

**Warning: "Empty row skipped"**
- Hay filas vacías en el Excel
- No es error, se ignoran automáticamente

**Warning: "Contact incomplete, skipped"**
- Falta first_name Y email
- Solución: completa los datos o deja vacío para no crear contacto

**Error: "account_name missing"**
- Fila sin nombre de cuenta
- Solución: completa account_name en todas las filas

**Error: "expected_value_eur invalid"**
- Valor no numérico o negativo
- Solución: usa números > 0

**Error: "stage_key invalid"**
- Stage no existe (typo)
- Solución: usa keys válidos (new, contacted, qualified, proposal, negotiation)

---

## 7. CONFIGURACIÓN

**Acceso:** Solo admin  
**URL:** http://localhost:8000/dashboard/config

### 7.1 Catálogos Disponibles

**7 catálogos configurables:**

1. **Provincias (Regions)**
   - name: nombre provincia
   - country_code: código país (default ES)
   - sort_order: orden de aparición
   - is_active: activo/inactivo

2. **Tipos de Cliente (Customer Types)**
   - name: nombre tipo (Empresa, Pyme, Autónomo, etc)
   - sort_order: orden
   - is_active

3. **Canales (Lead Sources)**
   - name: nombre canal (LinkedIn, Web, Referidos, etc)
   - category: categoría (opcional)
   - sort_order
   - is_active

4. **Roles de Contacto (Contact Roles)**
   - name: cargo/rol (Gerente, Compras, Técnico, etc)
   - sort_order
   - is_active

5. **Plantillas de Tarea (Task Templates)**
   - name: nombre plantilla
   - default_due_days: días por defecto
   - sort_order
   - is_active

6. **Etapas (Stages)**
   - key: identificador único (new, qualified, etc)
   - name: nombre visible
   - sort_order: orden en kanban
   - outcome: open / won / lost
   - is_terminal: etapa final true/false
   - is_active

7. **Probabilidades de Etapa (Stage Probabilities)**
   - stage_id: etapa asociada
   - probability: % de cierre (0.0 - 1.0)

### 7.2 Operaciones CRUD

**Crear elemento:**
1. Click "Crear" en el catálogo deseado
2. Completa formulario
3. Guardar
4. Aparece en listado

**Editar elemento:**
1. Click icono ✏️ (editar)
2. Modifica campos
3. Guardar

**Desactivar elemento:**
1. Click icono ❌ (desactivar)
2. Si está EN USO → modal de confirmación
3. "Forzar Operación" o "Cancelar"

**Activar elemento:**
1. Click icono ✓ (activar)
2. Elemento vuelve a estar disponible

### 7.3 Validación "EN USO"

**HOTFIX 7.1: Guardrails inteligentes**

Cuando intentas desactivar un valor que está en uso:

**Ejemplo:**
```
Intento: Desactivar provincia "Madrid"
Sistema detecta: 42 cuentas activas usan "Madrid"
Modal: "⚠️ Esta provincia está en uso por 42 cuenta(s) activa(s). ¿Forzar?"
Opciones:
  - Cancelar: no hace nada
  - Forzar Operación: desactiva de todos modos
```

**Casos que generan warning:**
- Desactivar provincia/tipo/canal/rol con registros activos
- Cambiar outcome de stage con oportunidades activas
- Marcar stage como terminal con opp abiertas

**Audit log diferenciado:**
- Si se fuerza: `action="deactivate_region_forced"`
- Flag `"forced": true` en audit log

**Recomendación:**
- Si un valor está en uso y quieres limpiarlo:
  1. Crea el nuevo valor
  2. Migra manualmente los registros (edita accounts/opps)
  3. Desactiva el valor antiguo cuando ya no esté en uso

### 7.4 Stages: Orden Visual

**Hint en UI:**
> "El Kanban usa **sort_order** para ordenar columnas."

**Ejemplo:**
```
Stage     | sort_order | Kanban Position
new       | 1          | Primera columna
contacted | 2          | Segunda columna
qualified | 3          | Tercera columna
...
```

**Cambiar orden:**
1. Editar stage
2. Cambiar sort_order
3. Guardar
4. Refrescar kanban → columnas reordenadas

**Duplicados:**
- Permitidos (no bloqueante)
- Si hay 2 stages con sort_order=3, orden alfabético

---

## 8. AUTOMATIZACIONES Y EMAIL

### 8.1 Qué Hacen las Automatizaciones

**3 automatizaciones diarias (07:00 AM por defecto):**

**A) Detección Tareas Vencidas:**
- Detecta tasks con due_date < hoy y status='open'
- Crea activity system en oportunidad
- Dedupe: 7 días (no repite mismo task)

**B) Oportunidades Sin Actividad (14 días):**
- Detecta opps sin actividad en 14+ días
- Crea task "Seguimiento pendiente" (due: hoy+3)
- Dedupe: 14 días (no duplica task)

**C) Propuestas Sin Seguimiento (7 días):**
- Detecta opps en stage "proposal" sin actividad 7+ días
- Crea task "Seguimiento propuesta" (due: hoy+2)
- Dedupe: 14 días

**Resultado:**
- Tasks automáticas aparecen en tu listado
- Emails diarios con resumen
- Activities type="system" registradas

### 8.2 Notificaciones Email

**Cuándo se envían:**
- Diariamente a las 07:00 AM (después de automatizaciones)
- Solo a usuarios activos
- Solo si tienes tareas (vencidas, próximas o futuras)

**Contenido del email:**
```
Asunto: CRM: Resumen Diario - 2 vencidas, 1 próxima

Hola [Tu Nombre],

📋 Resumen de tareas para hoy:

🔴 VENCIDAS (2)
- Llamar cliente | ACME Corp | Vence: 2026-01-05
- Reunión follow | XYZ Inc | Vence: 2026-01-06

🟡 PRÓXIMOS 2 DÍAS (1)
- Enviar presupuesto | Tech Solutions | Vence: 2026-01-08

🟢 PRÓXIMOS 10 DÍAS (3)
- Seguimiento | Startup Inc | Vence: 2026-01-12
- ...

[Ir al Dashboard]
```

**Configuración:**
- EMAIL_ENABLED=true/false en .env
- Si falta config SMTP → emails desactivados automáticamente
- Ver Guía Admin para configurar Gmail/Outlook

### 8.3 Ajustar Automatizaciones

**En archivo .env:**

```bash
# Enable/disable
AUTOMATIONS_ENABLED=true

# Hora de ejecución (24h format)
AUTO_RUN_TIME=07:00

# Thresholds (días)
AUTO_NO_ACTIVITY_DAYS=14        # Cambiar a 7, 21, etc
AUTO_PROPOSAL_NO_ACTIVITY_DAYS=7

# Dedupe windows
AUTO_OVERDUE_DEDUP_DAYS=7
AUTO_FOLLOWUP_DEDUP_DAYS=14
```

**Ejemplo: Cambiar a 10 días sin actividad**
1. Abrir .env
2. Cambiar `AUTO_NO_ACTIVITY_DAYS=14` a `AUTO_NO_ACTIVITY_DAYS=10`
3. Guardar
4. Reiniciar CRM (STOP_CRM.bat + START_CRM.bat)

**Desactivar completamente:**
- Cambiar `AUTOMATIONS_ENABLED=false`
- Reiniciar CRM
- No se ejecutarán automatizaciones ni emails

### 8.4 Ejecutar Manualmente (Admin)

**Para testing o ejecución on-demand:**

1. Login como admin
2. Navegador → F12 (Developer Tools)
3. Tab Console
4. Ejecutar:

```javascript
// Todas las automatizaciones
fetch('/admin/automations/run?job=all', {method:'POST', credentials:'include'})
  .then(r => r.json()).then(console.log);

// Solo emails
fetch('/admin/automations/run?job=emails', {method:'POST', credentials:'include'})
  .then(r => r.json()).then(console.log);

// Ver estado
fetch('/admin/automations/status', {credentials:'include'})
  .then(r => r.json()).then(console.log);
```

**Respuesta ejemplo:**
```json
{
  "success": true,
  "job": "all",
  "results": {
    "overdue": {"processed": 5, "skipped": 2},
    "no_activity": {"processed": 3, "skipped": 1},
    "proposal_followup": {"processed": 2, "skipped": 0}
  }
}
```

---

[CONTINÚA EN PARTE 2...]
