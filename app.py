import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import streamlit.components.v1 as components

# Import vos fonctions existantes
from sonalyse_advisor.json_utils import (
    load_json,
    json_extract_info,
    get_average_rating,
    get_noise_type_by_hour,
    get_noise_type_percentage_hourly,
    get_noise_type_percentage_daily,
    get_average_db,
    get_db_min_max_peak_by_hour,
)

from sonalyse_advisor.agent_backend import interpret_json

st.set_page_config(page_title="Sonalyze Diagnostic", page_icon="🔊", layout="wide")

# ========================================
# 🔒 CHARGEMENT DES  DONNÉES
# ========================================


@st.cache_data
def load_data():
    """
    Charge et traite UNIQUEMENT les données réelles depuis json_utils.
    Si une erreur survient → renvoie None proprement.
    """
    try:
        # Load JSON
        raw_data = load_json("data/dps_analysis_pi3_exemple.json")

        # Extraction via ton module json_utils
        (
            extracted_rating,
            extracted_dominant_noise,
            extracted_average_median,
            extracted_min_max_peak,
            extracted_background_noise,
        ) = json_extract_info(raw_data)

        # Calculs statistiques via json_utils
        average_db = get_average_db(extracted_average_median)
        average_rating = get_average_rating(extracted_rating)
        noise_percentage = get_noise_type_percentage_daily(extracted_dominant_noise)
        noise_by_hour = get_noise_type_by_hour(extracted_dominant_noise)
        noise_percentage_hourly = get_noise_type_percentage_hourly(noise_by_hour)
        db_min_max_peak_by_hourly = get_db_min_max_peak_by_hour(extracted_average_median, extracted_min_max_peak)

        # Retour uniforme
        return {
            "ratings": extracted_rating,
            "dominant_noise": extracted_dominant_noise,
            "average_median": extracted_average_median,
            "min_max_peak": extracted_min_max_peak,
            "background_noise": extracted_background_noise,
            "stats": {
                "avg_db": average_db,
                "avg_db_day": average_db,  # tu ajusteras plus tard
                "avg_db_night": average_db * 0.8,
                "max_db": max([x["max_dB"] for x in extracted_min_max_peak]),
                "min_db": min([x["min_dB"] for x in extracted_min_max_peak]),
            },
            "grade": average_rating,
            "noise_percentage": noise_percentage,
            "noise_percentage_hourly": noise_percentage_hourly,
            "db_min_max_peak_by_hourly": db_min_max_peak_by_hourly,
        }

    except Exception as e:
        st.error(f"❌ Impossible de charger les données réelles : {e}")
        return None


# Charger données
data = load_data()

# ========================================
# TAB 2 — FCT PDF GENERATION
# ========================================
def generate_pdf(data):
    """
    Génère un PDF du rapport DPS.
    Cette fonction sera remplie plus tard.(Par driss)

    Paramètres :
        data (dict) : données complètes retournées par load_data()

    Étapes à implémenter :  genere pdf vide 
        1. Créer un buffer mémoire (BytesIO) plus facile
        2. Créer un document PDF ReportLab
        4. Construire le PDF 
        5. Retourner le buffer

    Retour :
        BytesIO : PDF généré
    """
    pass  # La logique sera ajoutée plus tard

if data:
    stats = data["stats"]
    grade = data["grade"]
    st.success(f"✅ {len(data['ratings'])} mesures chargées depuis données réelles")
else:
    # Fallback données test
    stats = {
        "avg_db": 42.5,
        "avg_db_day": 42.5,
        "avg_db_night": 33.2,
        "max_db": 78.0,
        "min_db": 22.0,
    }
    grade = "C"

logement = {"nom": "Logement Exemple", "adresse": "15 Rue de la République"}
piece = {"nom": "Chambre"}

# ========================================
# 🎨 HEADER
# ========================================

st.title("🔊 Diagnostic Sonalyze Advisor")
st.markdown("*Votre diagnostic de performance sonore intelligent*")

col_info1, col_info2 = st.columns([3, 1])
with col_info1:
    st.caption(f"📍 {logement['nom']} - {piece['nom']}")
with col_info2:
    if st.button("📄 Générer PDF"):
     pdf_file = generate_pdf(data)
        #st.success("✅ Rapport PDF généré avec succès ! (fonctionnalité à venir)")
     #msg pour driss : c la ou ca se passe action genere pdf 

