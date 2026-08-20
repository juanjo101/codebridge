Quiero que integres de forma completa capacidades de **Ciberseguridad, Application Security, Quality Assurance y generación automática de pruebas** dentro de CodeBridge.

Trabaja sobre el repositorio actual de CodeBridge y **respeta estrictamente la arquitectura existente**, especialmente el sistema de skills ubicado en:

`.agents/skills/`

Antes de modificar código:

1. Inspecciona completamente la estructura actual del proyecto.
2. Lee `AGENTS.md`.
3. Analiza las skills existentes dentro de `.agents/skills/`.
4. Reutiliza los patrones, convenciones, nombres, frontmatter, estructura de carpetas y mecanismos de activación ya utilizados por CodeBridge.
5. No inventes una arquitectura paralela si la funcionalidad puede integrarse en la arquitectura existente.
6. No elimines ni rompas ninguna funcionalidad existente.
7. No introduzcas dependencias innecesarias.
8. Toda nueva funcionalidad debe ser modular, extensible y compatible con futuras skills.

## Objetivo general

Convertir CodeBridge en un agente de desarrollo capaz de actuar también como:

- Software Developer
- QA Engineer
- Test Engineer
- Application Security Engineer
- Secure Code Reviewer
- Security Auditor

CodeBridge debe poder analizar un proyecto, desarrollar código, generar pruebas, ejecutar validaciones, encontrar vulnerabilidades, recomendar correcciones, aplicar correcciones cuando el usuario lo autorice y volver a ejecutar las pruebas para comprobar que el problema fue resuelto.

## Skills nuevas obligatorias

Crea como mínimo las siguientes skills:

```text
.agents/skills/
├── codebridge-security/
│   ├── SKILL.md
│   └── references/
│
├── codebridge-security-scan/
│   ├── SKILL.md
│   └── references/
│
├── codebridge-qa/
│   ├── SKILL.md
│   └── references/
│
└── codebridge-test-generator/
    ├── SKILL.md
    └── references/
```

Si después de analizar la arquitectura existente determinas que algún nombre debe ajustarse para mantener consistencia con CodeBridge, puedes hacerlo, pero conserva exactamente estas cuatro responsabilidades funcionales.

# 1. Skill: codebridge-security

Esta skill debe funcionar como especialista en **Application Security y Secure Coding**.

Debe revisar código fuente, configuraciones, APIs, autenticación, autorización, dependencias y arquitectura.

Debe detectar como mínimo:

- SQL Injection
- Command Injection
- Code Injection
- Cross-Site Scripting / XSS
- CSRF
- SSRF
- Path Traversal
- Directory Traversal
- Insecure File Upload
- IDOR / Broken Object Level Authorization
- Broken Access Control
- autenticación insegura
- autorización incorrecta
- sesiones inseguras
- JWT mal implementados
- almacenamiento inseguro de passwords
- hashing débil
- criptografía insegura
- secretos hardcoded
- API keys expuestas
- tokens expuestos
- credenciales en código
- configuración insegura
- CORS inseguro
- headers de seguridad ausentes
- validación insuficiente de entradas
- deserialización insegura
- logging de datos sensibles
- exposición de información
- manejo inseguro de excepciones
- uso inseguro de funciones del sistema
- dependencias vulnerables
- riesgos derivados de componentes desactualizados

Utiliza como referencias conceptuales:

- OWASP Top 10
- OWASP API Security Top 10
- CWE
- principios Secure by Design
- Least Privilege
- Defense in Depth
- Zero Trust cuando sea relevante

Cada vulnerabilidad encontrada debe incluir:

```text
Severidad:
Categoría:
OWASP:
CWE:
Archivo:
Línea o rango:
Descripción:
Evidencia:
Impacto:
Probabilidad:
Recomendación:
Ejemplo de corrección:
```

Utiliza severidades:

- Critical
- High
- Medium
- Low
- Informational

Nunca marques una vulnerabilidad como confirmada si solo existe una sospecha.

Diferencia claramente entre:

- Confirmed
- Probable
- Potential
- Informational

No inventes vulnerabilidades.

# 2. Skill: codebridge-security-scan

Esta skill debe orquestar análisis automático de seguridad utilizando herramientas reales cuando estén disponibles.

