# Plan de Solución: Unicidad de IDs en Pies de Tabla, Normalización de IA, Sanitización de Figuras y Resumen Portugués

Este plan aborda los 5 problemas específicos reportados en la revisión final del lote XML JATS.

---

## Problemas Detectados y Soluciones Propuestas

### 1. IDs Duplicados en Pies de Tabla (`TFN1`..`TFN4`)
- **Problema:** Los elementos `<fn fn-type="other">` dentro de `<table-wrap-foot>` en las tablas del `sub-article` en inglés utilizan IDs principales (`TFN1`..`TFN4`) en lugar de IDs con prefijo `en-` (`en-TFN1`..`en-TFN4`), ocasionando 4 IDs duplicados en el documento compuesto.
- **Solución:**
  - En `format_tables` (en `main.py`) y en la regla de normalización (`apply_10_out_of_10_expert_fixes.py`), asignar prefijos explícitos de idioma para los IDs de pie de tabla: `en-TFN1`..`en-TFN4` para las tablas dentro de `<sub-article>`, y `TFN1`..`TFN4` para las tablas del cuerpo principal en español.

### 2. Sección "Inteligencia Artificial" Triplicada y Mal Distribuida
- **Problema:** El cuerpo español contiene:
  1. Párrafo sobre IA anidado dentro de `<sec sec-type="financial-disclosure">` (Financiamiento).
  2. Una sección `<sec>` de IA totalmente vacía.
  3. Otra sección `<sec>` de IA que solo contiene el título `<bold>Inteligencia artificial</bold>`.
- **Solución:**
  - Extraer el párrafo de declaración de uso de IA fuera de la sección de Financiamiento.
  - Eliminar todas las secciones `<sec>` vacías o redundantes relativas a Inteligencia Artificial.
  - Consolidar una **única sección final** `<sec id="sec9">` con `<title>Inteligencia artificial</title>` conteniendo la declaración textual completa de los autores, posicionada inmediatamente después de `<sec sec-type="financial-disclosure">`.

### 3. Figura Inglesa (`en-f1`) Anidada Dentro de un Párrafo (`<p>`)
- **Problema:** En el `sub-article` inglés, la figura `<fig id="en-f1">` se encuentra anidada como hijo directo de `<p>`, lo cual viola la especificación de bloques en JATS DTD.
- **Solución:**
  - En `format_figures` y en la sanitización final, verificar si algún nodo `<fig>` o `<graphic>` tiene un padre directo `<p>`.
  - Des-envolver el nodo `<fig>` moviéndolo como hermano después del párrafo `<p>`, y eliminar el `<p>` si queda vacío.

### 4. Atributo `href` Redundante en Nodos `<graphic>`
- **Problema:** Los nodos gráficos incluyen tanto `href="..."` como `xlink:href="..."`. El atributo sin prefijo `href` es no estándar en JATS y puede provocar rechazo en la validación DTD.
- **Solución:**
  - Eliminar el atributo plano `href` de todos los elementos `<graphic>` e `<inline-graphic>`, conservando exclusivamente `xlink:href="..."`, `ext-link-type="uri"`, `mimetype="image"` y `mime-subtype="png"`.

### 5. Extracción y Estructuración del Resumen en Portugués desde el DOCX Fuente
- **Problema:** El resumen en portugués presente en el DOCX fuente (sección *"Abstrato"*) no se estaba incorporando al XML final porque la purga previa de metadatos en `clean_body_duplicate_metadata` eliminaba esos párrafos antes de que el extractor de resúmenes los procesara.
- **Solución:**
  - Modificar `clean_body_duplicate_metadata` y `extract_structured_abstracts_from_body` para preservar y extraer los párrafos del resumen en portugués desde el DOCX fuente antes de efectuar la purga.
  - Formatear el resumen en portugués en `<trans-abstract xml:lang="pt">` con sus secciones correspondientes (`Introdução:`, `Objetivo:`, `Metodologia:`, `Resultados:`, `Conclusões:`).

---

## Proposed Changes

### Core Engine & Pipeline

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **`format_tables(soup)`**: Generar IDs `en-TFNx` para tablas en `<sub-article>`.
- **`clean_body_duplicate_metadata(soup, metadata)`**: Preservar el bloque del resumen portugués para su extracción antes de purgar párrafos iniciales.

#### [MODIFY] [apply_10_out_of_10_expert_fixes.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/apply_10_out_of_10_expert_fixes.py)
- Renombrar cualquier ID de pie de tabla en `<sub-article>` a `en-TFNx`.
- Consolidar la sección de Inteligencia Artificial en español en una sola sección `<sec id="sec9">` con el texto completo y eliminar secciones/párrafos duplicados en Financiamiento.
- Des-envolver `<fig>` si está dentro de un `<p>`.
- Eliminar el atributo plano `href` de todos los `<graphic>`.

---

## Verification Plan

### Automated Tests & Script Validation
1. Re-procesar el artículo 566 y el lote completo.
2. Ejecutar un script de verificación automatizado para confirmar:
   - Que **todos** los 66 atributos `id` del XML compuesto sean 100% únicos (0 duplicados).
   - Que exista exactamente **1 sección** de Inteligencia Artificial en español con su título y cuerpo completo.
   - Que la figura `en-f1` no esté dentro de un `<p>`.
   - Que ningún nodo `<graphic>` contenga el atributo plano `href`.
   - Que `<trans-abstract xml:lang="pt">` contenga el resumen completo extraído del DOCX.

### Manual Verification
- Inspeccionar la estructura final de `566_ESP.xml`.
