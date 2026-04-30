# 📖 Guía de Usuario - CRM v2.0

Guía completa para usar el sistema CRM de seguimiento comercial.

---

## 🆕 Novedades de la v2.0

| Área | Qué hay nuevo |
|------|--------------|
| **Roles** | Nuevo rol **Commercial** con acceso filtrado a sus propios datos |
| **Tareas** | Gestión completa de tareas desde el kanban y desde clientes |
| **Oportunidades** | Campos estratégicos, motivo de pérdida, integración IA |
| **Formularios** | El responsable/asignado se preselecciona con el usuario actual al crear |
| **Permisos** | Commercial puede crear y editar sus propios recursos sin necesitar a sales |

---

## 🚀 Primeros Pasos

### **1. Acceder al Sistema**

```
1. Abrir navegador (Chrome, Edge o Firefox)
2. Ir a la URL proporcionada por el administrador
3. Iniciar sesión:
   - Usuario: tu email
   - Contraseña: proporcionada por el administrador
```

**Primera vez:** Contacta al administrador para que te cree el usuario con el rol adecuado.

---

### **2. Navegación Principal**

```
┌──────────────────────────────────────────┐
│ CRM  [Dashboard]  [Clientes]  [Tareas] [?] │  ← Barra superior
└──────────────────────────────────────────┘
```

**Secciones:**
- **Dashboard**: Vista general, KPIs, Kanban de oportunidades
- **Clientes**: Gestión completa de clientes y contactos
- **Tareas**: Listado y gestión de todas tus tareas
- **?**: Ayuda (esta guía)
- **Usuario** (esquina derecha): Perfil y cerrar sesión

---

## 👤 Roles y Permisos

El sistema tiene cuatro roles. Cada uno ve y puede hacer cosas distintas.

### **Tabla de permisos**

| Acción | Admin | Sales | Commercial | Viewer |
|--------|-------|-------|------------|--------|
| Ver todos los clientes | ✅ | ✅ | ❌ (solo los suyos) | ✅ |
| Crear clientes | ✅ | ✅ | ✅ | ❌ |
| Editar clientes | ✅ | ✅ | ✅ (solo los suyos) | ❌ |
| Archivar clientes | ✅ | ✅ | ❌ | ❌ |
| Ver todas las oportunidades | ✅ | ✅ | ❌ (solo las suyas) | ✅ |
| Crear oportunidades | ✅ | ✅ | ✅ | ❌ |
| Editar oportunidades | ✅ | ✅ | ✅ (solo las suyas) | ❌ |
| Cerrar como Ganada/Perdida | ✅ | ✅ | ❌ | ❌ |
| Mover tarjetas en kanban | ✅ | ✅ | ✅ (solo las suyas) | ❌ |
| Crear tareas | ✅ | ✅ | ✅ | ❌ |
| Editar tareas | ✅ | ✅ | ✅ (solo las suyas) | ❌ |
| Completar tareas | ✅ | ✅ | ✅ | ✅ |
| Gestionar usuarios | ✅ | ❌ | ❌ | ❌ |
| Gestionar catálogos | ✅ | ❌ | ❌ | ❌ |

### **Detalle de cada rol**

**Admin** — Acceso total al sistema, gestión de usuarios y configuración.

**Sales** — Acceso completo al CRM (clientes, oportunidades, tareas) sin gestión de usuarios ni catálogos.

**Commercial** — Acceso restringido a sus propios datos:
- Solo ve sus propios clientes, oportunidades y tareas en el kanban
- Puede crear recursos nuevos (el responsable se asigna automáticamente a él)
- Puede editar y eliminar sus propios recursos
- **No puede** cerrar oportunidades como Ganada/Perdida (lo hace sales/admin)
- **No puede** ver ni editar datos de otros usuarios

**Viewer** — Solo lectura. Puede ver y completar tareas asignadas a él, nada más.

---

## 📊 Dashboard

### **Vista Overview**

**KPIs Principales:**

```
┌─────────────────────────────────────┐
│  Pipeline Total:     €500,000       │  ← Suma de todas las oportunidades abiertas
│  Pipeline Ponderado: €250,000       │  ← Ajustado por probabilidad de cierre
│  Cerrado Anual:      €180,000       │  ← Suma de lo ganado este año
│  Objetivo Anual:     €1,000,000     │  ← Meta del año
└─────────────────────────────────────┘
```

