# Plan de Mejora: Normalización y Unicidad Estricta de IDs en JATS XML (SciELO SPS)

Analizando las observaciones del experto, se identifican **22 errores de unicidad de IDs** causados por duplicación de identificadores entre el artículo principal (Español) y la traducción (`<sub-article xml:lang="en">`), además de omisión de `id` en tablas del cuerpo principal e inconsistencias de formato en los IDs de secciones (`<sec>`).

## User Review Required

> [!IMPORTANT]
> **Cambios en la estructura de IDs:**
> 1. Se prefijarán todos los identificadores del `<sub-article>` en inglés con `en-` (`en-f1`, `en-t1`, `en-B1`, `en-sec1`).
> 2. Se actualizarán automáticamente las referencias cruzadas (`<xref>`) internas dentro del `<sub-article>` para apuntar a los nuevos atributos `rid` prefijados (ejemplo: `<xref ref-type="bibr" rid="en-B1">`).
> 3. Las secciones (`<sec>`) se estandarizarán en formato canónico neutro (`sec1`, `sec2`, ..., y `en-sec1`, `en-sec2`, ...), eliminando acentos y nombres en idioma local.

## Proposed Changes

### 1. Motor de Conversión JATS y Sub-artículo (`main.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Normalización de IDs en `<sub-article>`:**
  - En la construcción del `<sub-article>`, renombrar todas las figuras a `id="en-f1"`, `en-f2`, ...
  - Renombrar todas las tablas a `id="en-t1"`, `en-t2`, ...
  - Renombrar todas las referencias bibliográficas a `id="en-B1"`, `en-B2`, ...
  - Renombrar las secciones a `id="en-sec1"`, `en-sec2`, ...
  - Actualizar los elementos `<xref>` dentro del `<sub-article>` para que utilicen `rid="en-f1"`, `rid="en-t1"`, `rid="en-B1"`.
- **Asignación de IDs en Artículo Principal:**
  - Garantizar que todo `<table-wrap>` en el artículo principal reciba secuencialmente `id="t1"`, `id="t2"`, etc.
  - Normalizar los IDs de `<sec>` en el artículo principal a `sec1`, `sec2`, `sec3`, etc., removiendo acentos y caracteres especiales.

---

### 2. Script de Correcciones de Experto y Post-procesamiento

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Añadir una fase de post-procesamiento y saneamiento XML que:
  1. Detecte y prefije automáticamente con `en-` cualquier `id` y `rid` en `<sub-article>`.
  2. Asigne `id="tX"` a cualquier `<table-wrap>` huérfano en `<article>`.
  3. Reemplace los IDs de `<sec>` con nombres limpios (`sec1`, `sec2`, ..., `en-sec1`, `en-sec2`).

---

### 3. Pipeline de Generación por Lotes

#### [MODIFY] [process_sanus_batch.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/process_sanus_batch.py)
- Garantizar que el pipeline por lotes ejecute la rutina de saneamiento de IDs en todos los documentos.

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Unicidad de IDs en Python:**
   - Ejecutar un script que extraiga todos los atributos `id` de cada archivo XML generado en `Articulos/SANUS/SANUSxmlNEW`.
   - Confirmar que `len(ids) == len(set(ids))` en el 100% de los archivos XML (cero IDs duplicados).
2. **Validación del Mapeo `<xref>`:**
   - Verificar que todos los atributos `rid` en los nodos `<xref>` de cada XML tengan un nodo correspondiente con ese `id` exacto.
3. **Re-generación del Lote Completo:**
   - Ejecutar el lote completo de los 6 manuscritos y verificar que los 12 archivos XML cumplan strictly la convención:
     - Principal: `aff1`, `c1`, `sec1`, `f1`, `t1`, `B1`
     - Sub-article: `en-sec1`, `en-f1`, `en-t1`, `en-B1`
