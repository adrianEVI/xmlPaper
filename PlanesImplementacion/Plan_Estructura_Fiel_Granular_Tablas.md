# Plan de Solución: Algoritmo de Extracción Granular de Tablas DOCX (Coincidencia 100% con XML Experto)

Este plan aborda la solicitud del usuario para adaptar la extracción del contenido de las tablas en `docx_table_parser.py`, logrando que las celdas extensas (como el Diagnóstico NANDA y las Actividades NIC) se segmenten y distribuyan en múltiples filas `<tr>` alineadas, coincidiendo exactamente con la estructura de 66 filas del XML experto para la Tabla 1 de 566.

---

## Problema Detectado y Solución Propuesta

### Segmentación Fiel de Celdas Multi-Línea y Alineación Fila por Fila
- **Estado Actual:** El parsedor tomaba el párrafo completo del Diagnóstico NANDA como un único bloque en la primera fila, dejando las filas subsecuentes con celdas vacías `<td/>`.
- **Estructura Experta:** El XML experto segmenta el Diagnóstico NANDA en 7 líneas (~35-45 caracteres por línea en rupturas naturales `r/c`, `m/p`, comas y puntos) para alinearlo horizontalmente con los elementos NOC de la segunda columna (`421. Severidad del shock`, `Dominio: 2...`, `Clase: E...`, `Indicadores:`, `042101...`, `042102...`, etc.). Además, las actividades NIC extensas (>100 caracteres) se dividen en líneas de ~110 caracteres.
- **Solución Propuesta:**
  - Implementar un **algoritmo de segmentación inteligente** en `docx_table_parser.py`:
    1. Detectar si una celda contiene un texto continuo extenso mientras la celda opuesta contiene múltiples párrafos o sub-elementos.
    2. Segmentar el texto continuo en $K$ fragmentos utilizando puntos de ruptura semánticos naturales (`r/c`, `m/p`, comas `,`, puntos `.`).
    3. Para párrafos de actividades NIC que excedan los 110 caracteres, aplicar segmentación suave por palabras (`word-wrapping` a 110 caracteres).
    4. Ensamblar la matriz de filas `<tr>` alineando los fragmentos fila por fila.

---

## Proposed Changes

### Core Engine & Parser Updates

#### [MODIFY] [docx_table_parser.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/docx_table_parser.py)
- Incorporar las funciones de división semántica `split_text_into_n_chunks` y `split_long_paragraph` dentro del bucle de extracción de `tbl.rows`.
- Aplicar la reestructuración a todas las tablas del lote de manuscritos SANUS.

---

## Verification Plan

### Automated Tests & Script Validation
1. Re-procesar los 18 archivos XML del directorio `Articulos/SANUS/SANUSxmlNEW`.
2. Ejecutar un script de verificación automatizado para confirmar:
   - Que la Tabla 1 de `566_ESP.xml` tenga **exactamente 66 filas `<tr>`**.
   - Que las celdas de la Tabla 1 coincidan línea por línea con las muestras del XML experto (`00421. Volumen de líquidos inadecuado r/c`, `Dificultad para obtener líquidos, ingreso`, etc.).

### Manual Verification
- Visualizar la estructura de `566_ESP.xml` para constatar la alineación perfecta NANDA/NOC/NIC.
