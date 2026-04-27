# Presentación Sevilla FC: Slides para NanoBanana

## Branding

| Elemento | Valor |
|---|---|
| Background | `#0B0E14` (dark navy) |
| Primary | `#D4001E` (Sevilla red) |
| Secondary | `#FFFFFF` (white) |
| Accent | `#FF3344` (bright red) |
| Headings | Montserrat |
| Body | Inter |
| Title color | `#FFFFFF` |
| Subtitle color | `#8B95A5` |
| Aspect ratio | 16:9 |

Coherencia visual: título siempre arriba a la izquierda, fondo oscuro uniforme, acentos en rojo Sevilla.

---

## Slide 1: Portada

```json
{
  "slide_type": "cover",
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
    "title": "Valoración Integral de Jugadores",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "Sevilla FC · LaLiga EA Sports 2024/2025",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Dark cinematic football stadium at night with dramatic red lighting, Sevilla FC colors, minimal and elegant, abstract geometric lines suggesting data and analytics overlaid on the pitch, professional sports presentation style, 16:9 widescreen",
    "items": []
  }
}
```

---

## Slide 2: El Reto

```json
{
  "slide_type": "items",
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
    "title": "El Reto",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "6 partidos · 3 proveedores · 21 jugadores",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Abstract dark background with subtle data grid lines and connection nodes in red, representing multiple data sources converging, minimal and clean, professional analytics aesthetic",
    "items": [
      {
        "identifier": "skillcorner",
        "name": "SkillCorner (Game Intelligence)",
        "tag": "Tracking",
        "detail": "31.000 eventos con 310 variables: posición, presión, xThreat, carreras sin balón y pressing chains.",
        "color": "#D4001E",
        "highlight": true,
        "icon": "radar"
      },
      {
        "identifier": "espn_opta",
        "name": "ESPN / Opta (Eventing)",
        "tag": "Eventos",
        "detail": "xG, xA, pases, tiros y tackles. Datos técnicos clásicos de 4 partidos.",
        "color": "#3B82F6",
        "highlight": false,
        "icon": "clipboard-list"
      },
      {
        "identifier": "fisicos",
        "name": "Datos Físicos Agregados",
        "tag": "Físico",
        "detail": "Distancia, sprints, HSR, PSV-99, aceleraciones, cambios de dirección y agilidad.",
        "color": "#10B981",
        "highlight": false,
        "icon": "activity"
      },
      {
        "identifier": "contexto",
        "name": "Contexto: 6 derrotas contra el Big 3",
        "tag": "Partidos",
        "detail": "Barça (J10, J23) · Atlético (J16, J30) · Real Madrid (J18, J37). Todos resultados adversos para el Sevilla.",
        "color": "#F59E0B",
        "highlight": false,
        "icon": "calendar"
      }
    ]
  }
}
```

---

## Slide 3: De Datos a Decisiones

```json
{
  "slide_type": "items",
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
    "title": "De Datos a Decisiones",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "Pipeline completo: dato crudo → insight accionable",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Dark background with a horizontal flow diagram made of four glowing connected nodes in red, flowing left to right like a data pipeline, abstract geometric style with subtle circuit-board lines, professional analytics aesthetic, minimal and clean",
    "items": [
      {
        "identifier": "fase1",
        "name": "Datos Crudos",
        "tag": "Fase 1",
        "detail": "31K eventos de SkillCorner (310 variables), eventos ESPN/Opta (xG, xA) y métricas físicas (sprints, HSR, PSV-99) de 6 partidos.",
        "color": "#3B82F6",
        "highlight": false,
        "icon": "database"
      },
      {
        "identifier": "fase2",
        "name": "Procesamiento",
        "tag": "Fase 2",
        "detail": "Limpieza, normalización y extracción de features: de 310 columnas a 6 dimensiones de rendimiento por jugador y partido.",
        "color": "#8B5CF6",
        "highlight": false,
        "icon": "filter"
      },
      {
        "identifier": "fase3",
        "name": "Inteligencia",
        "tag": "Fase 3",
        "detail": "Scoring multidimensional con pesos por posición, clustering de perfiles, predicción de fatiga y riesgo de lesión.",
        "color": "#D4001E",
        "highlight": true,
        "icon": "brain"
      },
      {
        "identifier": "fase4",
        "name": "Decisión",
        "tag": "Fase 4",
        "detail": "Dashboard interactivo con simulación What-If y valoración integral: rendimiento, físico, mercado, comercial y médico.",
        "color": "#10B981",
        "highlight": false,
        "icon": "check-circle"
      }
    ]
  }
}
```

---

## Slide 4: Hallazgos Clave