Debe detectar automáticamente el stack tecnológico del proyecto y seleccionar las herramientas correspondientes.

Soporta inicialmente:

### Análisis estático / SAST

- Semgrep
- Bandit para Python

### Dependencias

- pip-audit
- npm audit

Cuando sea apropiado contempla también ecosistemas adicionales sin hacerlos dependencias obligatorias.

### Secret Detection

- Gitleaks

### Dynamic Application Security Testing

Permitir integración con:

- OWASP ZAP

IMPORTANTE:

Las pruebas dinámicas, escaneo activo, fuzzing o cualquier prueba contra aplicaciones en ejecución solo deben ejecutarse cuando:

- el objetivo pertenezca al usuario;
- sea un entorno de desarrollo o pruebas;
- o exista autorización expresa.

Por defecto utiliza análisis pasivo y seguro.

Nunca lances ataques destructivos.

Nunca realices acciones de explotación fuera del entorno autorizado.

## Flujo de seguridad

Implementa conceptualmente:

```text
Project Discovery
       ↓
Technology Detection
       ↓
Security Review
       ↓
SAST
       ↓
Dependency Scan
       ↓
Secret Detection
       ↓
Configuration Review
       ↓
DAST si está autorizado
       ↓
Consolidation
       ↓
Security Report
```

Los resultados provenientes de herramientas distintas deben consolidarse y eliminar duplicados.

## Security Score

Genera cuando sea posible una puntuación:

```text
Security Score: XX/100
```

La puntuación debe basarse en hallazgos reales y explicar brevemente el criterio utilizado.

No generes una puntuación arbitraria.

# 3. Skill: codebridge-qa

Debe actuar como **Senior QA Engineer**.

Debe analizar:

- requerimientos
- código
- arquitectura
- APIs
- componentes
- interfaces
- flujos de usuario
- validaciones
- manejo de errores

Debe producir una estrategia de pruebas adaptada al proyecto.

Debe contemplar:

- Unit Tests
- Integration Tests
- Functional Tests
- API Tests
- End-to-End Tests
- Regression Tests
- Smoke Tests
- Edge Cases
- Negative Testing
- Boundary Testing
- Input Validation
- Error Handling
- Concurrency Testing cuando corresponda
- Performance Testing cuando corresponda

Debe identificar automáticamente:

- qué debe probarse;
- qué partes son críticas;
- qué pruebas faltan;
- qué código tiene riesgo de regresión;
- qué comportamientos no están cubiertos.

No generes tests inútiles únicamente para aumentar cobertura.

Prioriza comportamiento y riesgo.

# 4. Skill: codebridge-test-generator

Debe convertir la estrategia de QA en pruebas ejecutables.

Debe detectar automáticamente el lenguaje y framework.

Como mínimo soporta:

### Python

- pytest
- unittest

### JavaScript / TypeScript

- Jest
- Vitest

### Web / E2E

- Playwright

Cuando el proyecto utilice otro framework existente, reutilízalo antes de introducir uno nuevo.

Nunca agregues dos frameworks equivalentes innecesariamente.

Ejemplo:

Si el proyecto ya utiliza pytest, continúa usando pytest.

Si ya utiliza Jest, no instales Vitest sin una razón técnica clara.

## Tests generados

Los tests deben:

- ser deterministas;
- ser repetibles;
- no depender de Internet salvo que sea indispensable;
- aislar servicios externos mediante mocks cuando corresponda;
- utilizar fixtures;
- limpiar recursos temporales;
- cubrir casos positivos y negativos;
- incluir edge cases relevantes;
- tener nombres descriptivos.

# Integración QA + Security + Development

Estas capacidades no deben funcionar aisladas.

Implementa un flujo integrado:

```text
Development
    ↓
Static Validation
    ↓
QA Analysis
    ↓
Test Generation
    ↓
Test Execution
    ↓
Security Review
    ↓
Security Scan
    ↓
Findings
    ↓
Suggested Fixes
    ↓
Fix
    ↓
Regression Tests
    ↓
Security Re-scan
```

Debe ser posible que CodeBridge ejecute un ciclo:

```text
detect → explain → fix → test → rescan
```

No apliques automáticamente cambios de seguridad destructivos o arquitectónicos sin autorización explícita.

