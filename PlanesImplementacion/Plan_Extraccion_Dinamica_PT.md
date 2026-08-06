# Implementation Plan: Extracción Dinámica del Resumen en Portugués desde el DOCX

Tienes toda la razón. Si el DOCX original contiene su propio resumen en portugués, el sistema no debería sobreescribirlo ni descartarlo, ni depender de un "hardcode" sacado del XML del experto (que parece haberlo editado de forma manual y ajena al autor original).

## Análisis del Problema
He revisado el motor principal (`main.py`) que convierte el DOCX, y he encontrado el motivo exacto de la pérdida:
En la función `extract_structured_abstracts_from_body`, el código identifica correctamente los resúmenes en español e inglés y los guarda en las variables `metadata.abstract_es` y `metadata.abstract_en`. Sin embargo, cuando detecta el resumen en portugués, simplemente ejecuta un `p.decompose()` (lo borra) **sin guardar su contenido**.
Esto provocaba que el sistema se quedara sin abstract en portugués, obligando a Gemini a intentar reconstruirlo y originando las discrepancias.

## Solución Propuesta

### 1. Modificar `main.py`
Actualizaremos el bloque que procesa el "Portuguese Abstract":
```python
        # Portuguese Abstract (Resumo/Abstrato)
        if ("introducao" in txt_clean or "abstrato" in txt_clean or "resumo" in txt_clean) and sum(1 for kw in ["objetivo", "metodologia", "resultados", "conclusoes", "conclusao"] if kw in txt_clean) >= 3:
            clean_txt = re.sub(r'^(?:Resumo|Resumo:|Abstrato|Abstrato:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if len(clean_txt) > 50:
                metadata.abstract_pt = format_abstract_text(clean_txt)
                p.decompose()
                continue
```
Esto asegurará que cualquier artículo que contenga un resumen portugués en su texto original (DOCX) lo conserve exactamente como el autor lo redactó.

### 2. Limpiar `fix_all_sanus_expert_rules.py`
Eliminaré el código que implementamos antes que "forzaba" la versión del experto mediante la variable `sections_data_566`. Al hacer esto, permitiremos que el pipeline fluya de manera nativa desde el DOCX original hasta el XML final, y esto solucionará el problema **para todos los artículos del proyecto**, no solo para el 566.

> [!IMPORTANT]
> **Aprobación de la regla general:**
> Al aplicar esta extracción dinámica, el texto resultante en el XML final será la **copia exacta y literal del DOCX**, ignorando cualquier ajuste parafraseado que haya hecho el experto (que rompió la regla de conservar el original). ¿Procedo a ejecutar este enfoque?