```json
{
  "slide_type": "items",
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
    "title": "Hallazgos Clave",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "Patrones detectados en 6 partidos de LaLiga 2024/2025",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Dark background with four glowing insight cards arranged in a grid, each with a subtle red accent border, professional dashboard analytics style, clean and impactful",
    "items": [
      {
        "identifier": "top",
        "name": "Top Performers",
        "tag": "Rendimiento",
        "detail": "Adams (0.71) e Isaac Romero (0.69) lideran el scoring. Lukebakio es el más regular, con score estable en los 6 partidos.",
        "color": "#D4001E",
        "highlight": true,
        "icon": "trophy"
      },
      {
        "identifier": "clusters",
        "name": "Dos perfiles de jugador",
        "tag": "Clustering",
        "detail": "Cluster Físico-Ofensivo (Romero, Lukebakio, Ejuke, Carmona) frente a Cluster Retención-Defensivo (Badé, Gudelj, Agoumé, Sow).",
        "color": "#8B5CF6",
        "highlight": false,
        "icon": "git-branch"
      },
      {
        "identifier": "riesgo",
        "name": "Alertas de Carga",
        "tag": "Riesgo",
        "detail": "Badé, Sow y Romero en riesgo medio: caída de PSV-99, ACWR fuera de rango óptimo y fatiga acumulada creciente.",
        "color": "#F59E0B",
        "highlight": false,
        "icon": "alert-triangle"
      },
      {
        "identifier": "comercial",
        "name": "Valor Comercial frente a Rendimiento",
        "tag": "Paradoja",
        "detail": "Gudelj (3,1M seguidores) y Saúl (2,9M) tienen alto impacto en RRSS, pero obtienen los scores más bajos del equipo.",
        "color": "#06B6D4",
        "highlight": false,
        "icon": "trending-down"
      }
    ]
  }
}
```

---

## Slide 5: Transición a Demo

```json
{
  "slide_type": "transition",
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
    "title": "Veámoslo en vivo",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "Dashboard interactivo con 10 módulos de análisis",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Dark cinematic background with a glowing laptop screen showing a dashboard interface, red accent glow emanating from the screen, dramatic lighting, professional and minimal, suggesting live data analytics demo",
    "items": [
      {
        "identifier": "modulo1",
        "name": "Vista General y Rankings",
        "tag": "Panorama",
        "detail": "Ranking de jugadores, heatmap por jornada y KPIs de equipo.",
        "color": "#D4001E",
        "highlight": true,
        "icon": "bar-chart-2"
      },
      {
        "identifier": "modulo2",
        "name": "Perfiles y Comparativas",
        "tag": "Individual",
        "detail": "Radar de 6 dimensiones, evolución por partido y cara a cara entre jugadores.",
        "color": "#3B82F6",
        "highlight": false,
        "icon": "user"
      },
      {
        "identifier": "modulo3",
        "name": "Inferencia y Simulación",
        "tag": "Predictivo",
        "detail": "Clustering, fatiga, riesgo de lesión y escenarios What-If con Monte Carlo.",
        "color": "#8B5CF6",
        "highlight": false,
        "icon": "brain"
      },
      {
        "identifier": "modulo4",
        "name": "Valoración Integral",
        "tag": "Decisión",
        "detail": "Rendimiento, físico, mercado, comercial y médico en un único score.",
        "color": "#10B981",
        "highlight": false,
        "icon": "star"
      }
    ]
  }
}
```

---

## Slide 6: Conclusiones

```json
{
  "slide_type": "closing",
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
    "title": "Conclusiones",
    "title_color": "#FFFFFF",
    "title_font": "Montserrat",
    "subtitle": "De datos a decisiones",
    "subtitle_color": "#8B95A5",
    "visual_prompt": "Dark elegant background with subtle red geometric lines converging to a point, suggesting data-driven decision making, professional closing slide aesthetic, Sevilla FC red accents, minimal and impactful",
    "items": [
      {
        "identifier": "C1",
        "name": "La valoración integral supera a la unidimensional",
        "tag": "Enfoque",
        "detail": "Combinar 6 dimensiones de rendimiento con datos externos revela el valor real de cada jugador, no solo sus goles o pases.",
        "color": "#D4001E",
        "highlight": true,
        "icon": "layers"
      },
      {
        "identifier": "C2",
        "name": "El tracking revela lo invisible",
        "tag": "Datos",
        "detail": "Las carreras sin balón, las pressing chains y las opciones de pase no aparecen en las estadísticas clásicas, pero definen el rendimiento.",
        "color": "#3B82F6",
        "highlight": false,
        "icon": "eye"
      },
      {
        "identifier": "C3",
        "name": "Gestión de carga es prevención",
        "tag": "Salud",
        "detail": "Monitorizar la fatiga, el ACWR y la caída de PSV-99 permite anticipar lesiones y optimizar rotaciones.",
        "color": "#10B981",
        "highlight": false,
        "icon": "heart-pulse"
      },
      {
        "identifier": "C4",
        "name": "Una herramienta replicable y escalable",
        "tag": "Futuro",
        "detail": "El modelo se puede aplicar a toda la plantilla, al mercado de fichajes y al scouting con más partidos y ligas.",
        "color": "#F59E0B",
        "highlight": false,
        "icon": "rocket"
      }
    ]
  }
}
```

---

## Guía de Presentación

| Slide | Presentador | Tiempo |
|---|---|---|
| 1. Portada | Cualquiera | 30s |
| 2. El Reto | Presentador 1 | 2 min |
| 3. Modelo Multidimensional | Presentador 2 | 2,5 min |
| 4. Hallazgos Clave | Presentador 2 | 2,5 min |
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
