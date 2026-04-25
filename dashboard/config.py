"""Configuracion central del dashboard Sevilla FC."""

from pathlib import Path

import pandas as pd

# --- Rutas ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Formación La Liga IA y caso práctico"
CACHE_DIR = Path(__file__).resolve().parent / "data" / "cache"

# --- Partidos ---
MATCHES = {
    1803069: {
        "label": "Barça vs Sevilla",
        "jornada": "J10",
        "date": "2024-10-20",
        "score": "5-1",
        "home": "FC Barcelona",
        "away": "Sevilla FC",
        "espn_file": "FCBarcelona Sevilla FC 201024_.csv",
    },
    1902526: {
        "label": "Atletico vs Sevilla",
        "jornada": "J16",
        "date": "2024-12-08",
        "score": "4-3",
        "home": "Atletico Madrid",
        "away": "Sevilla FC",
        "espn_file": None,
    },
    1927275: {
        "label": "R.Madrid vs Sevilla",
        "jornada": "J18",
        "date": "2024-12-22",
        "score": "4-2",
        "home": "Real Madrid",
        "away": "Sevilla FC",
        "espn_file": "Real Madrid Sevilla 221224.csv",
    },
    2002584: {
        "label": "Sevilla vs Barça",
        "jornada": "J23",
        "date": "2025-02-09",
        "score": "1-4",
        "home": "Sevilla FC",
        "away": "FC Barcelona",
        "espn_file": None,
    },
    2010398: {
        "label": "Sevilla vs Atletico",
        "jornada": "J30",
        "date": "2025-04-06",
        "score": "1-2",
        "home": "Sevilla FC",
        "away": "Atletico Madrid",
        "espn_file": "Sevilla Atelico Madrid 060425 .csv",
    },
    2017683: {
        "label": "Sevilla vs R.Madrid",
        "jornada": "J37",
        "date": "2025-05-18",
        "score": "0-2",
        "home": "Sevilla FC",
        "away": "Real Madrid",
        "espn_file": "Sevilla Real Madrid 180525.csv",
    },
}

MATCH_IDS = list(MATCHES.keys())

# --- Mapeo posicion -> perfil ---
POSITION_TO_PROFILE = {
    "GK": "GK",
    "LCB": "CB", "RCB": "CB", "CB": "CB",
    "LB": "FB", "RB": "FB", "LWB": "FB", "RWB": "FB",
    "DM": "DM", "LDM": "DM", "RDM": "DM",
    "CM": "DM",
    "LM": "WM", "RM": "WM",
    "AM": "AM", "CAM": "AM",
    "LW": "W", "RW": "W", "LF": "W", "RF": "W",
    "CF": "CF", "ST": "CF",
    "SUB": "SUB",
}

# --- Mapeo nombre fisico -> nombre dynamic events ---
PHYS_TO_DYN = {
    "Dodi Lukébakio": "D. Lukébakio",
    "Nemanja Gudelj": "N. Gudelj",
    "Saúl Ñíguez Esclapez": "Saúl Ñíguez",
    "Jesús Joaquín Fernández Sáez de la Torre": "Suso",
    "Djibril Sow": "D. Sow",
    "Lucien Jefferson Agoumé": "L. Agoumé",
    "Adrià Giner Pedrosa": "Adrià Pedrosa",
    "Albert-Mboyo Sambi Lokonga": "A. Sambi Lokonga",
    "Marcos do Nascimento Teixeira": "Marcão",
    "Rubén Vargas": "R. Vargas",
    "Loïc Badé": "L. Badé",
    "Chidera Ejuke": "C. Ejuke",
    "Gerard Fernández Castellano": "Peque Fernández",
    "José Ángel Carmona Navarro": "José Ángel Carmona",
    "Isaac Romero Bernal": "Isaac Romero",
    "Juan Luis Sánchez Velasco": "Juanlu Sánchez",
    "Enrique Jesús Salas Valiente": "Kike Salas",
    "Akor Jerome Adams": "A. Adams",
    "Stanis Idumbo Muzambo": "S. Idumbo",
}

# --- Pesos por dimension ---
D1_WEIGHTS = {
    "d1_xthreat_mean_norm": 0.25,
    "d1_pass_success_norm": 0.20,
    "d1_carries_p90_norm": 0.15,
    "d1_line_break_opts_norm": 0.20,
    "d1_forward_momentum_norm": 0.10,
    "d1_xa_p90_norm": 0.10,
}

