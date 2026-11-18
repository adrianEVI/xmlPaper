# Plan de Implementación: Refinamiento Integral JATS XML (SciELO SPS)

Basado en el diagnóstico del experto, se han definido **9 áreas de mejora estratégica** ordenadas jerárquicamente para llevar la generación de XMLs JATS 1.1 al 100% de cumplimiento con el estándar de producción SciELO SPS.

---

## User Review Required

> [!IMPORTANT]
> **Puntos clave de diseño e implementación:**
> 1. **Citas Bibliográficas y Tablas (`<xref>`):** Se transformarán automáticamente todas las citas numéricas del texto (`(1)`, `(8,9)`, `(3-7)`) y menciones a tablas/figuras (`Tabla 1`) en hipervínculos semánticos `<xref ref-type="bibr" rid="BX">` y `<xref ref-type="table" rid="tX">`.
> 2. **Afiliaciones y `<role>`:** Se mantendrán afiliaciones independientes (`aff1`, `aff2`, ..., `aff6`) considerando el grado académico y departamento, separando el grado en el elemento `<role>`.
> 3. **Distribución Multilingüe:** El artículo principal (`<article xml:lang="es">`) incluirá los metadatos en Portugués (`<trans-title-group xml:lang="pt">`, `<trans-abstract xml:lang="pt">`, `<kwd-group xml:lang="pt">`), reservando el `<sub-article xml:lang="en">` para la traducción completa en inglés.
> 4. **Consolidación Bibliográfica:** Las citas del `<sub-article>` apuntarán a la lista bibliográfica única del artículo principal (`B1`, `B2`, ...), evitando duplicar el `<ref-list>` en la traducción y ajustando el `<ref-count>` exacto.

---

## Proposed Changes

### Fase 1: Vinculación Automatizada de `<xref>` (Citas Bibliográficas y Tablas/Figuras)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Función `auto_link_cross_references(soup)`:**
  - Implementar expresiones regulares para detectar patrones de superíndice o paréntesis numéricos:
    - Simples `(15)` -> `<xref ref-type="bibr" rid="B15"><sup>15</sup></xref>`
    - Múltiples `(8,9)` -> `<xref ref-type="bibr" rid="B8"><sup>8</sup></xref><sup>,</sup><xref ref-type="bibr" rid="B9"><sup>9</sup></xref>`
    - Rangos `(3-7)` -> `<xref ref-type="bibr" rid="B3"><sup>3</sup></xref><sup>-</sup>...<sup>7</sup>`
  - Detectar menciones a tablas en el texto (ejemplo: `(Tabla 1)`) y convertirlas en `<xref ref-type="table" rid="t1">Tabla 1</xref>`.

---

### Fase 2: Purga del `<body>` y Desacoplamiento de Afiliaciones y `<role>`

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Purga de Metadatos sobrantes en `clean_body_duplicate_metadata`:**
  - Eliminar listas de afiliaciones, bloques de correspondencia, fechas de recibido/aceptado antes de la primera sección real (`<sec sec-type="intro">`).
- **Estructuración de Afiliaciones y `<role>`:**
  - Deduplicar afiliaciones evaluando la firma completa (`grado + departamento + institución + ciudad + país`).
  - Asignar `aff1`, `aff2`, ..., `aff6` a cada autor según corresponda.
  - Extraer el grado académico al nodo `<role>` dentro del autor (`<contrib contrib-type="author">`).

---

### Fase 3: Estructura Semántica de Tablas (`<label>`, `<caption>`, `<table-wrap-foot>`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Función `format_tables(soup)`:**
  - Extraer la primera línea superior con la numeración y título de la tabla e integrarlos en `<label>Tabla X</label>` y `<caption><title>Nombre de la tabla...</title></caption>` dentro de `<table-wrap id="tX">`.
  - Extraer el texto final de la fuente/notas de la tabla e integrarlo en `<table-wrap-foot><fn id="TFNX"><p>Fuente: ...</p></fn></table-wrap-foot>`.

---

### Fase 4: Metadatos Multilingües y Consolidación Bibliográfica

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Estructura `<front>` y Portugués:**
  - Extraer metadatos en portugués desde el DOCX y colocarlos en `<trans-title-group xml:lang="pt">`, `<trans-abstract xml:lang="pt">` y `<kwd-group xml:lang="pt">` en el `<front>` principal.
- **Consolidación Bibliográfica en `<sub-article>`:**
  - Eliminar la duplicación del `<ref-list>` en el `<sub-article>`.
  - Hacer que las citas bibliográficas del `<sub-article>` apunten directamente a los IDs principales (`B1`, `B2`, ...).
  - Calcular el `<ref-count>` contando exclusivamente las referencias únicas del `<back>` principal.

---

### Fase 5: Limpieza de Texto en Resúmenes y Notas Editorial

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Remoción de palabras repetidas en párrafos del resumen ("Introducción", "Objetivo:", etc.).
- Limpieza de concatenaciones indeseadas en la nota "Cómo citar" seleccionando únicamente la representación limpia.
- Corrección de fechas editoriales y `publisher-name` completo.

---

## Verification Plan

### Automated Tests
1. **Verificación de Enlaces `<xref>`:**
   - Confirmar que el conteo de `<xref ref-type="bibr">` en el cuerpo español e inglés sea > 0 y apunte a IDs existentes en `<ref>`.
   - Confirmar que las menciones a tablas tengan su enlace `<xref ref-type="table">`.
2. **Verificación de Afiliaciones y `<role>`:**
   - Confirmar que existan nodos `<aff id="aff1">` ... `<aff id="aff6">` y que cada `<contrib>` contenga su `<role>`.
3. **Verificación de Tablas y Metadatos Multilingües:**
   - Confirmar que todo `<table-wrap>` posea `<label>`, `<caption>` y `<table-wrap-foot>`.
   - Confirmar que el `<front>` contenga metadatos en portugués (`xml:lang="pt"`) y que el `<sub-article>` no duplique el `<ref-list>`.
