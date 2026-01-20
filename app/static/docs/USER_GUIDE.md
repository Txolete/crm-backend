# 📖 Guía de Usuario - CRM v1.0.0

Guía completa para usar el sistema CRM de seguimiento comercial.

---

## 🚀 Primeros Pasos

### **1. Acceder al Sistema**

```
1. Abrir navegador (Chrome, Edge o Firefox)
2. Ir a: http://localhost:8000
3. Iniciar sesión:
   - Usuario: admin (o tu usuario asignado)
   - Contraseña: (proporcionada por el administrador)
```

**Primera vez:** Cambiar contraseña en tu perfil.

---

### **2. Navegación Principal**

```
┌────────────────────────────────────┐
│ CRM  [Dashboard]  [Clientes]  [?] │  ← Barra superior
└────────────────────────────────────┘
```

**Secciones:**
- **Dashboard**: Vista general, KPIs, Kanban
- **Clientes**: Gestión completa de clientes y contactos
- **?**: Ayuda (esta guía)
- **Usuario**: Perfil y cerrar sesión

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

---

### **Vista Kanban**

El Kanban muestra todas las oportunidades organizadas por etapa.

**Etapas del Pipeline:**
```
[New] → [Contacted] → [Qualified] → [Proposal] → [Negotiation] → [Won/Lost]
  5%       10%           30%           50%            70%           100%/0%
```

**Usar el Kanban:**

1. **Ver oportunidades:**
   - Cada tarjeta = 1 oportunidad
   - Muestra: Cliente, Valor, Próxima tarea

2. **Mover oportunidades:**
   - Arrastrar tarjeta a otra columna
   - Sistema actualiza automáticamente
   - Crea registro en historial

3. **Filtrar:**
   - Por región, tipo de cliente, responsable
   - Buscar por nombre
   - Ocultar cerradas (Won/Lost)

4. **Abrir detalle:**
   - Click en tarjeta → Ver/Editar completo

**Ejemplo de tarjeta:**
```
┌────────────────────────┐
│ ACME Corp              │  ← Nombre del cliente
│ €50,000  [50%]         │  ← Valor y probabilidad
│ 📋 Enviar propuesta    │  ← Próxima tarea
│ 📅 20 Ene              │  ← Fecha límite
│ 🏷️ Madrid  Industria   │  ← Badges
└────────────────────────┘
```

---

## 👥 Gestión de Clientes

### **Listar Clientes**

```
Navegación: CRM → Clientes
```

**Vista principal:**
- Tabla con todos los clientes
- Búsqueda por nombre
- Filtros: Tipo, Región, Fuente, Responsable
- Botones: Ver detalle, Editar, Archivar

**Filtros:**
```
[Estado: Activos ▼]  [Tipo: Todos ▼]  [Región: Todas ▼]  [🔍 Buscar...]
```

---

### **Crear Nuevo Cliente**

**Pasos:**

```
1. Click "Nuevo Cliente" (botón verde superior derecha)

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
   - Responsable                 (Dropdown: usuarios del sistema)
   
   NOTAS:
   - Notas adicionales           (Texto libre)

3. Click "Crear"

✅ Toast verde: "Cliente creado correctamente"
```

