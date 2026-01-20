# 📘 MANUAL DE USUARIO - PARTE 2/3

[CONTINUACIÓN DESDE PARTE 1]

---

## 9. CONSEJOS Y MEJORES PRÁCTICAS

### 9.1 Gestión del Pipeline

**Mantén el Kanban actualizado:**
- Mueve tarjetas al menos 1 vez por semana
- Si no hay avance en 2 semanas → añade actividad explicando por qué
- Cierra oportunidades perdidas en cuanto lo sepas (no las dejes en "negotiation" 3 meses)

**Usa forecast close month:**
- Sé realista con las fechas
- Revisa y actualiza mensualmente
- Ayuda a proyectar ingresos

**Weighted value:**
- Deja que el sistema calcule automáticamente
- Solo usa override si tienes info privilegiada
- Ejemplo: "El cliente me dijo 95% seguro" → override a 0.95

**Conversión:**
- Objetivo típico: 20-30% (C/A)
- Si es < 15% → estás calificando mal (muchos "new" que no cierran)
- Si es > 40% → estás siendo muy conservador (añade más prospects)

### 9.2 Registro de Actividades

**Registra TODA interacción:**
- Llamada → activity tipo "call"
- Email importante → tipo "email"
- Reunión → tipo "meeting"
- Nota interna → tipo "note"

**Sé específico en el resumen:**
- ❌ Malo: "Hablé con el cliente"
- ✅ Bueno: "Llamada con Juan (Gerente). Confirma presupuesto OK. Espera aprobación directorio semana próxima. Siguiente paso: llamar 15/01"

**Timing:**
- Registra INMEDIATAMENTE después de la interacción
- No confíes en tu memoria
- 5 minutos ahora te ahorran 30 minutos después

### 9.3 Gestión de Tareas

**Crea tareas específicas:**
- ❌ Malo: "Seguimiento"
- ✅ Bueno: "Llamar a María para confirmar fecha de presentación"

**Due dates realistas:**
- Mejor 2 tareas cumplidas que 5 vencidas
- Si una task se vence, NO la borres → márcala como done y crea una nueva
- Las vencidas son métricas importantes

**Asignación:**
- Asigna a ti mismo o a un compañero específico
- No dejes tareas sin asignar (se pierden)

**Prioriza:**
- Rojo (vencidas) → urgente
- Amarillo (próximos 2 días) → importante
- Verde (próximos 10 días) → planificar

### 9.4 Importación Excel

**Pre-validación:**
- Revisa el Excel 2 veces antes de importar
- Usa dry-run SIEMPRE en primera importación
- Corrige warnings antes de importación real

**Incremental, no todo de golpe:**
- Primera vez: 10-20 filas para probar
- Si OK → importa el resto
- No importes 500 filas sin probar

**Limpieza de datos:**
- Elimina filas duplicadas en Excel
- Unifica nombres: "ACME Corp" = "ACME CORP" = "acme corp"
- Emails en minúsculas

**Backup antes de importar:**
- Run BACKUP_DB.bat antes de importaciones grandes
- Si algo sale mal, puedes restaurar

### 9.5 Catálogos de Configuración

**Planifica antes de crear:**
- Define 5-10 provincias relevantes (no 50)
- Define 3-5 tipos de cliente (Empresa, Pyme, Autónomo)
- Define 5-8 canales comerciales

**Nomenclatura consistente:**
- ❌ "Linkedin", "LinkedIn", "LINKEDIN"
- ✅ "LinkedIn" (siempre igual)

**Revisa uso antes de desactivar:**
- Si el sistema te avisa "en uso por X registros"
- Piensa si realmente quieres desactivarlo
- Considera migrar primero

**Stages: NO cambiar a la ligera:**
- Cambiar outcome (open/won/lost) afecta cálculos
- Cambiar sort_order reordena kanban
- Si dudas, pregunta a admin

### 9.6 Trabajo en Equipo

**Comunicación:**
- Usa activities tipo "note" para comunicar internamente
- Ejemplo: "Juan: confirmé con cliente que acepta propuesta. Puedes preparar contrato"

**Ownership claro:**
- Cada oportunidad debe tener un owner claro
- Si cambias de owner → actualiza el campo
- Evita opps "huérfanas"

**Reuniones de pipeline:**
- Revisa kanban en reunión semanal de equipo
- Cada uno explica movimientos de sus tarjetas
- Identifica bloqueos y ayuda mutua

