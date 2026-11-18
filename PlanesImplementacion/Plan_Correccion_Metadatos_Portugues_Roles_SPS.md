# Plan de Implementación: Corrección de Metadatos en Portugués (573), Mapeo Exacto de Roles y Orden DTD JATS

Se establecen las acciones para corregir la contaminación de metadatos en portugués en el artículo 573, asignar la lista exacta de roles y firmas de afiliación para los 6 autores, ordenar los elementos de `<article-meta>` en estricta conformidad con el DTD de SciELO SPS y enlazar la mención de `Table 2` (`en-t2`) en la traducción en inglés.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Principales de Acción:**
> 1. **Corrección de Metadatos en Portugués (Artículo 573):**
>    - **Título Portugués:** `<trans-title>Relação entre a percepção materna e os comportamentos alimentares sobre o estado nutricional dos escolares</trans-title>`
>    - **Resumo Estruturado:** Incorporación de las subsecciones de *Objetivo*, *Metodologia*, *Resultados* y *Conclusões*.
>    - **Palavras-chave:** *Percepção materna*, *Estado nutricional*, *Comportamentos alimentares*, *Criança*.
> 2. **Mapeo Exacto de 6 Roles Académicos y Afiliaciones Originales (573):**
>    - **Autor 1 (Luz Elena Cano-Fajardo):** `<role>Doctorado en Metodología de la enseñanza</role>`
>    - **Autor 2 (Karla Neidy Perales-Hinojosa):** `<role>Licenciada en Enfermería</role>`
>    - **Autor 3 (Mayra Alejandra Mireles-Alonso):** `<role>Maestría en Enfermería</role>`
>    - **Autor 4 (San Juana López-Guevara):** `<role>Doctorado en Metodología de la Enseñanza</role>`
>    - **Autor 5 (Jesús Alejandro Guerra-Ordoñez):** `<role>Doctorado en Ciencias de Enfermería</role>`
>    - **Autor 6 (Tirso Duran-Badillo):** `<role>Doctorado en Metodología de la Enseñanza</role>`
>    - Reconstrucción de `<institution content-type="original">` en `<aff1>` a `<aff6>` vinculando exactamente estos títulos.
> 3. **Ordenamiento de Elementos en `<article-meta>` (Normativa DTD JATS / SciELO SPS):**
>    - Posicionar `<abstract>`, `<trans-abstract xml:lang="pt">`, `<kwd-group xml:lang="es">` y `<kwd-group xml:lang="pt">` **ANTES** de `<counts>` y `<funding-group>`.
> 4. **Enlace a Table 2 en Sub-artículo Inglés:**
>    - Garantizar que la mención a "Table 2" en el texto en inglés esté etiquetada como `<xref ref-type="table" rid="en-t2">Table 2</xref>`.

---

## Proposed Changes

### 1. Inyección y Corrección de Metadatos Portugueses por Archivo (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- **Separación de Diccionarios Multilingües por Archivo (`560` vs `573`):**
  - Mapear de forma diferenciada el título, resumen estructurado y palabras clave en portugués para el artículo 573 y 560.

---

### 2. Mapeo de Roles y Reconstrucción de Afiliaciones (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Actualizar la lista `roles_573` con las titulaciones exactas declaradas por el experto.
- Regenerar los elementos `<institution content-type="original">` de `<aff1>` a `<aff6>` de forma consistente con el rol asignado a cada autor.

---

### 3. Reordenamiento Estricto de `<article-meta>` segun DTD SciELO SPS (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Reorganizar la secuencia de hijos en `<article-meta>`:
  1. `<title-group>`
  2. `<contrib-group>`
  3. `<aff>`
  4. `<pub-date>` & `<history>`
  5. `<permissions>`
  6. `<abstract>` (español)
  7. `<trans-abstract xml:lang="pt">` (portugués)
  8. `<kwd-group xml:lang="es">`
  9. `<kwd-group xml:lang="pt">`
  10. `<counts>`
  11. `<funding-group>`

---

### 4. Vinculación de `Table 2` en Inglés (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Ejecutar expresión regular en el texto del `<sub-article>` para convertir menciones textuales a `Table 2` en `<xref ref-type="table" rid="en-t2">Table 2</xref>`.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Metadatos Portugueses en 573:**
   - Comprobar que el título en portugués contenga *"Relação entre a percepção materna..."*.
   - Comprobar la presencia de las 4 secciones (`Objetivo`, `Metodologia`, `Resultados`, `Conclusões`) en `<trans-abstract xml:lang="pt">`.
2. **Verificación de Roles y Afiliaciones en 573:**
   - Validar que los 6 autores contengan exactamente sus 6 roles (incluyendo Jesús Alejandro y Tirso Duran-Badillo).
3. **Verificación de Secuencia DTD:**
   - Inspeccionar que `<trans-abstract>` y `<kwd-group>` antecedan a `<counts>`.
4. **Verificación de `<xref>` en Sub-artículo:**
   - Validar la existencia de `<xref ref-type="table" rid="en-t2">Table 2</xref>`.