**Cómo interpretar:**
- **Pipeline Total**: Valor máximo si ganas todo
- **Pipeline Ponderado**: Valor esperado realista
- **% Objetivo**: Cuánto llevas del objetivo anual
- **Pacing**: Si vas por buen camino (verde) o retrasado (rojo)

> **Commercial**: los KPIs solo reflejan sus propias oportunidades.

---

### **Vista Kanban**

El Kanban muestra las oportunidades organizadas por etapa.

**Etapas del Pipeline:**
```
[New] → [Contacted] → [Qualified] → [Proposal] → [Negotiation] → [Won/Lost]
  5%       10%           30%           50%            70%           100%/0%
```

**Usar el Kanban:**

1. **Ver oportunidades:**
   - Cada tarjeta = 1 oportunidad
   - Muestra: Cliente, Valor, Probabilidad, Próxima tarea, Responsable

2. **Mover oportunidades (drag & drop):**
   - Arrastrar tarjeta a otra columna
   - Sistema actualiza probabilidad y pipeline automáticamente
   - Crea registro en el historial de actividad
   - ⚠️ No se puede arrastrar directamente a Won/Lost (usar el botón de cierre)

3. **Filtrar:**
   - Por región, tipo de cliente, responsable
   - Buscar por nombre de cuenta
   - Ocultar/mostrar columnas cerradas (Won/Lost)

4. **Abrir detalle:**
   - Click en tarjeta → Drawer lateral con detalle completo

5. **Crear nueva oportunidad:**
   - Botón "Nueva Oportunidad" (parte superior derecha)

**Ejemplo de tarjeta:**
```
┌────────────────────────┐
│ ACME Corp              │  ← Nombre del cliente
│ €50,000  [50%]         │  ← Valor y probabilidad
│ 📋 Enviar propuesta    │  ← Próxima tarea
│ 📅 20 Ene              │  ← Fecha límite de la tarea
│ 👤 Juan García         │  ← Responsable
│ 🏷️ Madrid  Industria   │  ← Badges
└────────────────────────┘
```

**Cerrar una oportunidad:**
```
Roles admin / sales:
1. Abrir detalle de la oportunidad
2. Botón "Cerrar" → Seleccionar Ganada o Perdida
3. Rellenar motivo (si perdida) y valor final (si ganada)
4. Confirmar

El commercial solo puede mover etapas abiertas; el cierre lo gestiona sales/admin.
```

---

## 👥 Gestión de Clientes

### **Listar Clientes**

```
Navegación: CRM → Clientes
```

**Vista principal:**
- Tabla con todos los clientes (commercial: solo los suyos)
- Búsqueda por nombre
- Filtros: Tipo, Región, Fuente, Responsable, Estado

**Filtros:**
```
[Estado: Activos ▼]  [Tipo: Todos ▼]  [Región: Todas ▼]  [🔍 Buscar...]
```

---

### **Crear Nuevo Cliente**

```
1. Click "Nuevo Cliente" (botón superior derecha)

2. Rellenar formulario:

   BÁSICO:
   - Nombre *                    (Obligatorio)

   CONTACTO:
   - Sitio Web                   (Ejemplo: www.ejemplo.com)
   - Teléfono                    (Ejemplo: +34 912345678)
   - Email                       (Ejemplo: info@ejemplo.com)
   - CIF/NIF                     (Ejemplo: B12345678)
   - Dirección                   (Texto libre)

   CLASIFICACIÓN:
   - Tipo de Cliente             (Dropdown: Distribuidor, Instalador...)
   - Región                      (Dropdown: Madrid, Barcelona...)
   - Fuente de Lead              (Dropdown: Web, Referido...)
   - Detalle de Fuente           (Texto libre: nombre del referido, etc.)
   - Responsable                 (Se preselecciona con el usuario actual)

   NOTAS:
   - Notas adicionales           (Texto libre)

3. Click "Crear"

✅ Toast verde: "Cliente creado correctamente"
```

**Notas por rol:**
- **Commercial**: El campo "Responsable" se fija automáticamente a su usuario y no se puede cambiar desde el backend (aunque lo cambies en el formulario, el sistema lo sobreescribe).
- **Admin / Sales**: Pueden asignar cualquier responsable.

---

### **Ver Detalle de Cliente**

Click en cualquier cliente de la lista → Modal de detalle.

**Secciones del detalle:**