**Métricas compartidas:**
- Dashboard refleja el trabajo de TODO el equipo
- Conversión C/A es métrica colectiva
- Celebra wins juntos

---

## 10. SOLUCIÓN DE PROBLEMAS

### 10.1 Problemas Comunes

**"No puedo hacer login"**

Posibles causas:
1. Email o password incorrecto
   - Solución: Verifica mayúsculas/minúsculas
   - Solución: Pide reset de password al admin

2. Usuario desactivado
   - Solución: Contacta al admin

3. Servidor CRM no está corriendo
   - Solución: Verifica que START_CRM.bat está ejecutándose
   - Check: http://localhost:8000/health debería responder

**"El Kanban no carga / tarda mucho"**

Posibles causas:
1. Muchas oportunidades abiertas (>500)
   - Solución: Cierra opps perdidas antiguas
   - Solución: Usa filtros para reducir visualización

2. Navegador lento
   - Solución: Cierra otros tabs
   - Solución: Usa Chrome o Edge actualizado

3. Base de datos grande
   - Solución: Admin debe hacer BACKUP y limpiar datos antiguos

**"No recibo emails diarios"**

Posibles causas:
1. EMAIL_ENABLED=false
   - Solución: Admin debe configurar en .env

2. SMTP mal configurado
   - Solución: Admin revisa logs/error.log

3. No tienes tareas
   - Solución: Crea una task de prueba

4. Email en spam
   - Solución: Añade email CRM a contactos seguros

**"Importación Excel falla"**

Errores comunes:
1. "account_name missing"
   - Solución: Completa nombres en todas las filas

2. "expected_value_eur invalid"
   - Solución: Usa números, no texto

3. "stage_key invalid"
   - Solución: Usa: new, contacted, qualified, proposal, negotiation

4. Archivo no se sube
   - Solución: Verifica que es .xlsx (no .xls ni .csv)
   - Solución: Tamaño < 10MB

**"Drag & Drop no funciona"**

Posibles causas:
1. Navegador viejo
   - Solución: Actualiza a Chrome/Edge/Firefox últimas versiones

2. Tarjeta ya cerrada (won/lost)
   - Solución: No se pueden mover cerradas, usa botones Won/Lost

3. JavaScript desactivado
   - Solución: Habilita JavaScript en navegador

**"Gráficos no se ven"**

Posibles causas:
1. Bloqueador de ads/scripts
   - Solución: Desactiva para localhost

2. Sin datos
   - Solución: Verifica que hay oportunidades en BD

3. Filtros muy restrictivos
   - Solución: Reset filtros

### 10.2 Mensajes de Error

**HTTP 400 - Bad Request**
- Datos inválidos en formulario
- Solución: Revisa campos requeridos

**HTTP 401 - Unauthorized**
- Sesión expirada
- Solución: Vuelve a hacer login

**HTTP 403 - Forbidden**
- No tienes permisos (viewer intentando editar)
- Solución: Contacta admin para cambiar rol

**HTTP 404 - Not Found**
- Recurso no existe
- Solución: Refresca página o vuelve al dashboard

**HTTP 409 - Conflict (HOTFIX 7.1)**
- Elemento en uso
- Ejemplo: "Esta provincia está en uso por 42 cuenta(s) activa(s)"
- Solución: Fuerza operación o cancela

**HTTP 422 - Validation Error**
- Campos con formato incorrecto
- Ejemplo: email sin @, número negativo
- Solución: Corrige formato

**HTTP 500 - Internal Server Error**
- Error del servidor
- Solución: Contacta admin, revisa logs

### 10.3 Performance

**"El CRM va lento"**

Optimizaciones:
1. Cierra opps perdidas > 6 meses
2. Archiva cuentas inactivas
3. Limpia tasks completadas antiguas (admin)
4. Usa filtros en dashboard/kanban

**"El navegador se congela"**

Solución inmediata:
1. Cierra tab
2. Abre nueva tab
3. Vuelve a http://localhost:8000
4. Si persiste → reinicia navegador

**Prevención:**
- No abras 10 drawers simultáneos
- No hagas importaciones de 1000 filas sin dry-run
- Cierra sesión al final del día

### 10.4 Contactar Soporte

