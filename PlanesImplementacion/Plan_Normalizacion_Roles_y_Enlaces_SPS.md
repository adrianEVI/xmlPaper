# Plan de Implementación: Normalización de Roles y Uniformidad SciELO SPS en Bibliografía

Se establecen las reglas de normalización para la capitalización uniforme de grados académicos en los roles de autores y la estandarización estricta de atributos `xlink:href` en los enlaces bibliográficos y DOIs según SciELO SPS.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Principales de Acción:**
> 1. **Uniformidad de Grado Académico (`<role>`):**
>    - Normalizar la capitalización del rol `"Doctorado en Metodología de la enseñanza"` a `"Doctorado en Metodología de la Enseñanza"` en todos los autores para garantizar consistencia editorial 100% uniforme.
> 2. **Estandarización de Atributos en Enlaces Bibliográficos (`<ext-link>`):**
>    - Asegurar que todo nodo `<ext-link>` utilice exclusivamente el atributo `xlink:href="..."` (reemplazando cualquier atributo local sin prefijo `href="..."`) conforme al estándar JATS/SciELO SPS.
> 3. **Normalización de DOIs y Abreviaturas:**
>    - Verificar que todo `<pub-id pub-id-type="doi">` mantenga el formato canónico `10.xxxx/...` y que los enlaces de las citas sean consistentes.

---

## Proposed Changes

### 1. Actualización de Reglas de Normalización (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Estandarizar la lista `roles_573` para usar `"Doctorado en Metodología de la Enseñanza"` uniformemente.
- Iterar sobre todos los elementos `<ext-link>` en `<ref>` y `<body>` para migrar cualquier `href` a `xlink:href`.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Roles Uniformes:**
   - Comprobar que en `573_ESP.xml` no exista ninguna ocurrencia con 'e' minúscula en `"Doctorado en Metodología de la enseñanza"`.
2. **Verificación de Atributos `xlink:href`:**
   - Comprobar que ningún nodo `<ext-link>` tenga el atributo `href` sin namespace.
