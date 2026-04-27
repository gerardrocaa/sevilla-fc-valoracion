# Briefing completo para generar las diapositivas del Sevilla FC

Este documento contiene toda la informacion necesaria para que un modelo de IA genere los JSONs de cada diapositiva de la presentacion "Valoracion Integral de Jugadores del Sevilla FC".

---

## 1. Contexto del proyecto

Caso practico de LaLiga sobre valoracion integral de jugadores del Sevilla FC, basado en datos reales de 6 partidos de LaLiga EA Sports 2024/2025. Se analizan los partidos del Sevilla contra los tres grandes (Barcelona, Atletico de Madrid y Real Madrid), todos con resultado adverso. El sistema combina rendimiento deportivo (tracking + eventing), datos fisicos y factores comerciales/mercado para valorar a cada jugador de forma multidimensional.

### Fuentes de datos

- **SkillCorner (Game Intelligence)**: 31.000 eventos de tracking con 310 variables por evento (posicion, presion, xThreat, carreras sin balon, pressing chains, opciones de pase). 6 partidos.
- **ESPN / Opta (Eventing)**: Eventos tecnicos clasicos (xG, xA, pases, tiros, tackles). 4 de los 6 partidos.
- **Datos fisicos agregados**: Distancia, sprints, HSR, PSV-99, aceleraciones, cambios de direccion, agilidad. 19 jugadores.

### Partidos analizados

| Partido | Fecha | Jornada | Resultado |
|---------|-------|---------|-----------|
| FC Barcelona vs Sevilla FC | 2024-10-20 | J10 | 5-1 |
| Atletico Madrid vs Sevilla FC | 2024-12-08 | J16 | 4-3 |
| Real Madrid vs Sevilla FC | 2024-12-22 | J18 | 4-2 |
| Sevilla FC vs FC Barcelona | 2025-02-09 | J23 | 1-4 |
| Sevilla FC vs Atletico Madrid | 2025-04-06 | J30 | 1-2 |
| Sevilla FC vs Real Madrid | 2025-05-18 | J37 | 0-2 |

Los 6 partidos fueron derrotas del Sevilla.

### Hallazgos principales del analisis

- **Top performers**: Adams (0.71) e Isaac Romero (0.69) lideran el scoring. Lukebakio es el mas regular con score estable en los 6 partidos.
- **Dos clusters de jugador**: Fisico-Ofensivo (Romero, Lukebakio, Ejuke, Carmona) frente a Retencion-Defensivo (Bade, Gudelj, Agoume, Sow).
- **Alertas de carga**: Bade, Sow y Romero en riesgo medio (caida de PSV-99, ACWR fuera de rango optimo).
- **Paradoja comercial**: Gudelj (3,1M seguidores) y Saul (2,9M) tienen alto impacto en RRSS pero los scores mas bajos del equipo.

### Dashboard construido

10 modulos de analisis interactivo:
1. Vista General y Rankings
2. Perfil Individual con radar de 6 dimensiones
3. Comparativa cara a cara entre jugadores
4. Evolucion por partido
5. Clustering de perfiles
6. Fatiga y riesgo de lesion
7. Escenarios What-If con simulacion Monte Carlo
8. Valoracion Integral (rendimiento + fisico + mercado + comercial + medico)
9. Analisis de pressing y acciones sin balon
10. KPIs de equipo por jornada

---

## 2. Identidad visual y branding

Todas las diapositivas deben seguir este sistema visual:

| Elemento | Valor |
|---|---|
| Background | `#0B0E14` (dark navy) |
| Primary | `#D4001E` (rojo Sevilla) |
| Secondary | `#FFFFFF` (blanco) |
| Accent | `#FF3344` (rojo brillante) |
| Fuente titulos | Montserrat |
| Fuente cuerpo | Inter |
| Color titulos | `#FFFFFF` |
| Color subtitulos | `#8B95A5` |
| Aspect ratio | 16:9 |

Coherencia visual: titulo siempre arriba a la izquierda, fondo oscuro uniforme, acentos de color en rojo Sevilla.

---

## 3. Reglas de texto para todas las diapositivas

Estas reglas son obligatorias en todo el texto visible de las slides:

