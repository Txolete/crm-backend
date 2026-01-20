/*
  Lightweight onboarding for the CRM dashboard:
  - Help: loads USER_GUIDE.md and renders it with marked.js.
  - Guided tour: overlay + bubble with next/back, highlights DOM elements.
*/

(function () {
  // ---------------- Help (Markdown) ----------------
  const GUIDE_URL = '/static/docs/USER_GUIDE.md';

  async function loadGuide() {
    const container = document.getElementById('help-guide');
    if (!container) return;

    container.innerHTML = '<div class="text-muted">Cargando guía...</div>';

    try {
      const res = await fetch(GUIDE_URL, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const md = await res.text();

      if (window.marked) {
        container.innerHTML = window.marked.parse(md);
      } else {
        // Fallback: show raw if marked fails to load
        container.textContent = md;
      }

      // Make headings a bit more compact in the offcanvas
      container.querySelectorAll('h1').forEach(h => h.classList.add('h4'));
      container.querySelectorAll('h2').forEach(h => h.classList.add('h5'));
      container.querySelectorAll('h3').forEach(h => h.classList.add('h6'));

      // Ensure links open in new tab
      container.querySelectorAll('a[href]').forEach(a => {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener');
      });

    } catch (e) {
      container.innerHTML = '<div class="text-danger">No se pudo cargar la guía. Puedes abrirla en nueva pestaña.</div>';
      console.error('Help guide load failed:', e);
    }
  }

  window.reloadHelpGuide = loadGuide;

  document.addEventListener('shown.bs.offcanvas', (evt) => {
    if (evt.target && evt.target.id === 'helpOffcanvas') {
      loadGuide();
    }
  });

  // ---------------- Guided Tour ----------------
  const overlay = () => document.getElementById('tour-overlay');
  const bubble = () => document.getElementById('tour-bubble');
  const titleEl = () => document.getElementById('tour-title');
  const textEl = () => document.getElementById('tour-text');
  const btnPrev = () => document.getElementById('tour-prev');
  const btnNext = () => document.getElementById('tour-next');
  const btnSkip = () => document.getElementById('tour-skip');

  let tourSteps = [];
  let tourIdx = 0;
  let highlightedEl = null;

  function getEl(selector) {
    try {
      return document.querySelector(selector);
    } catch {
      return null;
    }
  }

  function clearHighlight() {
    if (highlightedEl) {
      highlightedEl.classList.remove('tour-highlight');
      highlightedEl = null;
    }
  }

  function positionBubbleNear(el) {
    const b = bubble();
    if (!b || !el) return;

    const rect = el.getBoundingClientRect();
    const margin = 12;

    // Try right, else left, else bottom
    const bW = Math.min(360, window.innerWidth - 20);
    b.style.maxWidth = bW + 'px';

    let top = Math.max(10, rect.top);
    let left = rect.right + margin;

    if (left + bW > window.innerWidth - 10) {
      left = Math.max(10, rect.left - bW - margin);
    }

    if (left < 10) {
      left = 10;
      top = Math.min(window.innerHeight - 140, rect.bottom + margin);
    }

    // Clamp
    top = Math.min(window.innerHeight - 160, Math.max(10, top));
    left = Math.min(window.innerWidth - bW - 10, Math.max(10, left));

    b.style.top = top + 'px';
    b.style.left = left + 'px';
  }

  function renderStep() {
    const step = tourSteps[tourIdx];
    if (!step) return;

    clearHighlight();

    const el = getEl(step.selector);
    if (!el) {
      // Skip missing element
      tourIdx = Math.min(tourIdx + 1, tourSteps.length - 1);
      if (tourSteps[tourIdx]) return renderStep();
      return endTour();
    }

    // Ensure visible
    el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });

    // Highlight
    el.classList.add('tour-highlight');
    highlightedEl = el;

    // Text
    titleEl().textContent = `${step.title} (${tourIdx + 1}/${tourSteps.length})`;
    textEl().textContent = step.text;

    // Buttons
    btnPrev().disabled = tourIdx === 0;
    btnNext().textContent = tourIdx === tourSteps.length - 1 ? 'Terminar' : 'Siguiente';

    // Position bubble
    setTimeout(() => positionBubbleNear(el), 250);
  }

  function endTour() {
    clearHighlight();
    overlay().style.display = 'none';
    bubble().style.display = 'none';
    tourIdx = 0;
  }

  function startTour() {
    tourSteps = [
      {
        selector: '.navbar-brand',
        title: 'Bienvenido al CRM',
        text: 'Este es tu panel principal. Desde aquí podrás gestionar todo tu pipeline comercial: clientes, oportunidades y tareas.'
      },
      {
        selector: 'a.nav-link[href="/accounts/page"]',
        title: 'Gestión de Clientes',
        text: 'Accede al listado completo de clientes. Puedes crear, editar, buscar y filtrar todas tus cuentas.'
      },
      {
        selector: '#btn-import-excel',
        title: 'Importar Excel',
        text: 'Importa múltiples clientes y oportunidades desde un archivo Excel. El sistema valida los datos antes de guardar.'
      },
      {
        selector: '#overview-tab',
        title: 'Vista Overview',
        text: 'Aquí ves los KPIs principales: Pipeline Total, Ponderado, Cerrado Anual y el pacing mensual teórico.'
      },
      {
        selector: '#kanban-tab',
        title: 'Vista Kanban',
        text: 'Cambia a esta pestaña para ver y gestionar tu pipeline por etapas. Arrastra oportunidades entre columnas y crea nuevas desde aquí.'
      },
      {
        selector: '#tasks-tab',
        title: 'Mis Tareas',
        text: 'Cambia a esta pestaña para revisar tus tareas pendientes, atrasadas y próximas.'
      },
      {
        selector: '.navbar .dropdown-toggle',
        title: 'Menú de Usuario',
        text: 'Despliega este menú para acceder a Configuración, Importar Excel, Editar Objetivos o cerrar sesión.'
      },
      {
        selector: '#btn-help',
        title: 'Ayuda y Soporte',
        text: 'Consulta el manual de usuario completo o vuelve a ver este tour cuando lo necesites.'
      }
    ];

    tourIdx = 0;
    overlay().style.display = 'block';
    bubble().style.display = 'block';
    renderStep();
  }

  window.startGuidedTour = startTour;

  // Tour específico para la página de Clientes
  window.startAccountsTour = function() {
    tourSteps = [
      {
        selector: '.navbar-brand',
        title: 'Gestión de Clientes',
        text: 'Esta es tu pantalla de gestión de clientes. Aquí puedes ver, crear, editar y buscar todas tus cuentas.'
      },
      {
        selector: '#btn-new-account',
        title: 'Crear Cliente',
        text: 'Haz clic aquí para crear un nuevo cliente. El formulario incluye todos los datos necesarios: nombre, contactos, región, tipo, etc.'
      },
      {
        selector: '#filter-search',
        title: 'Búsqueda Rápida',
        text: 'Busca clientes por nombre. La búsqueda se activa en tiempo real mientras escribes.'
      },
      {
        selector: '#filter-status',
        title: 'Filtro de Estado',
        text: 'Filtra por estado: activos o archivados. Por defecto solo se muestran los clientes activos.'
      },
      {
        selector: '#filter-customer-type',
        title: 'Filtro de Tipo',
        text: 'Filtra clientes por tipo (ej: Directo, Distribuidor, Partner). Los tipos se configuran en el módulo de Config.'
      },
      {
        selector: '#filter-region',
        title: 'Filtro de Provincia',
        text: 'Filtra por provincia o región. Útil para organizar tu cartera por zonas geográficas.'
      },
      {
        selector: '#accounts-table-body',
        title: 'Listado de Clientes',
        text: 'Aquí aparecen todos tus clientes. Haz clic en cualquier fila para ver el detalle completo, contactos y opciones de edición.'
      },
      {
        selector: '.navbar .nav-link[href="/dashboard"]',
        title: 'Volver al Dashboard',
        text: 'Regresa al dashboard principal para ver tus KPIs y el pipeline de oportunidades.'
      }
    ];

    tourIdx = 0;
    overlay().style.display = 'block';
    bubble().style.display = 'block';
    renderStep();
  };

  // Tour específico para la página de Configuración
  window.startConfigTour = function() {
    tourSteps = [
      {
        selector: '.main-container h2',
        title: 'Configuración',
        text: 'Aquí gestionas todos los catálogos maestros del CRM: provincias, tipos de cliente, fuentes, roles y más.'
      },
      {
        selector: '.nav-pills .nav-link[data-entity="regions"]',
        title: 'Provincias',
        text: 'Gestiona el catálogo de provincias o regiones. Puedes activar/desactivar las que uses y ordenarlas.'
      },
      {
        selector: '.nav-pills .nav-link[data-entity="customer-types"]',
        title: 'Tipos de Cliente',
        text: 'Define los tipos de cliente: Directo, Distribuidor, Partner, etc. Estos aparecen en formularios y filtros.'
      },
      {
        selector: '.nav-pills .nav-link[data-entity="lead-sources"]',
        title: 'Fuentes de Lead',
        text: 'Configura de dónde vienen tus leads: Web, Referido, Feria, Publicidad, etc.'
      },
      {
        selector: '.nav-pills .nav-link[data-entity="contact-roles"]',
        title: 'Roles de Contacto',
        text: 'Define los roles de tus contactos: CEO, CTO, Compras, Técnico, etc.'
      },
      {
        selector: '.nav-pills .nav-link[data-entity="stages"]',
        title: 'Stages',
        text: 'Visualiza los stages del pipeline. Cada uno tiene una probabilidad asociada para el cálculo de pipeline ponderado.'
      },
      {
        selector: 'a.nav-link[href="/dashboard"]',
        title: 'Volver al Dashboard',
        text: 'Una vez configurados los catálogos, regresa al dashboard para empezar a trabajar con tus oportunidades.'
      }
    ];

    tourIdx = 0;
    overlay().style.display = 'block';
    bubble().style.display = 'block';
    renderStep();
  };

  document.addEventListener('click', (e) => {
    if (!bubble() || bubble().style.display === 'none') return;

    if (e.target && e.target.id === 'tour-prev') {
      if (tourIdx > 0) {
        tourIdx -= 1;
        renderStep();
      }
    }
    if (e.target && e.target.id === 'tour-next') {
      if (tourIdx >= tourSteps.length - 1) return endTour();
      tourIdx += 1;
      renderStep();
    }
    if (e.target && e.target.id === 'tour-skip') {
      endTour();
    }
  });

  // Also close tour on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (bubble() && bubble().style.display !== 'none') endTour();
    }
  });
})();