**Antes de contactar:**
1. ✅ Verifica que START_CRM.bat está corriendo
2. ✅ Prueba en otro navegador
3. ✅ Revisa sección "Problemas Comunes" arriba

**Información a proporcionar:**
- Descripción del problema
- Pasos para reproducir
- Mensaje de error (screenshot)
- Rol de usuario (admin/sales/viewer)
- Navegador y versión
- Timestamp (fecha/hora del error)

**Canales de soporte:**
- Email: soporte@tuempresa.com
- Interno: Ticket en sistema interno
- Admin local: [Nombre admin interno]

**Logs para admin:**
- logs/app.log → registro general
- logs/error.log → errores críticos
- Proporciona últimas 50 líneas al reportar

---

## 11. SOPORTE

### 11.1 Recursos Disponibles

**Documentación:**
- Manual de Usuario (este documento)
- Guía Admin (para administradores)
- .env.example (configuración)

**Videos/Tutoriales:**
- (Pendiente: grabar screencasts de flujos principales)

**FAQ Online:**
- (Pendiente: publicar en wiki interna)

### 11.2 Actualizaciones

**Cómo saber versión actual:**
- Navbar → esquina inferior derecha → "v0.7.0"
- O: http://localhost:8000/health → campo "version"

**Changelog:**
- http://localhost:8000/versions (próximamente)
- Listado de cambios por versión

**Frecuencia de actualizaciones:**
- Minor releases: cada 1-2 meses
- Hotfixes: según necesidad
- Major releases: cada 6 meses

**Notificaciones:**
- Admin comunicará actualizaciones importantes
- Email a todos los usuarios
- Ventana de mantenimiento programada

### 11.3 Feedback y Mejoras

**Tu opinión importa:**
- Usa formulario de feedback (próximamente)
- Reporta bugs inmediatamente
- Sugiere mejoras

**Priorización:**
- Bugs críticos: fix en 24-48h
- Mejoras de UX: roadmap mensual
- Features nuevas: roadmap trimestral

**Roadmap público:**
- Próximas features en consideración:
  - Calendario integrado
  - Notificaciones push
  - App móvil
  - Reportes avanzados
  - Integración con ERP

### 11.4 Buenas Prácticas de Comunicación

**Reportar bugs:**
- ✅ "Al arrastrar opp de New a Contacted, se queda cargando y no se mueve"
- ❌ "No funciona"

**Sugerir mejoras:**
- ✅ "Sería útil poder filtrar Kanban por forecast month para ver solo opps de Q1"
- ❌ "El kanban debería tener más filtros"

**Pedir ayuda:**
- ✅ "Intenté importar Excel pero da error 'account_name missing' en fila 15. Adjunto archivo"
- ❌ "El Excel no funciona"

---

## APÉNDICE A: Glosario

**Account (Cuenta):**
Empresa u organización cliente/prospecto.

**Activity (Actividad):**
Registro de interacción con cliente (llamada, email, reunión, etc).

**Close Outcome:**
Estado final de una oportunidad: open (abierta), won (ganada), lost (perdida).

**Contact (Contacto):**
Persona física asociada a una cuenta.

**CRM:**
Customer Relationship Management - Sistema de Gestión de Relaciones con Clientes.

**Drag & Drop:**
Arrastrar y soltar (mover tarjetas en kanban con ratón).

**Drawer:**
Panel lateral que se abre al click en tarjeta de kanban.

**Dry Run:**
Importación de prueba sin guardar datos reales.

**Expected Value:**
Valor esperado de una oportunidad (EUR).

**Forecast Close Month:**
Mes estimado de cierre (YYYY-MM).

**KPI:**
Key Performance Indicator - Indicador Clave de Rendimiento.

**Lead Source:**
Canal de origen del cliente (LinkedIn, Web, etc).

**Opportunity (Oportunidad):**
Posibilidad concreta de venta.

**Owner:**
Responsable comercial de una cuenta u oportunidad.

**Pacing:**
Ritmo de avance hacia objetivo anual.

**Pipeline:**
Conjunto de oportunidades abiertas (embudo de ventas).

**Probability:**
Probabilidad de cierre (0-100%).

**Stage:**
Etapa de una oportunidad (new, contacted, qualified, proposal, negotiation, won, lost).

**Task (Tarea):**
Acción específica a realizar, con due date.

**Upsert:**
Update or Insert - Actualizar si existe, crear si no existe.

**Weighted Value:**
Valor ponderado por probabilidad (expected_value * probability).