```
┌─────────────────────────────────────┐
│  ACME Corporation            [✏️] [🗑️] │
├─────────────────────────────────────┤
│                                     │
│  📋 INFORMACIÓN BÁSICA               │
│  Tipo: Distribuidor                 │
│  Región: Madrid                     │
│  Responsable: Juan García           │
│  ...                                │
│                                     │
│  📞 INFORMACIÓN DE CONTACTO          │
│  Web: www.acme.com                  │
│  Tel: +34 912345678                 │
│  ...                                │
│                                     │
│  👥 CONTACTOS              [+ Añadir]│
│  Juan García  |  Gerente            │
│  juan@acme.com [Principal]          │
│                                     │
│  💼 OPORTUNIDADES        [Ver Kanban]│
│  (Lista de oportunidades activas)   │
│                                     │
│  📋 TAREAS               [+ Nueva]  │
│  (Lista de tareas del cliente)      │
│                                     │
└─────────────────────────────────────┘
```

---

### **Editar y Archivar Cliente**

**Editar:**
```
1. Abrir detalle del cliente
2. Click botón ✏️ (superior derecha)
3. Modificar campos → "Guardar Cambios"

Commercial: solo puede editar clientes de los que es responsable.
```

**Archivar:**
```
1. Abrir detalle
2. Click 🗑️ → Confirmar

⚠️ No se elimina físicamente. Para ver archivados:
[Estado: Activos ▼] → "Archivados"
```

---

## 👤 Gestión de Contactos

Los contactos son personas dentro de los clientes.

### **Añadir Contacto**

```
1. Abrir detalle del cliente
2. Sección "Contactos" → Click "Añadir"
3. Rellenar formulario:

   BÁSICO:
   - Nombre / Apellidos
   - Rol  (Gerente, Director, Técnico...)

   EMAILS:           [+ Añadir más]
   - email@ejemplo.com  [⭐ Principal]  [🗑️]

   TELÉFONOS:        [+ Añadir más]
   - +34 666777888   [⭐ Principal]  [🗑️]

4. Marcar ⭐ en el email/teléfono preferido
5. Click "Crear"
```

**Características:**
- Múltiples emails y teléfonos por contacto
- Solo uno puede ser principal por tipo
- Se pueden añadir o quitar canales libremente

---

## 💼 Gestión de Oportunidades

### **Crear Oportunidad**

```
Desde Kanban → Botón "Nueva Oportunidad"

Campos:
- Cuenta *               (Dropdown: clientes existentes)
- Nombre de Oportunidad  (Texto libre)
- Stage *                (Etapa inicial)
- Valor Esperado (EUR) * (Número)
- Forecast Close Month   (Mes estimado de cierre)

✅ Oportunidad creada, aparece en el kanban
```

**Commercial:** El responsable se asigna automáticamente a su usuario.

---

### **Editar Oportunidad**

Desde el drawer lateral (click en tarjeta del kanban):

**Campos editables:**
```
BÁSICO:
- Nombre, Valor esperado, Stage
- Fecha forecast de cierre
- Responsable (solo admin/sales)

ESTRATÉGICO (v2.0):
- Tipo de oportunidad        (Dropdown de catálogo)
- Estado mental del cliente  (Dropdown: interesado, dudoso...)
- Objetivo estratégico       (Texto libre)
- Próxima acción estratégica (Texto libre)
- Resumen ejecutivo          (Texto libre)

INTEGRACIÓN IA (v2.0):
- URL sesión ChatGPT         (Enlace a conversación de IA)
- Notas sesión externa       (Apuntes de reunión/llamada)
```

---

### **Cerrar Oportunidad (Ganada / Perdida)**

*Solo admin y sales.*

```
GANADA:
1. Drawer → Botón "Cerrar como Ganada"
2. Confirmar valor final ganado
3. Sistema registra cierre, suma a KPI "Cerrado Anual"

PERDIDA:
1. Drawer → Botón "Cerrar como Perdida"
2. Seleccionar motivo de pérdida (catálogo)
3. Añadir detalle opcional
4. Sistema registra cierre
```

**Auto-cierre por stage:** Si se arrastra una tarjeta a la columna Won o Lost (si está habilitada), el sistema cierra automáticamente la oportunidad.

---

## 📋 Gestión de Tareas

Las tareas representan acciones concretas vinculadas a un cliente o una oportunidad.

### **Crear Tarea**

```
Desde Dashboard → Tab "Tareas" → "Nueva Tarea"
O desde el detalle de cliente/oportunidad → "Añadir Tarea"

Campos:
- Título *               (Obligatorio)
- Descripción            (Texto libre)
- Tipo de tarea          (Dropdown: Llamada, Reunión, Email...)
- Oportunidad            (Vincular a oportunidad)
- Cliente                (Vincular a cliente)
- Prioridad              (Alta / Media / Baja)
- Fecha límite           (Fecha)
- Asignado a             (Se preselecciona con el usuario actual)
- Recordatorio           (Fecha opcional)

✅ Tarea creada, aparece en el listado
```

