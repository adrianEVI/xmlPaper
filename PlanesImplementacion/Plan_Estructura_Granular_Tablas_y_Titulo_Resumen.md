# Plan de Solución: Titular General de Resumen y Expansión Granular de Tablas DOCX

Este plan aborda los 2 problemas finales identificados de conformidad estructural con el XML experto y el estándar SciELO SPS / JATS DTD 1.1.

---

## Problemas Identificados y Soluciones Propuestas

### 1. Inserción del Título General del Resumen Español (`<title>Resumen</title>`)
- **Problema:** El elemento `<abstract>` en español comenzaba directamente con las subsecciones (`<sec><title>Introducción:</title>...`), omitiendo el titular del bloque `<title>Resumen</title>` exigido por la especificación experta SPS.
- **Solución:**
  - En `main.py` -> `build_structured_abstract_xml` y en el paso de normalización (`apply_10_out_of_10_expert_fixes.py`), asegurar que el elemento `<abstract>` contenga como primer hijo directo el nodo `<title>Resumen</title>` (sin dos puntos).

### 2. Expansión Granular de Filas en Tablas Españolas (`docx_table_parser.py`)
- **Problema:** Las tablas en español estaban excesivamente condensadas (ej. Tabla 1 con solo 6 filas de 8 celdas conteniendo párrafos extensos unidos), mientras que el XML experto posee 66 filas independientes, separando cada indicador y actividad en su propia fila alineada.
- **Solución:**
  - Refactorear `build_jats_table_from_docx` en `docx_table_parser.py` para analizar el contenido multi-párrafo (`cell.paragraphs`) y saltos de línea de cada celda.
  - Expandir las celdas multi-línea en múltiples filas individuales `<tr>` alineadas a través de las columnas de la tabla. De esta forma, las tablas en español mantendrán la misma granularidad y fidelidad visual exacta al DOCX original y al XML experto.

---

## Proposed Changes

### Core Engine & Parser Updates

#### [MODIFY] [docx_table_parser.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/docx_table_parser.py)
- Refactorear la extracción de filas `tbl.rows`.
- Cuando una celda posea múltiples párrafos o líneas independientes (`splitlines`), expandir el bloque de celdas en $N$ filas `<tr>` asociadas, conservando celdas vacías de relleno `<td></td>` donde corresponda para alineación entre columnas.

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- Ajustar `build_structured_abstract_xml` para inyectar `<title>Resumen</title>` sin dos puntos como primer hijo directo de `<abstract>`.

#### [MODIFY] [apply_10_out_of_10_expert_fixes.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/apply_10_out_of_10_expert_fixes.py)
- Asegurar que todo `<abstract>` posea su nodo `<title>Resumen</title>` inicial.

---

## Verification Plan

### Automated Tests & Script Validation
1. Re-procesar el lote completo de archivos SANUS con `docx_table_parser.py` actualizado.
2. Ejecutar un script de verificación automatizado para confirmar:
   - Que `<abstract>` contenga como primer hijo `<title>Resumen</title>`.
   - Que la Tabla 1 de `566_ESP.xml` tenga una estructura granular de más de 50 filas `<tr>` (coincidiendo con la fidelidad del XML experto).

### Manual Verification
- Visualizar `566_ESP.xml` para constatar la alineación limpia de celdas en las tablas de enfermería.
