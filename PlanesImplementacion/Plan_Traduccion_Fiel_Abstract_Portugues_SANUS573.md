# Plan de Implementación: Traducción Fiel 1 a 1 de Secciones del Abstract en Portugués (573)

Se establece la regla general de traducción directa 1 a 1 entre las subsecciones del `<abstract>` en español y el `<trans-abstract xml:lang="pt">`, eliminando cualquier extracción secundaria del `<body>` o paráfrasis resumida.

---

## User Review Required

> [!IMPORTANT]
> **Regla de Traducción Estricta 1 a 1 para Metadatos Multilingües:**
> 1. **Correspondencia Exclusiva con `<abstract>`:**
>    - Cada sección `<sec>` de `<trans-abstract xml:lang="pt">` se generará como la traducción directa 1 a 1 de su sección homóloga en `<abstract>` (Español).
>    - Queda strictly prohibida la incorporación de texto derivado del `<body>` (como detalles de balanzas o estadiómetros no presentes en el resumen fuente) o resúmenes paráfrasis.
> 2. **Traducción Fiel de las 5 Subsecciones de SANUS 573:**
>    - **Introdução:** *"A adoção de hábitos alimentares é influenciada pela família, sendo a mãe a principal cuidadora, razão pela qual sua percepção exerce influência decisiva sobre os tipos de alimentos consumidos pelos escolares."*
>    - **Objetivo:** *"Conhecer a relação entre a percepção materna e os comportamentos alimentares sobre o estado nutricional dos escolares."*
>    - **Metodologia:** *"Estudo descritivo, correlacional e transversal em 223 díades (mães e escolares de primeiro a sexto ano)..."*
>    - **Resultados:** *"Apenas 47 % das mães perceberam corretamente o estado nutricional do filho..."*
>    - **Conclusões:** *"Existe uma distorção perceptiva materna sobre o peso dos filhos..."*

---

## Proposed Changes

### 1. Actualización de la Regla de Traducción de Abstracts (`fix_all_sanus_expert_rules.py` y `main.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Sustituir la sección `Introdução:` e `Metodologia:` en `sections_data` por las traducciones 1 a 1 literales del `<abstract>` en español de SANUS 573.
- Asegurar que no se inyecten datos externos extraídos del cuerpo del artículo.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Correspondencia 1 a 1 en `573_ESP.xml`:**
   - Comprobar que `<sec><title>Introdução:</title>` comience con *"A adoção de hábitos alimentares..."*.
   - Comprobar que `<sec><title>Metodologia:</title>` refleje fielmente las 223 díades, alumnos de 1º a 6º grado y la institución pública sin datos ajenos al resumen.