# Comando unificado de auditoría

Integra una operación de alto nivel equivalente a:

```bash
cbm audit
```

Si la CLI existente utiliza otro patrón, intégralo respetando la arquitectura actual.

El objetivo es permitir algo equivalente a:

```text
Audit project
```

y ejecutar:

```text
Project Map
Code Quality
Unit Tests
Integration Tests
Test Coverage
Dependency Audit
Secret Detection
SAST
OWASP Review
Security Findings
QA Findings
Recommendations
```

Salida esperada:

```text
CODEBRIDGE AUDIT

Project:
Stack:

QUALITY
Quality Score: 92/100
Tests: 145 passed / 3 failed
Coverage: 84%

SECURITY
Security Score: 88/100

Critical: 0
High: 1
Medium: 4
Low: 7

DEPENDENCIES
Vulnerable dependencies: 2

SECRETS
Detected secrets: 0

RECOMMENDATIONS
1.
2.
3.
```

# Comandos o intenciones que CodeBridge debe reconocer

Las skills deben activarse ante solicitudes naturales como:

```text
Revisa la seguridad de este proyecto.
Haz un security audit.
Busca vulnerabilidades.
Haz un análisis OWASP.
Revisa si esta API es segura.
Haz un pentest seguro de esta aplicación local.
Analiza las dependencias.
Busca secretos expuestos.
Revisa este código desde el punto de vista de seguridad.
```

Para QA:

```text
Prueba este proyecto.
Haz QA de esta aplicación.
Genera las pruebas.
Busca bugs.
Genera unit tests.
Genera integration tests.
Haz pruebas E2E.
Revisa los edge cases.
Evalúa la cobertura.
Haz regression testing.
```

Y una solicitud:

```text
Audita completamente este proyecto.
```

debe combinar QA + Security.

# Herramientas

Antes de integrar cada herramienta:

1. Comprueba si ya está instalada.
2. Comprueba si ya existe una dependencia equivalente.
3. No rompas compatibilidad multiplataforma.
4. Maneja correctamente cuando la herramienta no esté instalada.
5. No hagas que CodeBridge falle completamente porque falte una herramienta opcional.

Ejemplo:

```text
Semgrep unavailable → skip + report
Bandit available → execute
Gitleaks unavailable → skip + installation recommendation
```

No instales herramientas globalmente sin necesidad.

Cuando corresponda, añade dependencias opcionales o instrucciones de instalación.

# Ejecución segura de comandos

Toda ejecución externa debe:

- utilizar subprocess de forma segura;
- evitar `shell=True` salvo justificación excepcional;
- sanitizar argumentos;
- utilizar timeout;
- capturar stdout;
- capturar stderr;
- capturar código de salida;
- manejar ejecutables inexistentes;
- evitar command injection.

No permitas que contenido controlado por un proyecto termine ejecutándose directamente como comando del sistema.

# Reporting

Crea un modelo común de hallazgos.

Idealmente:

```python
Finding(
    id,
    category,
    severity,
    title,
    description,
    file,
    line,
    source,
    cwe,
    owasp,
    confidence,
    recommendation
)
```

El formato interno puede variar si CodeBridge ya posee una abstracción equivalente.

No dupliques modelos existentes.

Los reportes deben poder producirse al menos en:

```text
terminal
Markdown
JSON
```

si la arquitectura actual lo permite sin complejidad excesiva.

# Priorización

Ordena los hallazgos por:

```text
Critical
High
Medium
Low
Informational
```

Dentro de una misma severidad prioriza:

1. probabilidad de explotación;
2. impacto;
3. facilidad de remediación.

# Fixes automáticos

Cuando el usuario solicite corregir vulnerabilidades:

1. explica el hallazgo;
2. identifica la causa;
3. propone el cambio;
4. aplica la corrección;
5. ejecuta tests;
6. vuelve a ejecutar el análisis afectado;
7. confirma si el hallazgo desapareció.

Nunca declares resuelto un problema únicamente porque modificaste el código.

Debe pasar la validación posterior.

# QA Gate

Implementa conceptualmente un Quality Gate.

Ejemplo:

```text
PASS
WARN
FAIL
```

Puede considerar:

```text
tests
coverage
security findings
critical bugs
dependency vulnerabilities
```