D2_WEIGHTS = {
    "d2_lead_to_shot_norm": 0.20,
    "d2_shots_p90_norm": 0.15,
    "d2_dangerous_runs_p90_norm": 0.25,
    "d2_penetrating_runs_p90_norm": 0.15,
    "d2_xg_p90_norm": 0.25,
}

D3_WEIGHTS = {
    "d3_runs_p90_norm": 0.20,
    "d3_hv_runs_p90_norm": 0.20,
    "d3_po_score_norm": 0.20,
    "d3_received_space_norm": 0.20,
    "d3_line_break_rate_norm": 0.20,
}

D4_WEIGHTS = {
    "d4_engagements_p90_norm": 0.15,
    "d4_pressing_chain_norm": 0.20,
    "d4_danger_neutralized_norm": 0.20,
    "d4_force_backward_norm": 0.10,
    "d4_solidity_norm": 0.15,
    "d4_tackles_int_p90_norm": 0.20,
}

D5_WEIGHTS = {
    "d5_mmin_norm": 0.15,
    "d5_hsr_dist_p90_norm": 0.25,
    "d5_sprints_p90_norm": 0.20,
    "d5_high_accel_p90_norm": 0.20,
    "d5_psv99_norm": 0.20,
}

D6_WEIGHTS = {
    "d6_retention_norm": 0.35,
    "d6_pass_accuracy_norm": 0.25,
    "d6_quick_decision_norm": 0.20,
    "d6_pass_selection_norm": 0.20,
}

# --- Pesos por perfil (D1..D6) ---
PROFILE_WEIGHTS = {
    "CB": [0.15, 0.05, 0.05, 0.40, 0.20, 0.15],
    "FB": [0.20, 0.05, 0.15, 0.25, 0.20, 0.15],
    "DM": [0.25, 0.05, 0.10, 0.25, 0.15, 0.20],
    "WM": [0.20, 0.10, 0.15, 0.15, 0.25, 0.15],
    "AM": [0.30, 0.15, 0.15, 0.10, 0.10, 0.20],
    "W":  [0.20, 0.25, 0.20, 0.10, 0.15, 0.10],
    "CF": [0.10, 0.35, 0.25, 0.05, 0.15, 0.10],
}

MIN_MINUTES = 30

# --- Colores ---
SEVILLA_RED = "#D4001E"
SEVILLA_WHITE = "#FFFFFF"
BG_COLOR = "#F5F5F5"

PROFILE_COLORS = {
    "CB": "#457B9D",
    "FB": "#2A9D8F",
    "DM": "#264653",
    "WM": "#E9C46A",
    "AM": "#F4A261",
    "W":  "#E63946",
    "CF": "#D62828",
}

# --- Etiquetas de dimensiones ---
DIM_LABELS = {
    "score_d1": "D1 Progresión",
    "score_d2": "D2 Amenaza",
    "score_d3": "D3 Mov. s/balón",
    "score_d4": "D4 Defensa",
    "score_d5": "D5 Físico",
    "score_d6": "D6 Retención",
}

DIM_COLS = list(DIM_LABELS.keys())

# --- Descripciones en lenguaje sencillo ---
DIM_DESCRIPTIONS = {
    "D1 Progresión": "Mide la capacidad del jugador para avanzar el balón hacia la portería rival (pases progresivos, conducciones, regates exitosos).",
    "D2 Amenaza": "Evalúa cuánto peligro genera cerca del área rival (tiros, asistencias esperadas, acciones de gol).",
    "D3 Mov. s/balón": "Valora el movimiento inteligente sin balón (desmarques, carreras al espacio, opciones de pase creadas).",
    "D4 Defensa": "Mide el esfuerzo y eficacia defensiva (intercepciones, presión, recuperaciones, duelos ganados).",
    "D5 Físico": "Rendimiento físico: distancia recorrida, sprints, velocidad máxima y resistencia durante el partido.",
    "D6 Retención": "Capacidad de conservar el balón bajo presión (pases completados, control, pérdidas evitadas).",
}

KPI_HELP = {
    "Score Compuesto": "Nota global del jugador de 0 a 1, donde 1 es el mejor rendimiento posible. Combina las 6 dimensiones según la importancia de cada una para su posición.",
    "Jugadores activos": "Jugadores del Sevilla FC que participaron en los partidos seleccionados.",
    "Partidos analizados": "Número de partidos incluidos en el análisis actual.",
    "Score medio equipo": "Media de las notas globales de todos los jugadores del equipo.",
    "CV": "Coeficiente de variación: valores bajos = rendimiento estable partido a partido; valores altos = rendimiento irregular.",
    "Mejor dimension": "La dimensión en la que el jugador obtiene la nota más alta.",
}