**Consejos:**
- Solo el Nombre es obligatorio
- Website acepta formato simple: `www.ejemplo.com`
- Sistema añade https:// automáticamente

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
│  ...                                │
│                                     │
│  📞 INFORMACIÓN DE CONTACTO          │
│  Web: www.acme.com                  │
│  Tel: +34 912345678                 │
│  ...                                │
│                                     │
│  👥 CONTACTOS              [+ Añadir]│
│  ┌─────────────────────────────┐   │
│  │ Juan García                 │   │
│  │ 👤 Gerente                  │   │
│  │ ✉️ juan@acme.com [Principal]│   │
│  │ ☎️ +34 666777888            │   │
│  │                   [✏️] [🗑️] │   │
│  └─────────────────────────────┘   │
│                                     │
│  💼 OPORTUNIDADES        [Ver Kanban]│
│  (Lista de oportunidades activas)   │
│                                     │
└─────────────────────────────────────┘
```

**Acciones disponibles:**
- **Editar cliente**: Botón ✏️ superior
- **Archivar**: Botón 🗑️ superior
- **Añadir contacto**: Botón verde
- **Editar contacto**: Botón ✏️ de cada contacto
- **Eliminar contacto**: Botón 🗑️ de cada contacto
- **Ver en Kanban**: Navega y resalta oportunidades

---

### **Editar Cliente**

```
1. Abrir detalle del cliente
2. Click botón "Editar" (✏️ superior derecha)
3. Modal con formulario pre-rellenado
4. Modificar campos necesarios
5. Click "Guardar Cambios"

✅ Cambios guardados, detalle se recarga
```

**Notas:**
- Todos los campos editables
- Dropdowns mantienen selección actual
- Website se normaliza automáticamente

---

### **Archivar Cliente**

```
1. Abrir detalle del cliente
2. Click botón "Archivar" (🗑️ superior derecha)
3. Confirmar en el diálogo
4. Cliente se mueve a "Archivados"

⚠️ No se elimina físicamente, se puede recuperar
```

**Para ver archivados:**
```
En lista de clientes:
[Estado: Activos ▼] → Cambiar a "Archivados"
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
   - Nombre                      (Ejemplo: Juan)
   - Apellidos                   (Ejemplo: García López)
   - Rol                         (Dropdown: Gerente, Director...)
   
   EMAILS:                       [+ Añadir más]
   - [email@ejemplo.com]  [⭐]  [🗑️]
   
   TELÉFONOS:                    [+ Añadir más]
   - [+34 666777888]      [⭐]  [🗑️]

4. Marcar principal (⭐) en email/teléfono preferido
5. Click "Crear"

✅ Contacto añadido, aparece en lista
```

**Características:**
- **Múltiples emails**: Click "+ Añadir" para más
- **Múltiples teléfonos**: Click "+ Añadir" para más
- **Principal**: Solo uno puede ser principal por tipo
- **Eliminar canal**: Click 🗑️ para quitar email/teléfono

---

### **Editar Contacto**

```
1. En detalle del cliente
2. Lista de contactos → Click ✏️ del contacto
3. Modal con datos actuales
4. Modificar:
   - Cambiar nombre/apellidos/rol
   - Añadir/eliminar emails/teléfonos
   - Cambiar cuál es principal
5. Click "Guardar Cambios"

✅ Contacto actualizado
```

**Ejemplo de edición:**
```
Estado inicial:
- juan@acme.com [Principal]

Añadir segundo email:
- juan@acme.com
- juan@personal.com

Cambiar principal:
- juan@acme.com
- juan@personal.com [Principal]  ← Click ⭐
```

---

### **Eliminar Contacto**

```
1. En lista de contactos
2. Click 🗑️ del contacto
3. Confirmar: "¿Eliminar a Juan García?"
4. Click "Aceptar"

✅ Contacto eliminado (archivado, no borrado físicamente)
```

---

## 📥 Importar Datos desde Excel

Para cargar múltiples clientes y oportunidades de una vez.

### **Preparar el Archivo**

**Usar plantilla:** `IMPORT_NORMALIZADO_CRM.xlsx`

**Estructura:**
```
Sheet: DATA
Columnas:
- account_name        (Nombre del cliente)
- region              (Región: Madrid, Barcelona...)
- customer_type       (Tipo: Distribuidor, Instalador...)
- lead_source         (Fuente: Web, Referido...)
- opportunity_name    (Nombre de la oportunidad)
- expected_value      (Valor esperado en euros)
- stage               (Etapa: new, contacted...)
- contact_name        (Nombre del contacto principal)
- contact_email       (Email del contacto)
- contact_phone       (Teléfono del contacto)
- next_step           (Próxima acción/tarea)
- notes               (Notas adicionales)
```

**Ejemplo de fila:**
```
ACME Corp | Madrid | Distribuidor | Web | Proyecto Solar | 50000 | qualified | Juan García | juan@acme.com | +34666777888 | Enviar propuesta | Cliente interesado
```

---

### **Importar**

```
1. Dashboard → Botón "Importar" (o navegar a /import)
2. Click "Seleccionar archivo"
3. Elegir IMPORT_NORMALIZADO_CRM.xlsx
4. Sistema valida automáticamente
5. Ver reporte:
   - ✅ Filas válidas
   - ⚠️ Warnings (valores no en catálogo)
   - ❌ Errores (datos faltantes)