Por defecto:

```text
Critical security vulnerability → FAIL
Failed essential tests → FAIL
High vulnerability → WARN/FAIL según contexto
Medium → WARN
Low → INFO
```

Haz que estos criterios sean configurables.

# CI/CD

Prepara la arquitectura para permitir posteriormente integración con GitHub Actions.

No obligues todavía a activar CI si no existe.

Si es razonable, crea un workflow opcional de ejemplo que pueda ejecutar:

```text
tests
security scan
dependency audit
secret scan
```

pero no introduzcas secretos ni credenciales.

# Documentación

Actualiza la documentación de CodeBridge.

Debe incluir:

```text
Security capabilities
QA capabilities
Supported tools
Installation
Usage examples
Audit examples
Safety constraints
Known limitations
```

Actualiza cuando corresponda:

- `README.md`
- `README_ES.md`
- `README_EN.md`

Evita duplicación innecesaria.

# Testing de la propia integración

Debes crear pruebas para las nuevas funcionalidades.

Como mínimo:

- detección del stack;
- selección de scanners;
- parser de resultados;
- normalización de findings;
- cálculo de severidad;
- comportamiento cuando una herramienta no existe;
- generación de reportes;
- activación de skills;
- generación de tests;
- flujo audit.

Los tests NO deben depender de tener Semgrep, ZAP o Gitleaks realmente instalados.

Utiliza mocks para las pruebas unitarias.

# Compatibilidad

No rompas:

- CLI existente;
- MCP;
- configuración actual de agentes;
- skills existentes;
- modelos NVIDIA;
- manejo de contexto;
- historial;
- project map;
- tests actuales.

Todos los tests existentes deben continuar pasando.

# Criterios de aceptación

No consideres terminada la tarea hasta cumplir:

```text
[ ] Skills Security creadas
[ ] Skills QA creadas
[ ] OWASP integrado conceptualmente
[ ] CWE soportado
[ ] Semgrep soportado
[ ] Bandit soportado
[ ] pip-audit soportado
[ ] npm audit soportado
[ ] Gitleaks soportado
[ ] OWASP ZAP preparado para uso autorizado
[ ] QA strategy implementada
[ ] Test generation implementado
[ ] pytest soportado
[ ] Jest/Vitest soportado
[ ] Playwright soportado
[ ] Findings normalizados
[ ] Security report implementado
[ ] QA report implementado
[ ] Audit combinado implementado
[ ] Manejo de herramientas ausentes implementado
[ ] Tests nuevos creados
[ ] Tests existentes pasan
[ ] Documentación actualizada
[ ] No hay regresiones conocidas
```

# Forma de trabajo

No hagas una implementación superficial.

Primero analiza el sistema existente.

Después presenta brevemente:

```text
CURRENT ARCHITECTURE
INTEGRATION PLAN
FILES TO CREATE
FILES TO MODIFY
DEPENDENCIES
RISKS
```

Luego implementa.

Después ejecuta las pruebas.

Después revisa tu propio código.

Después corrige cualquier fallo.

Finalmente entrega:

```text
IMPLEMENTATION SUMMARY
FILES CREATED
FILES MODIFIED
TEST RESULTS
SECURITY CAPABILITIES
QA CAPABILITIES
KNOWN LIMITATIONS
RECOMMENDED NEXT STEPS
```

# Restricciones importantes

No:

- elimines funciones existentes;
- cambies APIs públicas sin necesidad;
- hardcodees rutas;
- hardcodees secretos;
- generes falsos positivos deliberadamente;
- declares vulnerabilidades sin evidencia;
- ejecutes explotación ofensiva contra objetivos externos;
- hagas pentesting activo sin autorización;
- uses comandos destructivos;
- desactives tests para lograr que el build pase;
- ocultes errores;
- ignores excepciones silenciosamente.

Si detectas un conflicto entre esta instrucción y la arquitectura real de CodeBridge, **prioriza preservar la arquitectura y compatibilidad existente**, documenta el conflicto y realiza la solución técnicamente más limpia.

El resultado final debe hacer que CodeBridge pueda comportarse como un verdadero **Developer + QA Engineer + Application Security Engineer**, no simplemente como un LLM que da recomendaciones generales.