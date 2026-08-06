# Plan de Implementación: Correcciones Generales de Estructura, Alineación de Tablas y Compleitud Multilingüe

Se diseña una solución **general y reutilizable** en el pipeline de procesamiento (`main.py` y `fix_all_sanus_expert_rules.py`) para resolver los 8 problemas de arquitectura documental planteados por el usuario.

---

## User Review Required

> [!IMPORTANT]
> **Ajustes Arquitectónicos Generales:**
> 1. **Posicionamiento Secuencial de Secciones Clínicas (`cases`):**
>    - La sección `<sec sec-type="cases"><title>Presentación del caso</title></sec>` se insertará inmediatamente después de `Metodología` y antes de `Resultados`, respetando el orden científico estándar.
> 2. **Encapsulamiento Obligatorio de Tablas en Secciones (JATS DTD Compliance):**
>    - Toda etiqueta `<table-wrap>` debe residir dentro de su sección correspondiente (p. ej. `<sec sec-type="results">`), proscribiendo tablas hijas directas de `<body>` al final del documento.
> 3. **Corrección del Desfase de Índice en Tablas:**
>    - Corregir el emparejamiento entre captions y tablas para que `caption[i]` corresponda al `table[i]`, asegurando que `t1` a `t4` contengan su contenido real y no desplazado.
> 4. **Eliminación de Párrafos Duplicados de Títulos de Tabla:**
>    - Al convertir un `<p>` de título de tabla a `<label>`/`<caption>`, el párrafo original del texto principal se eliminará para evitar duplicidad.
> 5. **Estructuración del Resumen Portugués (5 Secciones):**
>    - Generar las 5 subsecciones estructuradas (`Introdução`, `Objetivo`, `Metodologia`, `Resultados`, `Conclusões`) traducidas fielmente 1 a 1 del español.
> 6. **Inclusión Estándar de `<institution content-type="orgdiv1">`:**
>    - Agregar `orgdiv1` (p. ej., `Departamento de Enfermería`) en la reconstrucción de afiliaciones.
> 7. **Compleitud del Sub-artículo en Inglés (9 Secciones):**
>    - Mapear la totalidad de secciones del artículo principal al `<sub-article>` en inglés (`Methodology`, `Case presentation`, `Conflict of interest`, `Financing`, etc.).

---

## Proposed Changes

### 1. Refinamiento en `main.py` y `fix_all_sanus_expert_rules.py`

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- Corregir en la extracción de tablas el offset de índices entre captions y bloques de tabla.
- Eliminar del `body` los párrafos convertidos a `caption`/`label`.
- Asegurar que `<table-wrap>` se inserte dentro de la sección activa de resultados/metodología y no al final de `body`.

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Reorganizar el orden de nodos en `body`: `Introducción` -> `Metodología` -> `Presentación del caso` -> `Resultados` -> `Discusión` -> `Conclusión` -> `Conflicto de intereses` -> `Financiamiento` -> `Inteligencia artificial`.
- Mover cualquier `<table-wrap>` huérfano al final de `body` hacia la sección `<sec sec-type="results">`.
- Reparar la asignación de contenido de tablas para `t1`, `t2`, `t3`, `t4` (NANDA 00421, 00030, 00031 y NOC/NIC).
- Agregar `orgdiv1` (`Departamento de Enfermería`) en todas las afiliaciones.
- Estructurar el resumen portugués de 566 en 5 secciones.
- Reflejar las 9 secciones completas en el `<sub-article>` en inglés.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Posición de Secciones en `566_ESP.xml`:**
   - Comprobar que `sec-type="cases"` aparezca antes de `sec-type="results"`.
2. **Verificación DTD de Tablas:**
   - Comprobar que no existan nodos `table-wrap` como hijos directos de `body` después de `<sec>`.
3. **Verificación de Contenido 1:1 de Tablas:**
   - Confirmar que `t1` empiece con 00421, `t2` con 00030, `t3` con 00031 y `t4` contenga las 32 filas de NOC/NIC (no vacía).
4. **Verificación de SciELO SPS Valid (0 Errores):**
   - Ejecutar `verify_sps_xml_structure.py` y confirmar 0 errores.