6. Click "Confirmar Importación"
7. Sistema crea:
   - Cuentas (clientes)
   - Oportunidades
   - Contactos principales
   - Tareas de próximo paso

✅ Importación completada
```

**Reporte ejemplo:**
```
📊 Resumen:
- 25 filas procesadas
- 20 cuentas creadas
- 25 oportunidades creadas
- 18 contactos añadidos
- 25 tareas generadas

⚠️ Warnings:
- Fila 5: Región "Valencia" no en catálogo
- Fila 12: Tipo "OEM" no en catálogo
→ Se guardaron en campos de texto libre
```

---

## 🎯 Flujo de Trabajo Típico

### **Escenario: Nuevo Lead**

```
1. CREAR CLIENTE
   Dashboard → Clientes → Nuevo Cliente
   - Nombre: "Nueva Empresa SL"
   - Región: Madrid
   - Tipo: Distribuidor
   - Fuente: Referido
   - Responsable: [Tu nombre]

2. AÑADIR CONTACTO
   Detalle cliente → Añadir contacto
   - Nombre: María
   - Apellidos: Fernández
   - Rol: Gerente
   - Email: maria@nuevaempresa.com [Principal]
   - Teléfono: +34 666123456

3. CREAR OPORTUNIDAD
   (Desde Dashboard → Kanban o gestión de oportunidades)
   - Cliente: Nueva Empresa SL
   - Nombre: "Proyecto 2026"
   - Valor: €30,000
   - Etapa: New

4. AÑADIR TAREA
   - Título: "Llamar para calificar"
   - Fecha: Mañana

5. SEGUIMIENTO
   - Kanban → Mover tarjeta según avance
   - New → Contacted → Qualified → ...
```

---

### **Escenario: Actualizar Oportunidad**

```
1. Dashboard → Kanban
2. Buscar oportunidad (filtros o búsqueda)
3. Arrastrar tarjeta a nueva etapa
   Ejemplo: "Contacted" → "Qualified"
4. Sistema actualiza:
   - Probabilidad (10% → 30%)
   - Pipeline ponderado
   - Historial de actividad
```

---

### **Escenario: Cerrar Venta (Won)**

```
1. Kanban → Oportunidad en "Negotiation"
2. Arrastrar a columna "Won"
3. Modal solicita:
   - Fecha de cierre
   - Valor final ganado
4. Confirmar
5. Sistema:
   - Marca como Ganada
   - Suma a "Cerrado Anual"
   - Crea actividad
   - Actualiza KPIs
```

---

## 🔍 Búsqueda y Filtros

### **Buscar Clientes**

```
En lista de clientes:
[🔍 Buscar...]  → Escribir nombre
Busca en: Nombre, Email, Teléfono, CIF
```

**Filtros combinables:**
```
[Estado: Activos]
[Tipo: Distribuidor]
[Región: Madrid]
[Fuente: Web]
[Responsable: Juan]

→ Muestra solo clientes que cumplan TODOS los filtros
```

---

### **Buscar en Kanban**

```
Barra de búsqueda superior:
[🔍 Buscar oportunidad...]

