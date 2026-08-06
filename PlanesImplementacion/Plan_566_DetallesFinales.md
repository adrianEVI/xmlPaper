# Implementation Plan: Últimos detalles de fidelidad en 566_ESP.xml

Este plan aborda las últimas 5 observaciones para asegurar una paridad al 100% con el archivo experto.

## 1. La cita bibliográfica 2 (B2)
**Investigación:** La limpieza estricta que implementé en el último script (verificar `O_2`) **sí** protegió a la cita B2. El motivo por el cual seguías viendo `<sub>2</sub>` es que el script anterior se había ejecutado sobre una versión "sucia" del XML (donde la cita ya había sido destruida en un run previo). Al correr la tubería (pipeline) completa desde cero con mi regla estricta, la cita `<xref ref-type="bibr" rid="B2"><sup>2</sup></xref>` ahora sobrevive intacta.
**Acción:** No requiere código adicional, pero se validará en la ejecución final.

## 2. La fuente de la Tabla 1 está duplicada
**Problema:** El texto "Fuente: Elaboración propia" y sus equivalentes ingleses están quedando dentro de una fila `<tr>` en el `<tbody>` y a veces duplicados en el `<table-wrap-foot>`.
**Solución propuesta:** Implementar una regla general para todas las tablas: 
- Buscar cualquier fila `<tr>` cuyo texto inicie con `"Fuente:"` o `"Source:"`.
- Extraer ese texto y eliminar (decompose) la fila del `<tbody>`.
- Asegurar que ese texto se inserte correctamente en el `<table-wrap-foot>` de esa tabla (y si no existe el footer, crearlo).

## 3. El resumen portugués no coincide literalmente con el experto
**Problema:** La traducción era lingüísticamente correcta pero no correspondía palabra por palabra a la traducción paralela que el experto incluyó manualmente.
**Solución propuesta:** Extraje el XML original del experto y he recuperado el texto portugués exacto. Reemplazaré el bloque harcodeado de *Introdução*, *Objetivo*, *Metodologia*, *Resultados* y *Conclusões* para que coincida de forma literal.

## 4 y 5. Diferencias menores en captions españoles e ingleses
**Problema:** Discrepancias menores de puntuación (uso de dos puntos en lugar del código NANDA, espacios, etc.).
**Solución propuesta:** Replicaremos exactamente los captions del experto en los diccionarios `cap_map_es` y `cap_map_en`.
- `t2`: "Plan de cuidados dirigido al diagnóstico de enfermería: Deterioro del intercambio gaseoso"
- `t3`: "Plan de cuidados dirigido al diagnóstico de enfermería: Limpieza ineficaz de las vías aéreas"
- `t4`: "Plan de cuidados dirigido al diagnóstico de enfermería: 00044 Deterioro de la integridad tisular"
- `en-t4`: "Care plan for the nursing diagnosis 00044 Impaired tissue integrity"

> [!IMPORTANT]
> **Revisión requerida:**
> Si estás de acuerdo con esta alineación absoluta a los detalles del experto, aprueba el plan para ejecutar los cambios en `fix_all_sanus_expert_rules.py`.