**Won:**
Oportunidad ganada/cerrada exitosamente.

**Lost:**
Oportunidad perdida/cerrada sin éxito.

---

## APÉNDICE B: Atajos de Teclado

**Generales:**
- `Ctrl + S` → Guardar (en formularios con soporte)
- `Esc` → Cerrar modal/drawer
- `Enter` → Submit formulario (si tiene un solo input)

**Navegación:**
- `Alt + 1` → Tab Overview (próximamente)
- `Alt + 2` → Tab Kanban (próximamente)
- `Alt + 3` → Tab Mis Tareas (próximamente)

**Kanban:**
- Click → Abrir drawer
- `Shift + Click` → Seleccionar múltiples (próximamente)
- `Ctrl + N` → Nueva oportunidad (próximamente)

---

## APÉNDICE C: Límites Técnicos

**Recomendaciones:**
- Oportunidades abiertas: < 500 (óptimo: 200-300)
- Tareas abiertas por usuario: < 100
- Actividades por oportunidad: ilimitado (el sistema es eficiente)
- Contactos por cuenta: ilimitado
- Import Excel: < 1000 filas por archivo
- Usuarios simultáneos: 3 (actual), escalable a 50+ con PostgreSQL

**Tamaños de archivo:**
- Import Excel: < 10MB
- Base de datos SQLite: < 1GB (recomendar migración a PostgreSQL)

**Retención de datos:**
- Audit log: indefinido
- Logs técnicos: 30 días (rotación automática)
- Backups: 30 backups (configurable)

---

## APÉNDICE D: Checklist Diario

**🌅 Mañana (08:00-09:00)**
- [ ] Revisar email CRM (resumen diario)
- [ ] Abrir tab "Mis Tareas"
- [ ] Priorizar: vencidas (rojo) primero
- [ ] Revisar próximas 2 días (amarillo)
- [ ] Planificar 2-3 acciones del día

**🏢 Durante el día**
- [ ] Registrar actividades inmediatamente
- [ ] Crear tareas de seguimiento después de reuniones
- [ ] Mover tarjetas en kanban según avance
- [ ] Responder a automatizaciones (tasks generadas por sistema)

**🌆 Tarde (17:00-18:00)**
- [ ] Cerrar oportunidades won/lost del día
- [ ] Marcar tareas completadas
- [ ] Revisar dashboard (KPIs actualizados)
- [ ] Crear tareas para mañana si necesario

**📅 Semanal (Viernes)**
- [ ] Reunión de pipeline con equipo
- [ ] Revisar forecast close month (actualizar si necesario)
- [ ] Archivar opps perdidas antiguas
- [ ] Limpiar tasks obsoletas

**📅 Mensual (Fin de mes)**
- [ ] Analizar conversión C/A
- [ ] Revisar pacing vs objetivo
- [ ] Identificar tendencias en gráficos
- [ ] Feedback a admin sobre mejoras

---

## APÉNDICE E: Plantilla de Actividad

**Estructura recomendada:**

```
Tipo: [call/email/meeting/note]

Resumen:
[Descripción breve pero específica]

Participantes:
- [Nombre] ([Cargo]) - [Empresa]

Temas tratados:
- [Punto 1]
- [Punto 2]

Acuerdos/Decisiones:
- [Decisión 1]
- [Decisión 2]

Siguiente paso:
[Acción concreta + responsable + fecha]

Observaciones:
[Notas adicionales]
```

**Ejemplo:**

```
Tipo: meeting

Resumen:
Reunión de seguimiento propuesta servicio consultorÃ­a con ACME Corp

Participantes:
- Juan Pérez (Gerente Compras) - ACME Corp
- María López (CFO) - ACME Corp

Temas tratados:
- Revisión de propuesta económica: 50.000 EUR confirmado
- Alcance de servicios: OK
- Timing: preferencia inicio 1 marzo

Acuerdos/Decisiones:
- ACME presenta propuesta a directorio semana 20/01
- Confirmación: 25/01

Siguiente paso:
Llamar a Juan el 26/01 para conocer decisión final

Observaciones:
María mostró preocupación por timing. Confirmé flexibilidad en fecha inicio.
```

---

**FIN DEL MANUAL DE USUARIO - PARTE 2/3**

[CONTINÚA EN PARTE 3 CON GUÍA ADMIN...]