Filtros laterales:
☐ Ocultar cerradas (Won/Lost)
[Región: Todas ▼]
[Tipo: Todos ▼]
[Owner: Todos ▼]
☐ Tareas atrasadas
```

**Navegación directa:**
```
Desde detalle de cliente:
Botón "Ver en Kanban" →
Kanban se abre con oportunidades del cliente resaltadas en verde
```

---

## ⚙️ Configuración

*Requiere rol **admin***

### **Gestionar Catálogos**

Desde menú Config/Admin:

**Tipos de Cliente:**
```
Añadir nuevo: Distribuidor, Instalador, OEM, etc.
Activar/Desactivar existentes
```

**Regiones:**
```
17 CCAA de España pre-cargadas
Activar/Desactivar según necesidad
```

**Fuentes de Lead:**
```
Web, Referido, Evento, Frío, etc.
Personalizar según tus canales
```

---

### **Gestionar Usuarios**

```
1. Admin → Usuarios
2. Ver lista de usuarios
3. Acciones:
   - Crear usuario nuevo
   - Asignar rol (admin/sales/viewer)
   - Activar/Desactivar
   - Reset password
```

**Roles:**
- **admin**: Acceso total
- **sales**: CRM completo (sin gestión usuarios)
- **viewer**: Solo lectura

---

## 💡 Consejos y Mejores Prácticas

### **Organización**

✅ **DO:**
- Asignar responsable a cada cliente
- Mantener contactos actualizados con roles
- Marcar email/teléfono principal
- Usar filtros para encontrar rápido
- Revisar Kanban diariamente

❌ **DON'T:**
- Dejar clientes sin responsable
- Crear duplicados (buscar antes)
- Archivar sin revisar oportunidades abiertas

---

### **Pipeline Saludable**

**Balance recomendado:**
```
New:          10-20%  → Entrada constante
Contacted:    15-20%  → Calificación activa
Qualified:    20-25%  → Oportunidades reales
Proposal:     20-25%  → En negociación
Negotiation:  15-20%  → Próximas a cerrar
```

**Si ves:**
- Mucho en New → Falta calificación
- Mucho en Qualified → Falta acción
- Poco en Proposal → Pipeline débil

---

### **Seguimiento Efectivo**

**Frecuencia recomendada:**
- New → Contactar en 24h
- Contacted → Seguir en 2-3 días
- Qualified → Seguir semanalmente
- Proposal → Seguir cada 3-4 días
- Negotiation → Seguir diariamente

**Usar tareas:**
- Siempre con fecha límite
- Descripción clara de la acción
- Asignar responsable

---

## 🆘 Preguntas Frecuentes

### **¿Cómo cambio mi contraseña?**
```
1. Click en tu nombre (esquina superior derecha)
2. Perfil
3. Cambiar contraseña
4. Guardar
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
Actualmente no hay export automático.
Alternativa: Copiar desde lista o usar herramienta externa sobre crm.db
```

---

### **¿Puedo eliminar permanentemente un cliente?**
```
No desde la UI (es baja lógica).
Motivo: Auditoría y compliance.
Si necesario: Contactar administrador de sistema.
```

---

### **¿Los datos están respaldados?**
```
Configuración actual: SQLite local
Backup manual: Copiar crm.db regularmente

Futuro con PostgreSQL: Backups automáticos programados
```

---

## 📞 Soporte

**¿Necesitas ayuda?**

1. Consultar esta guía
2. Revisar CHANGELOG.md (historial de cambios)
3. Contactar a tu administrador de sistema
4. Reportar bug: Proporcionar pasos para reproducir

---

## 🎓 Recursos Adicionales

- **README.md**: Documentación técnica e instalación
- **CHANGELOG.md**: Historial de versiones
- **SPEC**: Especificación funcional completa

---

**Versión de la Guía:** v1.0.0  
**Última actualización:** 16 Enero 2026

¿Sugerencias para mejorar esta guía? Contacta al administrador.
