# Plan de Implementación: Refinamiento Avanzado JATS XML (SciELO SPS)

Se estructuran las **9 correcciones de precisión de producción** indicadas por el experto para alcanzar el 100% de coincidencia estructural con el estándar JATS 1.1 SciELO SPS.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Clave de Implementación:**
> 1. **Diferenciación de 6 Afiliaciones y `<role>`:** Gemini y el extractor de metadatos asignarán afiliaciones únicas (`aff1` ... `aff6`) por combinación de grado académico y departamento, extrayendo el grado académico al elemento `<role>`.
> 2. **Citas Numéricas Inline y en Superíndice:** El reconocedor de citas abarcará tanto superíndices `<sup>(15)</sup>` como citas entre paréntesis en texto plano `(17)`, `(18)`, `(8,9)`, `(13-15)` sin requerir formato superíndice de Word.
> 3. **Purga Completa de Secciones "Recibido" / "Aceptado":** Se eliminarán las etiquetas `<sec>` de "Recibido" y "Aceptado" del inicio del `<body>`, asegurando que su información resida únicamente en la etiqueta `<history>` del `<front>`.
> 4. **Asociación de Títulos de Tablas 1 y 2:** Se ampliará la inspección previa a `<table-wrap>` para capturar títulos en párrafos anteriores con formatos heterogéneos, evitando etiquetas `<caption/>` vacías.

---

## Proposed Changes

### 1. Extracción de Afiliaciones y `<role>` (`main.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Ajuste del Prompt de Metadatos:**
  - Solicitar explícitamente a Gemini que no consolide autores en una sola afiliación si poseen distintos grados académicos o departamentos.
  - Extraer la titulación académica en la propiedad `role` del autor (ej. `Doctorado en Metodología de la Enseñanza`, `Licenciatura en Enfermería`).
  - Generar un nodo `<aff id="affX">` independiente por cada combinación única de grado y área.

---

### 2. Purga Estricta de Secciones de Historia en el `<body>` (`main.py` y `fix_all_sanus_expert_rules.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- **Eliminación de Nodos "Recibido" y "Aceptado":**
  - Eliminar del `<body>` cualquier sección `<sec>` cuyo título contenga "Recibido", "Aceptado" o "Received", "Accepted", dado que dichos datos ya han sido registrados en la etiqueta `<history>` de la cabecera.

---

### 3. Enlazado Avanzado de Citas Bibliográficas Inline (`auto_link_cross_references`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Detección de Citas sin Superíndice:**
  - Extender la función `auto_link_cross_references` para analizar nodos de texto e identificar paréntesis numéricos `(17)`, `(18)`, `(8,9)` y rangos `(13-15)` fuera de la etiqueta `<sup>`.
  - Convertir cada número o rango en su correspondiente `<xref ref-type="bibr" rid="BX">`.
  - Asegurar la transformación explícita de las menciones a `Table 2` o `Tabla 2` en `<xref ref-type="table" rid="en-t2">Table 2</xref>`.

---

### 4. Reparación de `<caption>` en Tablas 1 y 2 (`format_tables`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Captura Flexible de Título:**
  - Inspeccionar los 2 párrafos anteriores a todo `<table-wrap>` con la expresión regular `^(?:Tabla|Table|Tabela)\s*\d*[\.\:]?\s*(.*)$`.
  - Extraer el texto restante como `<caption><title>Texto del título</title></caption>` y eliminar etiquetas `<caption/>` vacías.

---

### 5. Limpieza de Texto en Resúmenes y Notas Editorial (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- **Limpieza de Prefijos:**
  - Remover mediante expresión regular `^\s*(?:Introducción|Objetivo|Metodología|Resultados|Conclusiones|Introduction|Objective|Methodology|Results|Conclusions|Introdução)\s*:?\s*` cualquier palabra sobrante concatenada al inicio de los párrafos del resumen.
- **Saneamiento de "Cómo citar":**
  - Extraer únicamente el texto directo del nodo `mixed-citation` evitando concatenaciones con descendientes.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Citas Inline en Inglés:**
   - Confirmar que las citas `(17)` y `(18)` en el `<sub-article>` inglés posean su correspondiente `<xref ref-type="bibr" rid="B17">17</xref>`.
2. **Verificación de Afiliaciones y `<role>`:**
   - Validar la existencia de 6 nodos `<aff id="aff1">` ... `<aff id="aff6">` y la presencia de `<role>` en los nodos de autor.
3. **Verificación de `<caption>` en Tablas 1 y 2:**
   - Validar que ninguna tabla contenga `<caption/>` vacío.
4. **Verificación de Purga del `<body>`:**
   - Comprobar que no existan secciones `<sec>` tituladas "Recibido" o "Aceptado" en el `<body>`.
