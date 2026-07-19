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

Este proyecto está dividido en un Backend (Python/FastAPI) y un Frontend (Next.js/React).

### Requisitos del Backend:
*   **Python**: Versión 3.8 o superior.
*   **Instalación de Dependencias**: 
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Linux/macOS
    pip install -r requirements.txt
    ```

### Requisitos del Frontend:
*   **Node.js**: Versión 18.0 o superior.
*   **Instalación de Dependencias**:
    ```bash
    cd Frontend
    npm install
    ```

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

### 5. Ejecutar el Editor de Base de Conocimiento (Knowledge Editor)
Para administrar de forma guiada el árbol dicotómico y las especies del archivo JSON (validando ciclos, referencias rotas y huérfanos):
```bash
python3 knowledge_editor.py
```

### 6. Ejecutar la Interfaz Gráfica (Next.js Frontend)
Para levantar el servidor de desarrollo de la interfaz de usuario web:
```bash
cd Frontend
npm run dev
```

---

## 🛠️ Estado del Proyecto e Hitos Completados

El prototipo original fue elevado a un software de producción ficológica completo, resolviendo todos los hitos pendientes bajo la **Metodología de Buchanan**:

1. **Catálogo Completo y Conectado (74 Especies)**: Se digitalizaron y enlazaron al árbol binario de preguntas el 100% de las especies del catálogo de la tesis (15 *Chlorophyta*, 21 *Heterokontophyta* y 38 *Rhodophyta*), asegurando que todas sean diagnosticables desde el nodo raíz.
2. **Editor de Conocimiento (`knowledge_editor.py`)**: Se desarrolló una herramienta interactiva para que los ingenieros de conocimiento y biólogos modifiquen el árbol y las especies de manera visual y guiada, previniendo errores de formato y comprobando la integridad lógica (detección de bucles, referencias rotas y huérfanos).
3. **Módulo de Explicación de Inferencia (Explainable AI - XAI)**: La interfaz web ahora incluye un panel interactivo que explica el porqué de cada pregunta ("¿Por qué se realiza esta pregunta?") mostrando qué especies se descartan o seleccionan con las respuestas. Además, justifica la especie final detallando cada carácter asumido por el JTMS.
4. **Módulo de Retractación (Deshacer)**: Permite al usuario retroceder en las preguntas del diagnóstico y corregir respuestas previas tanto a nivel de API como en la UI, interactuando directamente con el motor de mantenimiento de verdad.
5. **Mapeo de Filtros Ambientales**: Se añadieron selectores y deslizadores en el frontend para configurar la temperatura, salinidad, estación y mes de muestreo antes del diagnóstico, interactuando con los coeficientes de confianza del backend.
6. **Mapeo de Contradicciones (JTMS)**: En caso de inconsistencias anatómicas ingresadas por el usuario, el JTMS las captura y la interfaz web presenta una pantalla detallando la contradicción ficológica exacta y los caracteres en conflicto.
7. **Módulo de Ilustración Taxonómica (100% Cobertura de Imágenes)**: Se integró un panel visual que presenta al usuario una fotografía científica de la especie clasificada en la pantalla de resultados del diagnóstico. Este módulo utiliza un proxy en el backend (`/api/species-image`) que consulta de forma dinámica resúmenes de Wikipedia (con caché en memoria) y hace fallback inteligente a un banco local de 26 imágenes curadas para aquellas especies o géneros que carecen de material gráfico público.
