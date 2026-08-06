# Plan de Implementación: Limpieza Bibliográfica y Verificación de Validación SPS/SciELO

Se estructuran las acciones para la depuración de inconsistencias bibliográficas en la cita del Instituto Nacional de Salud Pública / INEGI y la preparación del paquete XML para su validación oficial de DTD, SPS y Schematron de SciELO.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Principales de Acción:**
> 1. **Depuración de Citas Bibliográficas (`<ref>`):**
>    - Inspeccionar y limpiar la referencia donde se presenta la mezcla del *Instituto Nacional de Salud Pública* con *(INEGI)*, asegurando que se conserve el texto exacto sin superposición de acrónimos erróneos.
> 2. **Fidelidad del Resumen Portugués:**
>    - Garantizar que la extracción y estructura de las 5 secciones (`Introdução`, `Objetivo`, `Metodologia`, `Resultados`, `Conclusões`) permanezca idéntica a la fuente.
> 3. **Verificación de Estructura para Validación SPS/SciELO:**
>    - Realizar un chequeo integral de conformidad sintáctica JATS XML (DTD, SPS y Schematron) en los 12 archivos XML de producción.

---

## Proposed Changes

### 1. Limpieza de Cita Bibliográfica (`fix_all_sanus_expert_rules.py` y `main.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Buscar y corregir la referencia bibliográfica que contiene `"Instituto Nacional de Salud Pública (INEGI)"` para separar adecuadamente el autor institucional o ajustar el texto a la cita real de la fuente.

---

### 2. Verificación de Conformidad DTD/SPS

#### [NEW] [verify_sps_xml_structure.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/verify_sps_xml_structure.py)
- Crear un script autónomo de validación para comprobar la estructura de las etiquetas JATS XML de todos los archivos en `Articulos/SANUS/SANUSxmlNEW`, reportando cero errores de DTD o jerarquía de nodos.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Cita Bibliográfica:**
   - Ejecutar un chequeo en los `<ref>` para comprobar que no exista la mezcla `"Instituto Nacional de Salud Pública (INEGI)"`.
2. **Ejecución del Verificador de Estructura SPS:**
   - Ejecutar `python verify_sps_xml_structure.py` para asegurar que el 100% de los 12 archivos XML cumpla con las reglas sintácticas y jerárquicas de SciELO.
