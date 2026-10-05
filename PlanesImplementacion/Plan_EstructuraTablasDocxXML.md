# Plan de Implementación: Preservación de Estructura y Diseño de Tablas (Word a JATS XML)

Este plan aborda la solución raíz para que las tablas en los archivos JATS XML (`.xml`) mantengan la estructura exacta de celdas combinadas (`colspan`, `rowspan`), alineaciones y formato visual presente en los documentos Word (`560_ESP.docx` y similares).

## Causa Raíz Identificada

El módulo [`docx_table_parser.py`](file:///Users/adrianevi/xmlPage/xmlPaper/docx_table_parser.py) extrae el contenido de las tablas utilizando `row.cells` de `python-docx` de forma plana:

1. **Pérdida de `colspan`**: `python-docx` repite el mismo objeto celda para cada columna abarcada por un `w:gridSpan`. El parser actual itera sobre `row.cells` y crea un `<td>` independiente por cada entrada, lo que provoca duplicación de textos (`<td>Texto</td><td>Texto</td>`) en lugar de generar un `<td colspan="N">`.
2. **Pérdida de `rowspan`**: El parser no analiza las etiquetas OpenXML `w:vMerge` (`restart` / `continue`), por lo que las celdas combinadas verticalmente se convierten en celdas repetidas o vacías en las filas siguientes en vez de usar `<td rowspan="N">`.
3. **Pérdida de Alineación y Estilos**: `docx_table_parser.py` crea elementos `<td>` sin transferir la alineación del texto (`align="left|center|right"`) ni preservar reglas estandarizadas de tabla JATS HTML.

---

## Cambios Propuestos

---

### Componente: Parser y Conversor de Tablas DOCX (`docx_table_parser.py`)

#### [MODIFY] [`docx_table_parser.py`](file:///Users/adrianevi/xmlPage/xmlPaper/docx_table_parser.py)

- **Inspección de elementos XML nativos (`w:tcPr`)**:
  - Leer la propiedad `w:gridSpan` de cada celda (`tc.span`) para asignar el atributo `colspan="N"`.
  - Leer la propiedad `w:vMerge` (`restart` para inicio de bloque, `continue` para filas secundarias) para calcular el total de filas combinadas y asignar `rowspan="N"`.
  - Omitir la generación de celdas `<td>` redundantes cuando ya forman parte de un `colspan` o `rowspan` previamente abierto.
- **Preservación de Alineaciones**:
  - Extraer la alineación de los párrafos internos (`p.alignment` o `w:jc`) para asignar `align="center"`, `align="left"` o `align="right"` en la etiqueta `<td>`.
- **Estructuración JATS XML Estándar**:
  - Garantizar que la tabla generada contenga una estructura limpia y válida según la DTD JATS SciELO SPS:
    ```xml
    <table-wrap id="t1">
      <label>Tabla 1</label>
      <caption><title>...</title></caption>
      <table>
        <tbody>
          <tr>
            <td colspan="2" align="left">...</td>
            <td align="center">...</td>
          </tr>
          <tr>
            <td rowspan="3" align="left">...</td>
            <td align="left">...</td>
            <td align="center">...</td>
          </tr>
        </tbody>
      </table>
      <table-wrap-foot>...</table-wrap-foot>
    </table-wrap>
    ```

---

### Componente: Formateador Global de Tablas (`main.py`)

#### [MODIFY] [`main.py`](file:///Users/adrianevi/xmlPage/xmlPaper/main.py)

- Actualizar la función `format_tables(soup)` para preservar los atributos `colspan`, `rowspan` y `align` existentes durante la limpieza o re-etiquetado de nodos `<table-wrap>`.

---

### Componente: Pipeline de Procesamiento SANUS (`process_sanus_batch.py`)

#### [MODIFY] [`process_sanus_batch.py`](file:///Users/adrianevi/xmlPage/xmlPaper/process_sanus_batch.py)

- Asegurar que la ejecución de `build_jats_table_from_docx` procese correctamente todos los archivos de la carpeta `SANUS` actualizando las tablas de los XMLs en `SANUSxmlNEW`.

---

## Plan de Verificación

### Pruebas Automatizadas
- Ejecutar un script de prueba en Python para convertir `560_ESP.docx` y comparar la tabla resultante contra el estándar de `t1`:
  - Verificar presencia de `<td colspan="2">` en fila 1.
  - Verificar presencia de `<td rowspan="3">` en fila 2.
  - Comprobar que no existan textos de celda duplicados en `SANUSxmlNEW/2448-6094-sanus-10-21-e560-NEW.xml`.

### Verificación Manual
- Abrir y validar los archivos XML en `SANUSxmlNEW/` para asegurar validez XML y estructura JATS SciELO SPS limpia.