PROFILE_DESCRIPTIONS = {
    "CB": "Central (defensa central)",
    "FB": "Lateral (defensa lateral)",
    "DM": "Centrocampista defensivo / Pivote",
    "WM": "Centrocampista de banda",
    "AM": "Mediapunta / Centrocampista ofensivo",
    "W": "Extremo",
    "CF": "Delantero centro",
}

PHYSICAL_GLOSSARY = {
    "M/min": "Metros por minuto — intensidad media de carrera del jugador durante el partido.",
    "HSR": "High Speed Running — distancia o acciones a alta velocidad (>19.8 km/h).",
    "PSV-99": "Velocidad máxima de sprint alcanzada (percentil 99).",
    "COD": "Change of Direction — cambios de dirección que miden la agilidad del jugador.",
    "P90": "Valor normalizado a 90 minutos de juego, para comparar jugadores con distintos minutos.",
    "TIP": "Team In Possession — métricas cuando el equipo tiene el balón.",
    "OTIP": "Opposite Team In Possession — métricas cuando el rival tiene el balón.",
    "Sprint": "Carrera a máxima velocidad (>25.2 km/h).",
    "Aceleración": "Cambios bruscos de velocidad que miden la explosividad del jugador.",
}

EVENT_GLOSSARY = {
    "Evento": "Cada acción registrada de un jugador durante el partido: un pase, un regate, una presión, etc.",
    "xThreat": "Amenaza esperada — probabilidad de que una acción termine en gol. Valores más altos = acciones más peligrosas.",
    "Rotura de línea": "Cuando una acción supera una línea defensiva rival (primera línea, penúltima o última).",
    "build_up": "Construcción — fase de juego donde el equipo sale jugando desde atrás.",
    "create": "Creación — fase donde el equipo busca generar peligro cerca del área rival.",
    "direct": "Juego directo — acciones rápidas hacia la portería sin fases intermedias.",
    "Presión": "Nivel de presión rival sobre el jugador con balón (de ninguna a muy alta).",
}

# --- Traducciones de valores de eventos ---
EVENT_TYPE_ES = {
    "player_possession": "Posesión",
    "passing_option": "Opción de pase",
    "off_ball_run": "Carrera sin balón",
    "on_ball_engagement": "Acción sobre balón",
}

EVENT_SUBTYPE_ES = {
    "behind": "A la espalda",
    "coming_short": "Viene corto",
    "counter_press": "Contrapresión",
    "cross_receiver": "Receptor de centro",
    "dropping_off": "Descuelgue",
    "overlap": "Desdoblamiento",
    "pressing": "Presión",
    "pressure": "Presión",
    "pulling_half_space": "Atrae al medio-espacio",
    "pulling_wide": "Atrae a banda",
    "recovery_press": "Presión de recuperación",
    "run_ahead_of_the_ball": "Carrera adelantada",
    "support": "Apoyo",
    "underlap": "Desdoblamiento interior",
}

PHASE_ES = {
    "build_up": "Construcción",
    "create": "Creación",
    "direct": "Juego directo",
    "transition": "Transición",
    "chaotic": "Caótica",
    "disruption": "Disrupción",
    "finish": "Finalización",
    "quick_break": "Contraataque",
    "set_play": "Balón parado",
}

PRESSURE_ES = {
    "no_pressure": "Ninguna",
    "low_pressure": "Baja",
    "medium_pressure": "Media",
    "high_pressure": "Alta",
    "very_high_pressure": "Muy alta",
}


def translate_event(val: str, mapping: dict) -> str:
    """Traduce un valor de evento usando el diccionario dado."""
    if pd.isna(val):
        return val
    return mapping.get(val, val)


