# Plan de Implementación: Ajustes de Producción Definitivos JATS XML (SciELO SPS)

Se detallan las soluciones técnicas para corregir los 8 puntos residuales señalados por el experto, garantizando la extracción completa de las 6 afiliaciones con sus `<role>`, la separación semántica de la Inteligencia Artificial, la captura íntegra de captions en las Tablas 1 y 2, y el saneamiento completo de las citas.

---

## User Review Required

> [!IMPORTANT]
> **Cambios Estructurales de Producción:**
> 1. **Extracción y Desacoplamiento de 6 Afiliaciones:** Se reconstruirá la asignación de afiliaciones para generar 6 nodos `<aff id="aff1">` ... `<aff id="aff6">` diferenciados por titulación académica (ej. *Doctorado en Metodología...*, *Licenciatura en Enfermería*), registrando el grado en la etiqueta `<role>` del autor.
> 2. **Captura Completa de Títulos en Tablas 1 y 2:** Se ampliará la inspección previa a `<table-wrap>` para detectar títulos con marcado especial (negritas o encabezados incrustados), separando `<label>Table 1</label>` y `<caption><title>Nutritional status...</title></caption>` en español e inglés.
> 3. **Independización de la Sección de Inteligencia Artificial:** Se desacoplará el bloque de Inteligencia Artificial de la sección de *Financiamiento*, creando una etiqueta `<sec>` independiente para IA tanto en el artículo principal como en el `<sub-article>`.
> 4. **Enlace a Table 2 y Metadatos en Inglés:** Se garantizará el enlace a `en-t2` y la traducción del nodo `<subject>` a "Research" en el `<sub-article>`.

---

## Proposed Changes

### 1. Extracción Estricta de 6 Afiliaciones y `<role>` (`main.py` y `fix_all_sanus_expert_rules.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Reconstruir la lógica de post-procesamiento de autores y afiliaciones:
  - Cuando los autores pertenezcan a la misma universidad pero con títulos académicos distintos, crear entradas únicas `<aff id="aff1">` a `<aff id="aff6">` conservando el texto descriptivo original en `<institution content-type="original">`.
  - Asignar el elemento `<role>` a cada `<contrib contrib-type="author">` con la titulación respectiva.

---

### 2. Captura de Títulos de Tablas 1 y 2 y Separación de Label/Caption (`main.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Función `format_tables`:**
  - Buscar párrafos precedentes considerando etiquetas `<bold>`, `<p>` o `<sec>` que inicien con `Tabla 1`, `Tabla 2`, `Table 1`, `Table 2`.
  - Separar explícitamente la etiqueta numérica en `<label>` y el resto del texto descriptivo en `<caption><title>`.
  - Aplicar la misma lógica a las tablas en inglés para evitar que `<caption>` contenga únicamente "Table 1".

---

### 3. Independización de la Sección de Inteligencia Artificial (`main.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Función `restructure_body_to_sections`:**
  - Detectar el sub-encabezado "Inteligencia artificial" o "Artificial intelligence" dentro de la sección de *Financiamiento* y cerrarla para iniciar un nuevo nodo `<sec id="secX"><title>Inteligencia artificial</title>...</sec>`.

---

### 4. Corrección de Enlaces, Fechas y Metadatos en Inglés (`main.py` y `fix_all_sanus_expert_rules.py`)

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- **Fecha de Publicación:** Asignar la fecha de publicación real `04/02/2026` para el volumen 10 número 21.
- **Enlace a Table 2:** Asegurar la conversión de las menciones a `Table 2` en `<xref ref-type="table" rid="en-t2">Table 2</xref>`.
- **Subject en Sub-artículo:** Traducir `<subject>` a "Research" dentro del `<front-stub xml:lang="en">`.
- **Saneamiento "Cómo citar":** Eliminar la duplicación concatenada utilizando únicamente la cadena del nodo `mixed-citation`.

---

## Verification Plan

### Automated Tests
1. **Verificación de 6 Afiliaciones y `<role>`:**
   - Confirmar la presencia de `<aff id="aff1">` hasta `<aff id="aff6">` y 6 nodos `<role>` en el XML.
2. **Verificación de Captions en Tablas 1 y 2:**
   - Confirmar que las tablas 1 y 2 posean `<caption><title>` con el texto descriptivo completo.
3. **Verificación de Sección de IA Separada:**
   - Confirmar la existencia de `<sec><title>Inteligencia artificial</title></sec>` independiente de *Financiamiento*.
4. **Verificación de Enlace a Table 2:**
   - Confirmar la presencia de `<xref ref-type="table" rid="en-t2">` en el cuerpo en inglés.
