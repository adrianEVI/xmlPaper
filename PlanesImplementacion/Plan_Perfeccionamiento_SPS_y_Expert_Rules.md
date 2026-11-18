# Plan de Perfeccionamiento Final: Atributos Graphic JATS, Resumen Portugués Exacto e Identificadores Editoriales

Este plan resuelve las 4 observaciones finales presentadas en la revisión de conformidad experta con el estándar SciELO SPS / JATS DTD 1.1.

---

## Problemas Identificados y Soluciones Propuestas

### 1. Eliminación del Atributo `ext-link-type="uri"` en Elementos `<graphic>`
- **Problema:** En el DTD de JATS 1.1, la etiqueta `<graphic>` no permite el atributo `ext-link-type` (el cual pertenece exclusivamente a `<ext-link>`). Su presencia en `<graphic>` puede ocasionar fallos strictly en la validación DTD.
- **Solución:**
  - En la rutina de sanitización de gráficos (`format_figures` y `apply_10_out_of_10_expert_fixes.py`), eliminar el atributo `ext-link-type` de todos los elementos `<graphic>` e `<inline-graphic>` en todo el documento (cuerpo principal y `sub-article`).

### 2. Corrección Fiel y Terminología NANDA Exacta en Resumen en Portugués
- **Problema:** El resumen en portugués generado presentaba pequeños arcaísmos/hispanismos (*"lenguaje padronizada"*, *"emplear o pensamento"*) y discrepancias terminológicas frente a la taxonomía NANDA padronizada en portugués (`troca gasosa prejudicada`, `integridade tecidual prejudicada`).
- **Solución:**
  - Reemplazar el texto del `<trans-abstract xml:lang="pt">` en el artículo 566 por la versión 100% literal y exacta proveniente del documento experto, asegurando terminología de enfermería correcta y portugués profesional impecable.

### 3. Asignación de Identificadores Editoriales Secundarios (`article-id pub-id-type="other"`)
- **Problema:** El nodo `<article-id pub-id-type="other">` contenía valores provisionales eliminados o faltantes frente a los registros de orden SciELO de la publicación.
- **Solución:**
  - Mapear e insertar el identificador de orden editorial oficial correspondiente para cada artículo del lote SANUS:
    - `549` -> `00113`
    - `560` -> `00112`
    - `561` -> `00304`
    - `564` -> `00111`
    - `566` -> `00202`
    - `573` -> `00110`

### 4. Uniformidad de Atributos en Nodos `<graphic>` (Español e Inglés)
- **Problema:** Las figuras en español incluían `mimetype="image"` y `mime-subtype="png"`, mientras que la figura del `sub-article` en inglés solo incluía `xlink:href="..."`.
- **Solución:**
  - Normalizar todos los elementos `<graphic>` y `<inline-graphic>` en ambas versiones lingüísticas para incluir de forma homogénea:
    ```xml
    <graphic mimetype="image" mime-subtype="png" xlink:href="[ISSN]-[JOURNAL]-[VOL]-[ISSUE]-[ARTICLE_ID]-gfX.png"/>
    ```

---

## Proposed Changes

### Pipeline & Normalization Scripts

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **`format_figures(soup)`**: Eliminar `ext-link-type` de elementos `<graphic>` e `<inline-graphic>` e inyectar `mimetype="image"` y `mime-subtype="png"` tanto en el cuerpo principal como en `<sub-article>`.

#### [MODIFY] [fix_how_to_cite_and_subarticle.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_how_to_cite_and_subarticle.py)
- Asignar el `<article-id pub-id-type="other">` correspondiente según el mapa de orden oficial (`00202` para 566, etc.).

#### [MODIFY] [apply_10_out_of_10_expert_fixes.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/apply_10_out_of_10_expert_fixes.py)
- Incorporar la limpieza estricta de atributos `ext-link-type` en `<graphic>`.
- Inyectar el resumen portugués 100% exacto del experto para 566.
- Asignar `mimetype="image"` y `mime-subtype="png"` de forma uniforme a todas las figuras.

---

## Verification Plan

### Automated Tests & Script Validation
1. Ejecutar el pipeline completo de post-procesamiento.
2. Ejecutar un script de verificación automatizado para confirmar:
   - Que **0** elementos `<graphic>` o `<inline-graphic>` tengan el atributo `ext-link-type`.
   - Que **100%** de los elementos `<graphic>` tengan `mimetype="image"` y `mime-subtype="png"`.
   - Que `566_ESP.xml` contenga `<article-id pub-id-type="other">00202</article-id>`.
   - Que el `<trans-abstract xml:lang="pt">` de 566 contenga las formulaciones exactas (`linguagem de enfermagem padronizada`, `troca gasosa prejudicada`).

### Manual Verification
- Visualizar `566_ESP.xml` para constatar la pulcritud del XML final.