# --- Etiquetas normalizadas para columnas ---
COLUMN_LABELS = {
    # Generales
    "player_name": "Jugador",
    "dyn_name": "Jugador",
    "profile": "Posición",
    "jornada": "Jornada",
    "match_label": "Partido",
    "match_id": "Partido",
    "minutes_played": "Minutos",
    "total_minutes": "Minutos totales",
    "n_matches": "Partidos",
    # Scores
    "composite_score": "Score Compuesto",
    "std_dev": "Desviación",
    "cv": "CV (consistencia)",
    "score_d1": "D1 Progresión",
    "score_d2": "D2 Amenaza",
    "score_d3": "D3 Mov. s/balón",
    "score_d4": "D4 Defensa",
    "score_d5": "D5 Físico",
    "score_d6": "D6 Retención",
    # Físicos
    "Distance": "Distancia (m)",
    "M/min": "Metros/min",
    "Running Distance": "Dist. carrera (m)",
    "HSR Distance": "Dist. HSR (m)",
    "HSR Distance P90": "Dist. HSR P90 (m)",
    "HSR Count": "Carreras HSR",
    "HSR Count P90": "Carreras HSR P90",
    "Sprint Distance": "Dist. sprint (m)",
    "Sprint Distance P90": "Dist. sprint P90 (m)",
    "Sprint Count": "Sprints",
    "Sprint Count P90": "Sprints P90",
    "PSV-99": "Vel. máx. (km/h)",
    "High Acceleration Count": "Acel. altas",
    "High Acceleration Count P90": "Acel. altas P90",
    "High Deceleration Count": "Decel. altas",
    "High Deceleration Count P90": "Decel. altas P90",
    "Change of Direction Count": "Cambios dirección",
    # Eventos
    "event_type": "Tipo",
    "event_subtype": "Subtipo",
    "x_start": "X inicio",
    "y_start": "Y inicio",
    "x_end": "X fin",
    "y_end": "Y fin",
    "overall_pressure_start": "Presión",
    "team_in_possession_phase_type": "Fase",
    "player_targeted_xthreat": "xThreat",
    "lead_to_shot": "Tiro",
    "lead_to_goal": "Gol",
    # M3: Inferencia
    "cluster": "Cluster",
    "fatigue_index": "Índice fatiga",
    "cumulative_load": "Carga acumulada",
    "psv99_pct_change": "Cambio PSV-99 (%)",
    "risk_level": "Nivel riesgo",
    "risk_score": "Score riesgo",
    "acwr": "ACWR",
    "sprint_ratio": "Ratio sprint",
    "load_change_pct": "Cambio carga (%)",
    "risk_factors": "Factores riesgo",
    "r2": "R²",
    "slope": "Pendiente",
    "p_value": "p-valor",
    "ci_lower": "IC inferior",
    "ci_upper": "IC superior",
    "statistic": "Correlación",
    "n_obs": "Observaciones",
    "significant": "Significativa",
    "interpretation": "Interpretación",
    "var_x": "Variable X",
    "var_y": "Variable Y",
    "pc1": "PC1",
    "pc2": "PC2",
    # M4: What-If
    "n_iterations": "Iteraciones",
    "block_type": "Tipo de bloque",
    "pressing_rate": "Tasa pressing",
    "solidity": "Solidez",
    "recovery_rate": "Tasa recuperacion",
    "pressing_chain_mean": "Cadena pressing",
    "danger_neutralized": "Peligro neutralizado",
    "rotation_frequency": "Frecuencia rotacion",
    "formation": "Formacion",
    "peak_fatigue": "Pico fatiga",
    "reduction_pct": "Reduccion (%)",
    # M5: Valoracion
    "score_rendimiento": "Rendimiento Deportivo",
    "score_fisico": "Condición Física",
    "score_mercado": "Valor de Mercado",
    "score_comercial": "Impacto Comercial",
    "score_medico": "Fiabilidad Médica",
    "integral_score": "Score Integral",
    "market_value_m": "Valor mercado (M€)",
    "contract_years": "Años contrato",
    "rrss_followers_k": "Seguidores RRSS (K)",
    "engagement_rate": "Tasa engagement",
    "media_mentions": "Menciones mediáticas",
    "injuries_2y": "Lesiones (2 temp.)",
    "days_missed": "Días perdidos",
}


def label(col: str) -> str:
    """Devuelve la etiqueta normalizada de una columna."""
    return COLUMN_LABELS.get(col, col)


# --- Template Plotly ---
# --- M3: Inferencia ---

# Features para clustering (dimensiones del score)
CLUSTERING_FEATURES = ["score_d1", "score_d2", "score_d3", "score_d4", "score_d5", "score_d6"]
CLUSTERING_FEATURES_PHYSICAL = ["M/min", "HSR Distance P90", "Sprint Distance P90", "PSV-99",
                                 "High Acceleration Count P90"]

CLUSTER_COLORS = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261", "#264653"]

RISK_COLORS = {"bajo": "#2A9D8F", "medio": "#E9C46A", "alto": "#E63946"}
RISK_LABELS = {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}

