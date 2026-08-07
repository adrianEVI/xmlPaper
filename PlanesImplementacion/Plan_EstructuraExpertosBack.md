# Plan de Implementación: Alineación de Estructura de Marcado con el Experto

## Descripción
Ajustes realizados en el pipeline de procesamiento `main.py` para replicar exactamente las convenciones de marcado del experto SciELO SPS:

1. **Orden en `<back>`**: `<ref-list>` se coloca **primero** y `<fn-group>` **segundo**.
2. **Título Dinámico de Referencias**: Conservación del título exacto detectado en el documento Word (ej. `"VIII. Fuentes de información"`, `"VII. Referencias bibliográficas"`).
3. **Numeración y Atributos de Notas al Pie**: IDs de la forma `id="fn1"`, `id="fn2"`, etiquetado `fn-type="other"`, y vinculación cruzada `<xref ref-type="fn" rid="fn1"><sup>1</sup></xref>`.
4. **Vinculación de Citas Bibliográficas en Notas al Pie**: Procesamiento automático de hipervínculos `<xref ref-type="bibr" rid="B1">` tanto en el cuerpo principal (`<body>`) como en las notas al pie (`<fn-group>`).

## Archivos Modificados
- `main.py`
  - `extract_bibliography_paragraphs`: Retorna `(ref_nodes, section_title)` capturando el título exacto de la sección bibliográfica.
  - `build_ref_list_xml`: Acepta el título dinámico para `<ref-list><title>`.
  - Endpoint `/convert`: Extrae `<fn-group>` y lo inserta después de `<ref-list>` en el elemento `<back>`.
  - `auto_link_cross_references`: Extendido para procesar y crear referencias `<xref ref-type="bibr">` en párrafos dentro de `<fn-group>`.