1. **Acentos y tildes**: Todas las palabras en castellano deben llevar sus acentos correctos (valoracion → valoración, posicion → posición, fisico → físico, medico → médico, mas → más, direccion → dirección, lesion → lesión, prediccion → predicción, etc.).

2. **Nombres propios con acentos**: Badé, Agoumé, Saúl, Atlético, Barça.

3. **Sin guiones largos**: No usar guiones largos (—) como separadores. En su lugar, usar dos puntos (:), parentesis, o reformular la frase de forma natural.

4. **Texto natural**: Las frases deben sonar como lenguaje hablado, no como listas telegraficas. Usar articulos (el, la, los, las), preposiciones y conectores donde hagan falta.

5. **Puntuacion**: Punto al final de cada bloque de texto (detail). Signos de interrogacion y exclamacion de apertura y cierre en castellano (¿...?, ¡...!).

6. **Comas decimales**: En castellano se usa coma como separador decimal (3,1M, no 3.1M; 2,5 min, no 2.5 min).

---

## 4. Estructura JSON de referencia

Cada diapositiva sigue esta estructura base. Los campos del theme son siempre los mismos:

```json
{
  "slide_type": "cover | items | transition | closing",
  "meta": {
    "language": "es",
    "aspect_ratio": "16:9",
    "quality": "high"
  },
  "theme": {
    "style": "sevilla_fc_dark",
    "background_color": "#0B0E14",
    "primary_color": "#D4001E",
    "secondary_color": "#FFFFFF",
    "accent_color": "#FF3344",
    "font_family_headings": "Montserrat",
    "font_family_body": "Inter"
  },
  "content": {
    "title": "...",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "...",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Descripcion en ingles de la imagen de fondo para generacion con IA",
    "items": [
      {
        "identifier": "id_unico",
        "name": "Nombre del item",
        "tag": "Etiqueta corta",
        "detail": "Texto descriptivo con acentos, puntuacion y tono natural.",
        "color": "#hexcolor",
        "highlight": true/false,
        "icon": "nombre-icono-lucide"
      }
    ]
  }
}
```

Notas:
- `slide_type`: "cover" para portada, "items" para slides con contenido, "transition" para transiciones, "closing" para cierre.
- `visual_prompt`: Siempre en ingles, estilo cinematografico oscuro con acentos en rojo Sevilla.
- `highlight`: Solo un item por slide deberia tener `true` (el mas importante).
- `icon`: Usar nombres de iconos de Lucide Icons.
- Paleta de colores para items: `#D4001E` (rojo, item principal), `#3B82F6` (azul), `#8B5CF6` (morado), `#10B981` (verde), `#F59E0B` (amarillo), `#06B6D4` (cyan).

---

## 5. Distribucion de diapositivas

### Slide 1: Portada
- **Tipo**: cover
- **Titulo**: "Valoración Integral de Jugadores"
- **Subtitulo**: "Sevilla FC · LaLiga EA Sports 2024/2025"
- **Visual prompt**: Estadio de futbol cinematografico de noche con iluminacion roja dramatica, colores del Sevilla FC, minimalista y elegante, lineas geometricas abstractas que sugieren datos y analitica sobre el cesped, estilo profesional de presentacion deportiva, 16:9.
- **Items**: Ninguno (slide limpia, solo titulo y subtitulo).
- **Proposito**: Abrir la presentacion con impacto visual. Primera impresion profesional y seria.

---

### Slide 2: El Reto
- **Tipo**: items
- **Titulo**: "El Reto"
- **Subtitulo**: "6 partidos · 3 proveedores · 21 jugadores"
- **Visual prompt**: Fondo abstracto oscuro con lineas de cuadricula de datos sutiles y nodos de conexion en rojo, representando multiples fuentes de datos convergiendo, minimalista y limpio, estetica de analitica profesional.
- **Proposito**: Presentar la magnitud del reto, las fuentes de datos disponibles y el contexto deportivo (todas derrotas).
- **Items** (4):