ACWR_THRESHOLDS = (0.8, 1.3)
PSV99_DROP_THRESHOLD = 5.0   # porcentaje
LOAD_SPIKE_THRESHOLD = 30.0  # porcentaje

CORRELATION_PAIRS = [
    {"var_x": "pressure_numeric", "var_y": "end_type_loss",
     "label_x": "Presión recibida", "label_y": "Pérdida de balón"},
    {"var_x": "n_defensive_lines", "var_y": "player_targeted_xthreat",
     "label_x": "Líneas defensivas", "label_y": "xThreat rival"},
    {"var_x": "n_passing_options", "var_y": "player_targeted_xthreat",
     "label_x": "Opciones de pase", "label_y": "xThreat generado"},
    {"var_x": "forward_momentum_num", "var_y": "lead_to_shot_num",
     "label_x": "Momentum ofensivo", "label_y": "Acaba en tiro"},
    {"var_x": "separation_start", "var_y": "xpass_completion",
     "label_x": "Separación", "label_y": "Precisión pase esperada"},
    {"var_x": "n_off_ball_runs", "var_y": "lead_to_shot_num",
     "label_x": "Carreras sin balón", "label_y": "Acaba en tiro"},
    {"var_x": "pressing_chain_length", "var_y": "end_type_recovery",
     "label_x": "Long. cadena pressing", "label_y": "Recuperación"},
]

INFERENCE_GLOSSARY = {
    "Cluster": "Grupo de jugadores con perfil de rendimiento similar, identificado por algoritmo K-Means.",
    "PCA": "Análisis de Componentes Principales — reduce las 6 dimensiones a 2 para visualizar los clusters.",
    "Silhouette": "Medida de calidad del clustering (0 a 1). Valores > 0.3 indican agrupaciones razonables.",
    "ACWR": "Acute:Chronic Workload Ratio — relación entre carga reciente y carga histórica. Valores fuera de [0.8, 1.3] indican riesgo.",
    "Índice de fatiga": "Combinación ponderada de caída de PSV-99, reducción de HSR y acumulación de carga (0 = fresco, 1 = fatigado).",
    "Riesgo de lesión": "Clasificación basada en ACWR, caída de velocidad y picos de carga. Verde = bajo, amarillo = medio, rojo = alto.",
    "Correlación": "Relación estadística entre dos variables. Pearson mide relación lineal, Spearman relación monótona.",
    "IC 95%": "Intervalo de confianza al 95% — rango donde se espera el valor real con 95% de probabilidad.",
    "p-valor": "Probabilidad de observar la correlación por azar. p < 0.05 = estadísticamente significativa.",
}

# --- M4: Escenarios What-If ---

WHATIF_DEFAULT_ITERATIONS = 1000
WHATIF_RANDOM_STATE = 42

FORMATION_TEMPLATES = {
    "4-3-3": {"GK": 1, "CB": 2, "FB": 2, "DM": 1, "WM": 2, "W": 2, "CF": 1},
    "4-4-2": {"GK": 1, "CB": 2, "FB": 2, "DM": 2, "WM": 2, "CF": 2},
    "3-5-2": {"GK": 1, "CB": 3, "WM": 2, "DM": 2, "AM": 1, "CF": 2},
    "3-4-3": {"GK": 1, "CB": 3, "WM": 2, "DM": 2, "W": 2, "CF": 1},
}

POSITION_COMPATIBILITY = {
    "GK": ["GK"],
    "CB": ["CB"],
    "FB": ["FB", "WM"],
    "DM": ["DM", "AM"],
    "WM": ["WM", "FB", "W"],
    "AM": ["AM", "DM", "WM"],
    "W": ["W", "WM", "AM"],
    "CF": ["CF", "W"],
}

BLOCK_LABELS = {
    "high_block": "Bloque alto",
    "medium_block": "Bloque medio",
    "low_block": "Bloque bajo",
}

WHATIF_GLOSSARY = {
    "Bootstrap": "Tecnica de remuestreo con reemplazo para estimar incertidumbre sin asumir distribucion normal.",
    "Monte Carlo": "Simulacion que repite el mismo experimento muchas veces (1000+) con variaciones aleatorias para obtener un rango de resultados probables.",
    "Intervalo de confianza": "Rango donde se espera el valor real. P25-P75 cubre el 50% central de las simulaciones.",
    "Percentil": "P50 = mediana (mitad). P25 = el 25% mas bajo. P75 = el 25% mas alto.",
    "xThreat": "Amenaza esperada por accion — probabilidad de que una accion termine en gol.",
    "Bloque defensivo": "Altura a la que el equipo defiende: alto (pressing arriba), medio, bajo (replegado).",
    "Rotacion": "Descanso programado de un jugador para gestionar su carga fisica.",
    "Formacion": "Disposicion tactica de los jugadores en el campo (ej: 4-3-3, 3-5-2).",
    "Composite score": "Nota global del jugador (0-1) que combina las 6 dimensiones de rendimiento.",
}

