"""
Verificar que dashboard.js se instaló correctamente
"""
import os

print("="*70)
print("VERIFICACIÓN DE ARCHIVOS")
print("="*70)

# 1. Verificar que el archivo existe
js_path = "app/static/js/dashboard.js"
html_path = "app/templates/dashboard.html"

print("\n1. VERIFICAR EXISTENCIA:")
if os.path.exists(js_path):
    size = os.path.getsize(js_path)
    print(f"   ✅ {js_path} existe")
    print(f"   Tamaño: {size:,} bytes")
    
    # Verificar líneas
    with open(js_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"   Líneas: {len(lines)}")
    
    # Buscar loadKanbanData
    content = ''.join(lines)
    if 'loadKanbanData' in content:
        print(f"   ✅ Contiene 'loadKanbanData'")
        
        # Contar ocurrencias
        count = content.count('loadKanbanData')
        print(f"   Ocurrencias de 'loadKanbanData': {count}")
        
        # Buscar la definición
        if 'async function loadKanbanData()' in content or 'function loadKanbanData()' in content:
            print(f"   ✅ Definición de función encontrada")
        else:
            print(f"   ❌ NO se encontró la definición de la función")
    else:
        print(f"   ❌ NO contiene 'loadKanbanData'")
        print(f"   ⚠️ El archivo NO se copió correctamente")
else:
    print(f"   ❌ {js_path} NO existe")

print("\n2. VERIFICAR HTML:")
if os.path.exists(html_path):
    size = os.path.getsize(html_path)
    print(f"   ✅ {html_path} existe")
    print(f"   Tamaño: {size:,} bytes")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"   Líneas: {len(lines)}")
    
    # Buscar estilos del kanban
    content = ''.join(lines)
    if '.kanban-container' in content:
        print(f"   ✅ Contiene estilos de Kanban")
    else:
        print(f"   ❌ NO contiene estilos de Kanban")
else:
    print(f"   ❌ {html_path} NO existe")

print("\n3. TAMAÑOS ESPERADOS:")
print(f"   dashboard.js debería tener ~1290 líneas")
print(f"   dashboard.html debería tener ~887 líneas")

print("\n" + "="*70)
print("DIAGNÓSTICO:")

# Diagnóstico automático
if os.path.exists(js_path):
    with open(js_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content = ''.join(lines)
    
    if len(lines) < 1200:
        print("❌ El archivo dashboard.js es DEMASIADO CORTO")
        print(f"   Tiene {len(lines)} líneas, debería tener ~1290")
        print("   SOLUCIÓN: Copia de nuevo el archivo dashboard.js descargado")
    elif 'loadKanbanData' not in content:
        print("❌ El archivo NO contiene el código del Kanban")
        print("   SOLUCIÓN: Copia de nuevo el archivo dashboard.js descargado")
    else:
        print("✅ El archivo parece correcto")
        print("   PROBLEMA: Caché del navegador")
        print("   SOLUCIÓN: Presiona Ctrl+Shift+R para recargar sin caché")
else:
    print("❌ El archivo dashboard.js NO está en la ubicación correcta")
    print("   SOLUCIÓN: Copia dashboard.js a app/static/js/dashboard.js")

print("="*70)