| # | identifier | name | tag | detail | color | highlight | icon |
|---|---|---|---|---|---|---|---|
| 1 | skillcorner | SkillCorner (Game Intelligence) | Tracking | 31.000 eventos con 310 variables: posición, presión, xThreat, carreras sin balón y pressing chains. | #D4001E | true | radar |
| 2 | espn_opta | ESPN / Opta (Eventing) | Eventos | xG, xA, pases, tiros y tackles. Datos técnicos clásicos de 4 partidos. | #3B82F6 | false | clipboard-list |
| 3 | fisicos | Datos Físicos Agregados | Físico | Distancia, sprints, HSR, PSV-99, aceleraciones, cambios de dirección y agilidad. | #10B981 | false | activity |
| 4 | contexto | Contexto: 6 derrotas contra el Big 3 | Partidos | Barça (J10, J23) · Atlético (J16, J30) · Real Madrid (J18, J37). Todos resultados adversos para el Sevilla. | #F59E0B | false | calendar |

---

### Slide 3: Modelo de Análisis
- **Tipo**: items
- **Titulo**: "De Datos a Decisiones"
- **Subtitulo**: "Pipeline completo: dato crudo → insight accionable"
- **Visual prompt**: Fondo oscuro con un diagrama de flujo horizontal de cuatro nodos conectados brillando en rojo, fluyendo de izquierda a derecha como un pipeline de datos, estilo geometrico abstracto con lineas sutiles de circuito, estetica de analitica profesional, minimalista y limpio.
- **Proposito**: Explicar la metodologia general del proyecto, el pipeline de principio a fin. Vista de alto nivel.
- **Items** (4):

| # | identifier | name | tag | detail | color | highlight | icon |
|---|---|---|---|---|---|---|---|
| 1 | fase1 | Datos Crudos | Fase 1 | 31K eventos SkillCorner (310 vars), eventos ESPN/Opta (xG, xA), métricas físicas (sprints, HSR, PSV-99) de 6 partidos. | #3B82F6 | false | database |
| 2 | fase2 | Procesamiento | Fase 2 | Limpieza, normalización y feature extraction: de 310 columnas a 6 dimensiones de rendimiento por jugador y partido. | #8B5CF6 | false | filter |
| 3 | fase3 | Inteligencia | Fase 3 | Scoring multidimensional con pesos por posición, clustering de perfiles, predicción de fatiga y riesgo de lesión. | #D4001E | true | brain |
| 4 | fase4 | Decisión | Fase 4 | Dashboard interactivo con simulación What-If y valoración integral: rendimiento + físico + mercado + comercial + médico. | #10B981 | false | check-circle |

---

### Slide 4: El Viaje del Dato
- **Tipo**: items
- **Titulo**: "El Viaje del Dato"
- **Subtitulo**: "De dato crudo a decisión accionable"
- **Visual prompt**: Fondo oscuro con un diagrama de flujo horizontal de cuatro nodos conectados brillando en rojo, fluyendo de izquierda a derecha como un pipeline de datos, estilo geometrico abstracto con lineas sutiles de circuito, estetica de analitica profesional, minimalista y limpio.
- **Proposito**: Contar el recorrido del dato de forma simplificada y directa. Complementa la slide anterior con un enfoque mas narrativo.
- **Items** (4):

| # | identifier | name | tag | detail | color | highlight | icon |
|---|---|---|---|---|---|---|---|
| 1 | fase1 | Datos crudos | Fase 1 | 31K eventos + 310 variables + datos físicos. | #3B82F6 | false | database |
| 2 | fase2 | Procesamiento | Fase 2 | Limpieza, normalización, feature extraction por jugador/partido. | #8B5CF6 | false | filter |
| 3 | fase3 | Inteligencia | Fase 3 | Scoring, clustering, predicción de fatiga/riesgo. | #D4001E | true | brain |
| 4 | fase4 | Decisión | Fase 4 | Dashboard interactivo para directivos y analistas. | #10B981 | false | check-circle |

---

### Slide 5: Transición a Demo
- **Tipo**: transition
- **Titulo**: "Veámoslo en vivo"
- **Subtitulo**: "Dashboard interactivo con 10 módulos de análisis"
- **Visual prompt**: Fondo cinematografico oscuro con una pantalla de portatil brillando mostrando una interfaz de dashboard, resplandor rojo saliendo de la pantalla, iluminacion dramatica, profesional y minimalista, sugiriendo una demo en vivo de analitica de datos.
- **Proposito**: Slide puente antes de la demo en vivo del dashboard. Anticipa los modulos que se van a mostrar.
- **Items** (4):