> Al menos uno de "Oportunidad" o "Cliente" debe estar informado.

---

### **Estados de Tarea**

```
open → in_progress → completed
  ↓
cancelled  (eliminar = cancelar, no borrado físico)
```

| Estado | Descripción |
|--------|-------------|
| **open** | Pendiente de iniciar |
| **in_progress** | En curso |
| **completed** | Terminada |
| **cancelled** | Cancelada (baja lógica) |

---

### **Editar y Completar Tareas**

**Editar:**
```
Lista de tareas → Click en tarea → Editar
Commercial: solo puede editar tareas que él creó o que le están asignadas.
```

**Completar:**
```
Cualquier usuario puede completar sus tareas asignadas:
Lista de tareas → Botón ✅ → Tarea marcada como completada
```

**Eliminar (cancelar):**
```
Lista de tareas → Botón 🗑️ → Estado pasa a "cancelled"
Commercial: solo puede cancelar sus propias tareas.
```

---

### **Filtros de Tareas**

```
[Asignado a: Yo ▼]
[Estado: Pendientes ▼]
[Prioridad: Alta ▼]
[Oportunidad: ... ▼]
[Tipo: Llamada ▼]
☐ Solo vencidas
```

---

## 🎯 Flujo de Trabajo Típico

### **Escenario: Nuevo Lead (rol Commercial)**

```
1. CREAR CLIENTE
   Clientes → Nuevo Cliente
   - Nombre, Región, Tipo, Fuente
   - Responsable: se rellena solo con tu usuario

2. AÑADIR CONTACTO
   Detalle cliente → Añadir contacto
   - Nombre, Rol, Email principal, Teléfono

3. CREAR OPORTUNIDAD
   Dashboard → Kanban → Nueva Oportunidad
   - Cliente, Valor, Stage inicial
   - Responsable: se asigna automáticamente

4. CREAR TAREA DE SEGUIMIENTO
   Drawer de oportunidad → Nueva tarea
   - "Llamar para calificar"  |  Prioridad: Alta  |  Fecha: mañana
   - Asignado a: [tu usuario - preseleccionado]

5. MOVER EN KANBAN
   Arrastrar tarjeta según avanza la negociación
   New → Contacted → Qualified → ...

6. SOLICITAR CIERRE A SALES/ADMIN
   Cuando llegue a Negotiation, avisar a sales/admin
   para que cierren como Ganada/Perdida
```

---

### **Escenario: Actualizar Oportunidad**

```
1. Dashboard → Kanban
2. Buscar oportunidad (filtros o búsqueda)
3. Arrastrar tarjeta a nueva etapa
4. Sistema actualiza:
   - Probabilidad automáticamente
   - Pipeline ponderado
   - Historial de actividad (registro automático)
```

---

### **Escenario: Cerrar Venta (Won) — Sales/Admin**

```
1. Kanban → Oportunidad en "Negotiation"
2. Click en tarjeta → Drawer
3. Botón "Cerrar como Ganada"
4. Rellenar:
   - Fecha de cierre
   - Valor final ganado (por defecto: valor esperado)
5. Confirmar
6. Sistema:
   - Marca como Ganada
   - Suma a "Cerrado Anual"
   - Crea actividad en historial
   - Actualiza KPIs
   - Guarda snapshot para análisis IA
```

---

## 🔍 Búsqueda y Filtros

### **Buscar Clientes**

```
En lista de clientes:
[🔍 Buscar...]  → Escribir nombre
```

**Filtros combinables:**
```
[Estado: Activos] [Tipo: Distribuidor] [Región: Madrid] [Responsable: Juan]
→ Muestra solo clientes que cumplan TODOS los filtros
```

### **Buscar en Kanban**

```
[🔍 Buscar cuenta...]   Barra superior

Filtros:
☐ Ocultar cerradas (Won/Lost)
[Owner: Todos ▼]

Commercial: el kanban ya filtra solo sus oportunidades, sin opción de ver las de otros.
```

---

## ⚙️ Configuración

*Requiere rol **admin***

### **Gestionar Catálogos**

Desde el menú Config:

