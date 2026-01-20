# ❌ ERROR: "No module named 'sqlalchemy'"

## 🔍 CAUSA DEL PROBLEMA

Este error significa que **las dependencias de Python NO están instaladas**.

El script `SETUP.bat` asume que ya tienes todo instalado, pero es la primera vez que usas el CRM.

---

## ✅ SOLUCIÓN (2 MINUTOS)

### **Opción 1: Usar INSTALL.bat (RECOMENDADO)**

En lugar de `SETUP.bat`, ejecuta:

```bash
# Doble clic en:
INSTALL.bat
```

Este script hace TODO automáticamente:
1. ✅ Crea el entorno virtual
2. ✅ Instala las dependencias
3. ✅ Ejecuta el setup

**Espera 1-2 minutos** mientras instala las dependencias.

---

### **Opción 2: Manual (Si INSTALL.bat falla)**

Si `INSTALL.bat` también falla, hazlo manualmente:

```bash
# 1. Abre CMD en la carpeta del CRM

# 2. Crea entorno virtual
python -m venv venv

# 3. Activa entorno virtual
venv\Scripts\activate.bat

# 4. Instala dependencias
pip install -r requirements.txt

# 5. Ejecuta setup
python setup.py

# 6. Arranca servidor
START_CRM.bat
```

---

## 🎯 QUÉ EJECUTAR

### **Primera vez:**
```
INSTALL.bat  ← Este instala TODO
```

### **Después:**
```
START_CRM.bat  ← Solo arrancar servidor
```

---

## ⚠️ NO EJECUTES SETUP.bat DIRECTAMENTE

`SETUP.bat` es para usuarios avanzados que ya tienen el entorno configurado.

Para la primera instalación, siempre usa: **`INSTALL.bat`**

---

## 📝 RESUMEN DEL ERROR

```
Error original:
  ModuleNotFoundError: No module named 'sqlalchemy'

Causa:
  Falta instalar las dependencias de Python

Solución:
  Ejecutar INSTALL.bat en lugar de SETUP.bat
```

---

## ✅ VERIFICACIÓN

Después de ejecutar `INSTALL.bat`, deberías ver:

```
✅ SETUP COMPLETADO
   • 1 Usuario admin
   • 7 Stages con probabilidades
   • 52 Provincias españolas
   ...

🔐 Credenciales:
   Email:    admin@example.com
   Password: admin123456

Siguiente paso: Ejecuta START_CRM.bat
```

Si ves esto, ¡está todo correcto! ✅

---

## 🆘 SI INSTALL.bat TAMBIÉN FALLA

Si `INSTALL.bat` falla con otro error, envíame:

1. La **captura completa** de la ventana de CMD
2. El **mensaje de error exacto**
3. Tu **versión de Python** (ejecuta: `python --version`)

---

**TL;DR: Ejecuta `INSTALL.bat`, no `SETUP.bat`** 🚀