| # | identifier | name | tag | detail | color | highlight | icon |
|---|---|---|---|---|---|---|---|
| 1 | modulo1 | Vista General y Rankings | Panorama | Ranking de jugadores, heatmap por jornada y KPIs de equipo. | #D4001E | true | bar-chart-2 |
| 2 | modulo2 | Perfiles y Comparativas | Individual | Radar de 6 dimensiones, evolución por partido y cara a cara entre jugadores. | #3B82F6 | false | user |
| 3 | modulo3 | Inferencia y Simulación | Predictivo | Clustering, fatiga, riesgo de lesión y escenarios What-If con Monte Carlo. | #8B5CF6 | false | brain |
| 4 | modulo4 | Valoración Integral | Decisión | Rendimiento, físico, mercado, comercial y médico en un único score. | #10B981 | false | star |

---

### Slide 6: Conclusiones
- **Tipo**: closing
- **Titulo**: "Conclusiones"
- **Subtitulo**: "De datos a decisiones"
- **Visual prompt**: Fondo elegante oscuro con lineas geometricas rojas sutiles convergiendo en un punto, sugiriendo toma de decisiones basada en datos, estetica profesional de slide de cierre, acentos en rojo Sevilla, minimalista e impactante.
- **Proposito**: Cerrar la presentacion con las 4 ideas fuerza del proyecto.
- **Items** (4):

| # | identifier | name | tag | detail | color | highlight | icon |
|---|---|---|---|---|---|---|---|
| 1 | C1 | La valoración integral supera a la unidimensional | Enfoque | Combinar 6 dimensiones de rendimiento con datos externos revela el valor real de cada jugador, no solo sus goles o pases. | #D4001E | true | layers |
| 2 | C2 | El tracking revela lo invisible | Datos | Las carreras sin balón, las pressing chains y las opciones de pase no aparecen en las estadísticas clásicas, pero definen el rendimiento. | #3B82F6 | false | eye |
| 3 | C3 | Gestión de carga es prevención | Salud | Monitorizar la fatiga, el ACWR y la caída de PSV-99 permite anticipar lesiones y optimizar rotaciones. | #10B981 | false | heart-pulse |
| 4 | C4 | Una herramienta replicable y escalable | Futuro | El modelo se puede aplicar a toda la plantilla, al mercado de fichajes y al scouting con más partidos y ligas. | #F59E0B | false | rocket |

---

## 6. Guia de presentacion

| Slide | Presentador | Tiempo |
|---|---|---|
| 1. Portada | Cualquiera | 30s |
| 2. El Reto | Presentador 1 | 2 min |
| 3. De Datos a Decisiones | Presentador 2 | 2,5 min |
| 4. El Viaje del Dato | Presentador 2 | 2,5 min |
| 5. Transición a Demo | Presentador 3 | 30s |
| DEMO EN VIVO | Presentador 3 | 6-7 min |
| 6. Conclusiones | Presentador 1 | 1,5 min |

### Ruta sugerida para la demo en vivo

1. **Vista General** → Mostrar el ranking en bar chart y el heatmap de jugadores por jornadas.
2. **Perfil Individual** → Seleccionar a Isaac Romero (top CF) y a Lukebakio (el más regular).
3. **Clustering** → Enseñar los 2 grupos y explicar qué los separa.
4. **Fatiga y Riesgo** → Señalar a Badé (fatigue 0,74 en J23) y a Sow (riesgo medio).
5. **What-If** → Simular en vivo: «¿Qué pasa si descansa Lukebakio un partido?»
6. **Valoración Integral** → Ranking final con las 5 capas.

---

## 7. Instrucciones para el modelo generador

Cuando generes cada JSON:

1. Copia el bloque `meta` y `theme` exactamente como aparece en la seccion 4 (son identicos en todas las slides).
2. Usa el `slide_type` indicado para cada diapositiva.
3. Escribe todo el texto visible en castellano con acentos correctos, sin guiones largos y con tono natural (ver seccion 3).
4. El `visual_prompt` va siempre en ingles.
5. Solo un item por slide debe tener `"highlight": true`.
6. Respeta los colores, iconos e identifiers exactos de las tablas de la seccion 5.
7. Cada campo `detail` debe terminar en punto.