st.divider()

# ========================================
# 📑 TABS
# ========================================

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Synthèse", "📈 Visualisations D3.js", "🤖 Analyse IA", "💡 Recommandations"]
)

# ========================================
# TAB 1 — SYNTHÈSE
# ========================================
with tab1:

    # Note globale
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        colors = {
            "A": "#00AA00",
            "B": "#55CC00",
            "C": "#AADD00",
            "D": "#FFEE00",
            "E": "#FFAA00",
            "F": "#FF5500",
            "G": "#DD0000",
        }
        st.markdown(
            f"""
            <div style='text-align: center; padding: 50px; background-color: {colors.get(grade, '#AADD00')}; 
                        border-radius: 20px; margin: 30px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h1 style='font-size: 140px; margin: 0; color: white; font-weight: bold;'>{grade}</h1>
                <p style='font-size: 28px; color: white; margin: 10px 0;'>Performance Sonore</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("☀️ Niveau Jour", f"{stats['avg_db_day']:.1f} dB")
    col2.metric("🌙 Niveau Nuit", f"{stats['avg_db_night']:.1f} dB")
    col3.metric("📈 Maximum", f"{stats['max_db']:.1f} dB")
    col4.metric("📉 Minimum", f"{stats['min_db']:.1f} dB")

    st.divider()

    # Répartition des bruits (si données disponibles)
    if data and "noise_percentage" in data:
        st.subheader("🔊 Répartition des sources de bruit")

        cols = st.columns(min(5, len(data["noise_percentage"])))
        color_map = {
            "traffic": "#FF6B6B",
            "voices": "#4ECDC4",
            "construction": "#45B7D1",
            "nature": "#96CEB4",
            "music": "#FFEAA7",
        }

        for i, (noise_type, percentage) in enumerate(data["noise_percentage"].items()):
            if i < 5:  # Limiter à 5 colonnes
                with cols[i]:
                    color = color_map.get(noise_type, "#667eea")
                    st.markdown(
                        f"""
                    <div style='text-align: center; padding: 15px; background-color: {color}20; 
                                border-left: 4px solid {color}; border-radius: 8px;'>
                        <h4 style='margin: 0; color: {color};'>{noise_type.title()}</h4>
                        <p style='font-size: 32px; margin: 5px 0; font-weight: bold;'>{percentage:.1f}%</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

# ========================================
# TAB 3 — VISUALISATIONS D3.js
# ========================================
with tab2:
    st.header("📈 Visualisations Interactives D3.js")

    if data:
        # Préparer données pour D3.js
        hourly_data = []
        for hour in range(24):
            hour_str = str(hour).zfill(2)
            if hour_str in data.get("noise_percentage_hourly", {}):
                noise_info = data["noise_percentage_hourly"][hour_str]
                hourly_data.append(
                    {
                        "hour": hour,
                        "noise_type": noise_info["noise_type"],
                        "percentage": noise_info["percentage"],
                    }
                )
        
        # Préparer données dB par heure
        db_min_max_peak_by_hourly = data.get("db_min_max_peak_by_hourly","")

        timeline_data = []
        for hour in sorted(db_min_max_peak_by_hourly.keys()):
            values = db_min_max_peak_by_hourly[hour]
            timeline_data.append(
                {
                    "hour": hour,
                    "value": values["average_dB"],
                    "min": values["min_dB"],
                    "max": values["max_dB"],
                    "peak": values["peak_dB"],
                }
            )

        # Convertir en JSON pour JavaScript
        timeline_json = json.dumps(timeline_data)
        print(timeline_json)
        noise_daily_json = json.dumps(
            [{"category": k, "value": v} for k, v in data["noise_percentage"].items()]
        )

    else:
        timeline_json = "[]"
        noise_daily_json = "[]"

    # HTML avec D3.js #erreur declenche dans console a gere apres fctmnt
    d3_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
            }}
            .chart-container {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .chart-title {{
                font-size: 1.3em;
                font-weight: 600;
                margin-bottom: 15px;
                color: #333;
            }}
            .tooltip {{
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 10px;
                border-radius: 6px;
                pointer-events: none;
                font-size: 13px;
                opacity: 0;
                transition: opacity 0.3s;
            }}
            svg {{
                display: block;
                margin: 0 auto;
            }}
        </style>
    </head>
    <body>
        <div class="chart-container">
            <div class="chart-title">📈 Évolution du Niveau Sonore (24h) -  DONNÉES RÉELLES</div>
            <div id="timeline"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🎵 Radar des Sources de Bruit -  DONNÉES RÉELLES</div>
            <div id="radar"></div>
        </div>
        
        <div class="tooltip" id="tooltip"></div>

        <script>
            // Données depuis Python
            const timelineData = {timeline_json};
            const radarData = {noise_daily_json};
            
            // Timeline Chart
            function drawTimeline() {{
                const margin = {{top: 40, right: 40, bottom: 60, left: 60}};
                const width = 1000 - margin.left - margin.right;
                const height = 350 - margin.top - margin.bottom;
                
                const svg = d3.select("#timeline")
                    .append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
                
                const x = d3.scaleLinear()
                    .domain([0, 23])
                    .range([0, width]);
                
                const y = d3.scaleLinear()
                    .domain([0, Math.max(80, d3.max(timelineData, d => d.max))])
                    .range([height, 0]);
                
                // Grid
                svg.append("g")
                    .attr("class", "grid")
                    .style("stroke", "#e0e0e0")
                    .style("stroke-dasharray", "2,2")
                    .call(d3.axisLeft(y).tickSize(-width).tickFormat(""));
                
                // Area
                if (timelineData.length > 0) {{
                    const area = d3.area()
                        .x(d => x(d.hour))
                        .y0(d => y(d.min))
                        .y1(d => y(d.max))
                        .curve(d3.curveMonotoneX);
                    
                    svg.append("path")
                        .datum(timelineData)
                        .attr("fill", "rgba(102, 126, 234, 0.2)")
                        .attr("d", area);
                    
                    // Line
                    const line = d3.line()
                        .x(d => x(d.hour))
                        .y(d => y(d.value))
                        .curve(d3.curveMonotoneX);
                    
                    svg.append("path")
                        .datum(timelineData)
                        .attr("fill", "none")
                        .attr("stroke", "#667eea")
                        .attr("stroke-width", 3)
                        .attr("d", line);
                }}
                
                // Threshold lines
                svg.append("line")
                    .attr("x1", 0).attr("x2", width)
                    .attr("y1", y(30)).attr("y2", y(30))
                    .attr("stroke", "#00AA00")
                    .attr("stroke-width", 2)
                    .attr("stroke-dasharray", "5,5");
                
                svg.append("text")
                    .attr("x", width - 5).attr("y", y(30) - 5)
                    .attr("text-anchor", "end")
                    .style("fill", "#00AA00")
                    .style("font-size", "12px")
                    .text("Recommandé nuit (30 dB)");
                
                svg.append("line")
                    .attr("x1", 0).attr("x2", width)
                    .attr("y1", y(45)).attr("y2", y(45))
                    .attr("stroke", "#FFAA00")
                    .attr("stroke-width", 2)
                    .attr("stroke-dasharray", "5,5");
                
                svg.append("text")
                    .attr("x", width - 5).attr("y", y(45) - 5)
                    .attr("text-anchor", "end")
                    .style("fill", "#FFAA00")
                    .style("font-size", "12px")
                    .text("Recommandé jour (45 dB)");
                
                // Axes
                svg.append("g")
                    .attr("transform", `translate(0,${{height}})`)
                    .call(d3.axisBottom(x).ticks(24));
                
                svg.append("g")
                    .call(d3.axisLeft(y));
                
                svg.append("text")
                    .attr("x", width / 2).attr("y", height + 45)
                    .style("text-anchor", "middle")
                    .style("font-weight", "600")
                    .text("Heure de la journée");
                
                svg.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -height / 2).attr("y", -45)
                    .style("text-anchor", "middle")
                    .style("font-weight", "600")
                    .text("Niveau sonore (dB)");
            }}
            
            // Radar Chart
            function drawRadar() {{
                if (radarData.length === 0) return;
                
                const margin = 60;
                const width = 500;
                const height = 400;
                const centerX = width / 2;
                const centerY = height / 2;
                const radius = Math.min(width, height) / 2 - margin;
                
                const svg = d3.select("#radar")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", `translate(${{centerX}},${{centerY}})`);
                
                const angleSlice = Math.PI * 2 / radarData.length;
                
                // Grid circles
                const levels = 5;
                for (let i = 1; i <= levels; i++) {{
                    svg.append("circle")
                        .attr("r", radius / levels * i)
                        .style("fill", "none")
                        .style("stroke", "#ddd");
                }}
                
                // Axes
                radarData.forEach((d, i) => {{
                    const angle = angleSlice * i - Math.PI / 2;
                    const x = Math.cos(angle) * radius;
                    const y = Math.sin(angle) * radius;
                    
                    svg.append("line")
                        .attr("x1", 0).attr("y1", 0)
                        .attr("x2", x).attr("y2", y)
                        .style("stroke", "#ddd");
                    
                    const labelX = Math.cos(angle) * (radius + 40);
                    const labelY = Math.sin(angle) * (radius + 40);
                    
                    svg.append("text")
                        .attr("x", labelX).attr("y", labelY)
                        .attr("text-anchor", "middle")
                        .attr("dominant-baseline", "middle")
                        .style("font-size", "13px")
                        .style("font-weight", "600")
                        .text(d.category);
                }});
                
                // Data polygon
                const radarLine = d3.lineRadial()
                    .angle((d, i) => angleSlice * i)
                    .radius(d => (d.value / 100) * radius)
                    .curve(d3.curveLinearClosed);
                
                svg.append("path")
                    .datum(radarData)
                    .attr("d", radarLine)
                    .style("fill", "rgba(102, 126, 234, 0.3)")
                    .style("stroke", "#667eea")
                    .style("stroke-width", "3px");
                
                // Points
                const tooltip = d3.select("#tooltip");
                radarData.forEach((d, i) => {{
                    const angle = angleSlice * i - Math.PI / 2;
                    const r = (d.value / 100) * radius;
                    const x = Math.cos(angle) * r;
                    const y = Math.sin(angle) * r;
                    
                    svg.append("circle")
                        .attr("cx", x).attr("cy", y).attr("r", 6)
                        .style("fill", "#667eea")
                        .style("cursor", "pointer")
                        .on("mouseover", function(event) {{
                            tooltip
                                .style("opacity", 1)
                                .html(`<strong>${{d.category}}</strong><br/>Pourcentage: ${{d.value.toFixed(1)}}%`)
                                .style("left", (event.pageX + 10) + "px")
                                .style("top", (event.pageY - 30) + "px");
                        }})
                        .on("mouseout", () => tooltip.style("opacity", 0));
                }});
            }}
            
            // Initialize
            drawTimeline();
            drawRadar();
        </script>
    </body>
    </html>
    """

    # Afficher D3.js
    components.html(d3_html, height=900, scrolling=True)

# ========================================
# TAB 3 — ANALYSE IA
# ========================================
with tab3:
    st.header("🤖 Analyse IA")
    st.info("🧠 Cliquez sur le bouton pour lancer l'analyse IA.")

    if st.button("Lancer l'analyse IA"):
        stream_response = interpret_json("sonalyse_advisor/dps_analysis_pi3_exemple.json", "sonalyse_advisor/context.txt","data/logement2.json")

        # Execute the Python code dynamically
        try:
            exec(stream_response)
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'exécution du code : {e}")

# ========================================
# TAB 4 — RECOMMANDATIONS
# ========================================
with tab4:
    st.header("💡 Recommandations Personnalisées")

    st.subheader("🔧 Solutions Immédiates (50-200€)")
    st.markdown(
        """
    - **Joints de fenêtre adhésifs** (20-40€)
      - Impact: ⭐⭐⭐ | Réduction: -5 à -8 dB
    - **Rideaux phoniques** (60-150€)
      - Impact: ⭐⭐ | Réduction: -3 à -5 dB
    """
    )

    st.subheader("🛠️ Améliorations (500-2000€)")
    st.markdown(
        """
    - **Survitrage** (200-400€/fenêtre)
      - Impact: ⭐⭐⭐⭐ | Réduction: -8 à -12 dB
    """
    )

# FOOTER
st.divider()
st.caption("🚀 Sonalyze Advisor v1.0 - Hackathon IA Boot2Code")