WHATIF_SCENARIO_DESCRIPTIONS = {
    "ausencia": {
        "titulo": "Que pasa si un jugador no juega?",
        "descripcion": "Simula el impacto en las metricas de equipo cuando un jugador es excluido. "
                       "Identifica pares posicionales que absorberian su contribucion.",
    },
    "bloque": {
        "titulo": "Que bloque defensivo es mas efectivo?",
        "descripcion": "Compara la eficacia de bloque alto, medio y bajo basado en eventos reales. "
                       "Evalua pressing, solidez y capacidad de recuperacion.",
    },
    "rotacion": {
        "titulo": "Impacto de rotar a un jugador",
        "descripcion": "Proyecta la curva de fatiga con y sin descansos programados. "
                       "Estima la reduccion de pico de fatiga y riesgo de lesion.",
    },
    "formacion": {
        "titulo": "Que formacion rinde mejor?",
        "descripcion": "Compara dos formaciones tacticas asignando los mejores jugadores a cada posicion. "
                       "Recalcula scores con pesos de la nueva posicion.",
    },
}

# --- M5: Valoracion Multidimensional ---

M5_DEFAULT_WEIGHTS = {
    "rendimiento": 40,
    "fisico": 20,
    "mercado": 20,
    "comercial": 10,
    "medico": 10,
}

M5_DIM_LABELS = {
    "score_rendimiento": "Rendimiento Deportivo",
    "score_fisico": "Condición Física",
    "score_mercado": "Valor de Mercado",
    "score_comercial": "Impacto Comercial",
    "score_medico": "Fiabilidad Médica",
    "integral_score": "Score Integral",
}

M5_DIM_DESCRIPTIONS = {
    "Rendimiento Deportivo": "Basado en el composite score (D1-D6) del módulo de rendimiento, penalizado por inconsistencia (CV alto).",
    "Condición Física": "Percentil físico (HSR, sprints, PSV-99) combinado con resiliencia a la fatiga y ajuste por riesgo de lesión.",
    "Valor de Mercado": "Eficiencia valor/rendimiento considerando edad, años de contrato restantes y valor de mercado estimado.",
    "Impacto Comercial": "Alcance en redes sociales, tasa de engagement y presencia mediática del jugador.",
    "Fiabilidad Médica": "Historial de lesiones en últimas 2 temporadas: número, días perdidos y lesiones recurrentes.",
}

M5_DATA_SOURCES = {
    "Rendimiento Deportivo": "real",
    "Condición Física": "real",
    "Valor de Mercado": "externo",
    "Impacto Comercial": "externo",
    "Fiabilidad Médica": "externo",
}

M5_GLOSSARY = {
    "Score Integral": "Puntuación global (0-100) que combina 5 dimensiones con pesos configurables. Herramienta de apoyo, no ranking absoluto.",
    "Pesos": "Porcentaje de importancia asignado a cada dimensión. Deben sumar 100%.",
    "Datos reales": "Dimensiones calculadas a partir de datos de tracking y eventing de los 6 partidos analizados.",
    "Datos externos": "Dimensiones basadas en datos proporcionados por el usuario (mercado, Instagram, historial medico) via archivo CSV.",
    "Composite Score": "Nota global de rendimiento (0-1) del módulo 1, que combina las 6 dimensiones tácticas.",
    "CV": "Coeficiente de variación — mide la consistencia partido a partido. CV bajo = rendimiento estable.",
    "Eficiencia valor/rendimiento": "Relación entre lo que rinde un jugador y lo que cuesta. Valores altos = buena inversión.",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "font": {"family": "Inter, sans-serif", "size": 12, "color": "#333"},
        "paper_bgcolor": SEVILLA_WHITE,
        "plot_bgcolor": "#FAFAFA",
        "hoverlabel": {"bgcolor": "#333", "font_size": 12, "font_color": SEVILLA_WHITE},
        "margin": {"t": 50, "b": 40, "l": 60, "r": 20},
    }
}