| Catálogo | Para qué se usa |
|----------|----------------|
| **Tipos de Cliente** | Distribuidor, Instalador, OEM... |
| **Regiones** | 17 CCAA de España (pre-cargadas) |
| **Fuentes de Lead** | Web, Referido, Evento, Frío... |
| **Stages** | Etapas del pipeline (nombre, probabilidad, orden) |
| **Tipos de Oportunidad** | Categorías de negocio |
| **Motivos de Pérdida** | Por qué se pierde una oportunidad |
| **Estado Mental del Cliente** | Interesado, Dudoso, En pausa... |
| **Tipos de Tarea** | Llamada, Reunión, Demo, Email... |
| **Plantillas de Tarea** | Tareas predefinidas con título y prioridad |

---

### **Gestionar Usuarios**

```
Admin → Usuarios → Lista de usuarios

Acciones:
- Crear usuario nuevo (nombre, email, rol, contraseña)
- Cambiar rol
- Activar / Desactivar
- Reset de contraseña

Roles disponibles: admin | sales | commercial | viewer
```

---

## 💡 Consejos y Mejores Prácticas

### **Para el Commercial**

✅ **DO:**
- Crear la tarea de seguimiento justo al crear la oportunidad
- Asegurarte de que "Asignado a" eres tú al crear tareas (viene preseleccionado)
- Mover tus tarjetas en el kanban conforme avanza la negociación
- Avisar a sales/admin cuando una oportunidad llegue a Negotiation

❌ **DON'T:**
- Crear tareas sin asignarlas — no podrás editarlas después
- Intentar ver clientes de otros (obtendrás error 403)

---

### **Pipeline Saludable**

**Balance recomendado:**
```
New:          10-20%  → Entrada constante de leads
Contacted:    15-20%  → Calificación activa
Qualified:    20-25%  → Oportunidades reales
Proposal:     20-25%  → En negociación
Negotiation:  15-20%  → Próximas a cerrar
```

**Si ves:**
- Mucho en New → Falta calificación
- Mucho en Qualified → Falta acción comercial
- Poco en Proposal → Pipeline débil

---

### **Seguimiento Efectivo**

**Frecuencia recomendada:**
- New → Contactar en 24h
- Contacted → Seguir en 2-3 días
- Qualified → Seguir semanalmente
- Proposal → Seguir cada 3-4 días
- Negotiation → Seguir diariamente

**Usar tareas correctamente:**
- Siempre con fecha límite
- Título claro ("Llamar a Juan para confirmar propuesta")
- Asignar a quien realmente va a hacerla

---

## 🆘 Preguntas Frecuentes

### **¿Por qué no veo los clientes/oportunidades de mis compañeros?**
```
Si tu rol es "commercial", el sistema solo te muestra
tus propios datos. Es el comportamiento esperado.
Para ver todos los datos, necesitas rol sales o admin.
```

---

### **Creé una tarea y ahora no puedo editarla, ¿por qué?**
```
Asegúrate de que la tarea está asignada a ti o de que
fuiste tú quien la creó. Si la creó otro usuario o está
asignada a otro, necesitas rol sales/admin para editarla.

Al crear tareas, el campo "Asignado a" viene preseleccionado
con tu usuario — no lo desmarques si quieres poder editarla.
```

---

### **¿Cómo cierro una oportunidad como Ganada?**
```
El rol commercial NO puede cerrar oportunidades.
Debes avisar a un usuario sales o admin para que
realice el cierre con el valor y fecha correctos.
```

---

### **¿Puedo recuperar un cliente archivado?**
```
Sí:
1. Filtro Estado → "Archivados"
2. Abrir detalle del cliente
3. Botón "Reactivar"
```

---

### **¿Qué pasa si importo datos duplicados?**
```
Sistema hace "upsert" por nombre:
- Si existe el cliente → actualiza
- Si no existe → crea nuevo
```

---

### **¿Cómo exporto datos?**
```
Actualmente no hay export automático desde la UI.
Alternativa: Contactar al administrador de sistema.
```

---

### **¿Puedo eliminar permanentemente un cliente o tarea?**
```
No desde la UI (es baja lógica para auditoría).
Clientes → se archivan
Tareas   → se cancelan
Si necesitas borrado físico, contacta al administrador.
```

---

## 📞 Soporte

**¿Necesitas ayuda?**

1. Consultar esta guía
2. Contactar a tu administrador de sistema
3. Reportar bug: indicar pasos para reproducir + rol de usuario

---

**Versión de la Guía:** v2.0.0
**Última actualización:** 30 Abril 2026
