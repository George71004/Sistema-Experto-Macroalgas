# Sistema Experto Ficológico (Macroalgas de la Isla de Margarita)

Este proyecto consiste en un **Sistema Experto Avanzado** diseñado bajo la **Metodología de Buchanan** para la identificación taxonómica sistemática de macroalgas intermareales (Phyla: *Chlorophyta*, *Heterokontophyta* y *Rhodophyta*) recolectadas en Playa La Caracola y Playa Valdez, Isla de Margarita, Venezuela.

---

## 📋 ¿Qué hace y cómo funciona?

El sistema funciona como un asistente inteligente por línea de comandos que guía a un biólogo o investigador de campo a través de preguntas dicotómicas sucesivas para clasificar especímenes botánicos:

1. **Base de Conocimiento Declarativa (`algae_knowledge.json`)**: Contiene la ontología estructurada en forma de Grafo Dirigido Acíclico (DAG). Divide las especies en tres grandes bloques macro-evolutivos (Verdes, Pardas y Rojas) para agilizar el diagnóstico.
2. **Motor de Inferencia Recursivo (`expert_algas.py`)**: Evalúa las características morfológicas ingresadas. Posee soporte integrado de **backtracking recursivo** en ramas paralelas cuando el usuario desconoce una característica (entrada `D`), mostrando en pantalla cómo se duplica el razonamiento lógico.
3. **Sistema de Mantenimiento de Verdad (JTMS)**: Verifica la consistencia anatómica en tiempo real para evitar que se asuman caracteres contradictorios (por ejemplo, poseer estructura celular cenocítica y al mismo tiempo talo laminar celular).
4. **Filtros Ambientales**: Permite pre-filtrar las especies candidatas mediante coeficientes probabilísticos de temperatura superficial del agua, salinidad, estación y mes de colecta específicos del ecosistema de Margarita.
5. **Trazabilidad**: Imprime la conclusión taxonómica final acompañada de la ruta detallada de razonamiento y el estado de justificación de cada opción tomada.

---

## 🛠️ Requisitos e Instalación

Este proyecto ha sido optimizado para ejecutarse de forma nativa en la consola con la biblioteca estándar de Python, minimizando el uso de dependencias externas pesadas.

### Dependencias y Librerías:
*   **Python**: Versión 3.8 o superior.
*   **Librerías externas**: Ninguna requerida (se ejecuta exclusivamente con módulos nativos como `json`, `os`, `sys`).

---

## 🚀 Comandos de Ejecución

Todos los comandos deben ejecutarse desde la terminal dentro de la carpeta del proyecto:

### 1. Inicializar/Compilar la Base de Conocimiento
Si el archivo `algae_knowledge.json` no existe o desea restaurarlo a su estado por defecto con el catálogo sistemático y el árbol de Rhodophyta:
```bash
python3 generar_json_prueba.py
```

### 2. Ejecutar el Diagnóstico Interactivo
Para iniciar el sistema experto interactivo en la línea de comandos:
```bash
python3 expert_algas.py
```
*   **Instrucciones**: Responda con `S` (Sí), `N` (No) o `D` (Desconocido). Si ingresa `D`, verá cómo la terminal inicia búsquedas paralelas.

### 3. Ejecutar la Suite de Calibración (Test Cuantitativo)
Para ejecutar la calibración automatizada del motor sobre las 30 muestras físicas de herbario y obtener la exactitud global, sensibilidad y especificidad:
```bash
python3 expert_algas.py --calibration
```

### 4. Ejecutar la API HTTP
Para exponer la lógica del sistema experto por endpoints JSON:
```bash
python3 api_server.py
```
Luego puedes probar:
```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/diagnosis/start -H "Content-Type: application/json" -d '{"session_id":"demo"}'
curl -X POST http://127.0.0.1:8000/api/diagnosis/answer -H "Content-Type: application/json" -d '{"session_id":"demo","character_name":"color_verde_no_calc","answer":"S"}'
curl "http://127.0.0.1:8000/api/diagnosis/state?session_id=demo"
```

---

## 🗺️ Próximos Pasos (Lo que falta para terminar el sistema)

Para elevar este prototipo a un software de producción ficológica completo, se identifican las siguientes áreas de desarrollo:

1. **Completitud del Catálogo (72 especies)**:
   *   Actualmente, el archivo `algae_knowledge.json` tiene implementadas las bifurcaciones lógicas detalladas y fichas para aproximadamente 40 especies principales del catálogo de Margarita (incluyendo los taxones clave como *Jania adhaerens*, *Cottoniella filamentosa*, *Caulerpa scalpelliformis*, *C. mexicana*, y géneros representativos como *Sargassum*, *Dictyota*, *Ulva*, *Hypnea* y *Gracilaria*).
   *   **Falta**: Alimentar y codificar las preguntas diagnósticas finas y descripciones botánicas de las 32 especies restantes del inventario de la tesis.
2. **Interfaz de Gestión de Conocimiento (Knowledge Editor)**:
   *   **Falta**: Crear un módulo CLI administrativo (`knowledge_editor.py`) que permita a los ingenieros de conocimiento agregar, modificar o eliminar nodos de transición y especies del JSON de forma visual y guiada en consola, sin riesgo de romper el formato sintáctico del grafo.
3. **Módulo de Explicación de Inferencia Avanzado (Explainable AI - XAI)**:
   *   **Falta**: Implementar comandos del sistema durante el interrogatorio como `WHY` (¿Por qué se me pregunta esto?) para ver qué hipótesis activas del JTMS están en juego, y `HOW <Especie>` (¿Cómo se llegó a este descarte?) para desplegar explicaciones botánicas estructuradas de los desvíos lógicos.
4. **Base de Datos Ambiental Ampliada**:
   *   **Falta**: Enriquecer los perfiles ambientales de los especímenes (`env_profile`) con registros de temperatura superficial del agua y salinidad de todo un año hidrológico continuo en las bahías de Margarita, optimizando la precisión de la confianza de clasificación bajo fuerte degradación física de la muestra.
