# Plan de Implementación: Estructura de Tablas y Enriquecimiento General de `<contrib-group>` (Word a JATS XML)

Este plan contempla dos mejoras estructurales clave para la conversión de documentos DOCX a JATS XML:
1. **Preservación de tablas**: Manejo de `colspan`, `rowspan`, alineaciones y bordes.
2. **Generación completa de `<contrib-group>`**: Inclusión de `<xref ref-type="aff"><sup>N</sup></xref>`, `<role>` para los títulos/grados de los autores, y extracción determinista de metadatos de autores cuando la portada en español carece de ellos (extrayendo desde el DOCX en inglés o encabezados).

---

## Causa Raíz Identificada

1. **`xref` de Afiliación Incompleto**: `main.py` generaba `<xref ref-type="aff" rid="affN"/>` como etiqueta vacía sin el número de superíndice (`<sup>N</sup>`) requerido por el estándar DTD SciELO SPS JATS v1.1.
2. **Roles de Autores Ausentes**: No se poblaban las etiquetas `<role>` con el título académico/profesional del autor (ej. "Doctor en Metodología de la Enseñanza", "Licenciatura en Enfermería").
3. **Omisión de Autores en Portadas**: En documentos como `573_ESP.docx`, la portada en español no contiene la lista de autores/afiliaciones, mientras que el documento `573_ENG.docx` (o las secciones secundarias) sí contiene los 6 autores con sus roles, ORCIDs y filiaciones.
4. **Modelos Gemini Obsoletos**: Los modelos en `main.py` incluían nombres de modelos no disponibles (`gemini-2.0-flash` retorno 404), impidiendo la extracción por IA cuando fallaban las cuotas.

---

## Cambios Propuestos

---

### Componente: Generador de Front-Matter SciELO (`main.py`)

#### [MODIFY] [`main.py`](file:///Users/adrianevi/xmlPage/xmlPaper/main.py)

- **Actualizar `build_scielo_front`**:
  - Garantizar que cada `<xref ref-type="aff" rid="affN">` contenga `<sup>N</sup>` con el número correspondiente a la afiliación.
  - Insertar la etiqueta `<role>` cuando exista información de grado, título o función del autor.
  - Soportar múltiples afiliaciones por autor si están separadas por coma.
- **Extractor Determinista / Fallback de Autores desde DOCX**:
  - Implementar parser determinista de párrafos de título/autores de DOCX (vía `python-docx`) para extraer nombres, apellidos, ORCID, número de afiliación y rol académico cuando la extracción de Gemini devuelva autores vacíos.
  - En `process_sanus_batch.py`, pasar como fallback el texto o ruta del archivo de idioma complementario (`_ENG.docx`) para completar la lista de autores si el archivo en español no los incluye en portada.
- **Actualizar lista de modelos Gemini**:
  - Cambiar los modelos a `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro` para evitar errores 404.

---

### Componente: Batch Processing (`process_sanus_batch.py`)

#### [MODIFY] [`process_sanus_batch.py`](file:///Users/adrianevi/xmlPage/xmlPaper/process_sanus_batch.py)

- Integrar la extracción complementaria de autores de `_ENG.docx` a `_ESP.docx` durante la generación del XML final.
- Formatear el XML con sangría de tabuladores (`\t`) conservando la estética SciELO.

---

## Plan de Verificación

### Pruebas Automatizadas
- Ejecutar la generación en batch para el archivo `573` (`573_ESP.docx` y `573_ENG.docx`).
- Validar mediante script que el XML resultante en `SANUSxmlNEW/573_ESP.xml` y `SANUSxmlNEW/2448-6094-sanus-10-21-e573.xml` contenga:
  - `<contrib-group>` con los 6 autores.
  - Cadena de `<xref ref-type="aff" rid="aff1"><sup>1</sup></xref>`.
  - Etiqueta `<role>` con la profesión/grado de cada autor.
  - Estructura limpia e indentada con `\t`.

### Verificación Manual
- Abrir y validar el archivo XML resultante en el editor.
