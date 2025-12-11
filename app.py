import matplotlib
matplotlib.use("Agg")#juuste pour éviter un bug avec streamlit si t'as macos
import streamlit as st
import json
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import plotly.graph_objects as go
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from sonalyse_advisor.agent_backend import interpret_json
import re
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
import matplotlib.pyplot as plt
import io

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
# 🔒 CHARGEMENT DES DONNÉES
# ========================================

@st.cache_data
def load_data():
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
                "avg_db_day": average_db,
                "avg_db_night": average_db * 0.8,
                "max_db": max([x["max_dB"] for x in extracted_min_max_peak]),
                "min_db": min([x["min_dB"] for x in extracted_min_max_peak]),
            },
            "grade": average_rating,
            "noise_by_hour": noise_by_hour,
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

def fig_to_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf

ia_response=interpret_json(
    "sonalyse_advisor/dps_analysis_pi3_exemple.json",
    "sonalyse_advisor/context.txt","data/logement1.json")

# Extraire uniquement la partie "3. Recommandations"
match = re.search(r"3\. Recommandations\s*(.*?)(?:\n\d+\..*|$)", ia_response, re.DOTALL)
recommendations_text = match.group(1).strip() if match else "Aucune recommandation disponible."

# Enlever caractères spéciaux et bouts de code
recommendations_text = re.sub(r"[^\w\s\-\.,:]", "", recommendations_text)
recommendations_text = recommendations_text.replace("\n", "<br/>")



def generate_pdf_with_graphs(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # TITRE
    elements.append(Paragraph("<b>Diagnostic Sonalyze - Rapport</b>", styles["Title"]))
    elements.append(Spacer(1, 20))
    
    grade = data["grade"]

    grade_color = {
        "A": "#00AA00",
        "B": "#55CC00",
        "C": "#AADD00",
        "D": "#FFEE00",
        "E": "#FFAA00",
        "F": "#FF5500",
        "G": "#DD0000",
    }.get(grade, "#AADD00")

    elements.append(Paragraph(
        f"<para alignment='center'><font size=22><b>Note de performance : "
        f"<font color='{grade_color}'>{grade}</font></b></font></para>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 20))

    # =====================
    # 📊 GRAPHE : Timeline
    # =====================
    timeline_data = data["db_min_max_peak_by_hourly"]

    fig, ax = plt.subplots(figsize=(8, 3))
    hours = sorted(timeline_data.keys())
    values = [timeline_data[h]["average_dB"] for h in hours]
    ax.plot(hours, values)
    ax.set_title("Évolution du niveau sonore (24h)")
    ax.set_xlabel("Heure")
    ax.set_ylabel("dB")

    img_timeline = fig_to_img(fig)
    elements.append(Image(img_timeline, width=450, height=200))
    elements.append(Spacer(1, 20))
    
        # ======================
    # 🌐 GRAPHE RADAR : Sources de bruit
    # ======================
    labels = list(data["noise_percentage"].keys())
    values = list(data["noise_percentage"].values())

    # fermer le radar (dernier = premier)
    values += values[:1]
    angles = [n / float(len(labels)) * 2 * 3.1415926 for n in range(len(labels))]
    angles += angles[:1]

    fig = plt.figure(figsize=(4, 4))
    ax = plt.subplot(111, polar=True)

    # Tracé
    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.3)

    # Label des axes
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    # Valeurs numériques
    for i, v in enumerate(values[:-1]):
        ax.text(angles[i], v + 3, f"{v:.1f}%", fontsize=9, ha='center')

    ax.set_title("Radar des sources de bruit (en %)")

    img_radar = fig_to_img(fig)
    elements.append(Image(img_radar, width=300, height=300))
    elements.append(Spacer(1, 12))

    legend_text = "<br/>".join(
        [f"<b>{k.title()}</b> : {v:.1f}% du temps" for k, v in data["noise_percentage"].items()]
    )
    elements.append(Paragraph(f"<b>Légende des sources de bruit :</b><br/>{legend_text}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # =====================
    # 🔥 GRAPHE : Heatmap
    # =====================
    heatmap = data["noise_percentage_hourly"]

    fig, ax = plt.subplots(figsize=(8, 3))

    # Construire la matrice
    matrix = [v["percentage"] for v in heatmap.values()]

    # Heatmap
    cax = ax.imshow([matrix], aspect="auto", cmap="viridis")

    ax.set_title("Heatmap des bruits (simplifiée)")

    # Ajouter une vraie barre de couleur (légende)
    cbar = fig.colorbar(cax)
    cbar.set_label("Intensité du bruit (%)", fontsize=8)

    img_heatmap = fig_to_img(fig)
    elements.append(Image(img_heatmap, width=450, height=150))
    elements.append(Spacer(1, 12))

    # Explication pour l'utilisateur final
    legend_text = """
    <b>Légende des couleurs :</b><br/>
    • <b>Bleu</b> : très faible pourcentage de bruit.<br/>
    • <b>Vert</b> : bruit modéré.<br/>
    • <b>Jaune</b> : bruit notable / zones actives.<br/>
    • <b>Blanc</b> : pics importants de bruit.<br/><br/>
    <b>Utilité :</b> La heatmap permet de voir rapidement quelles heures présentent les taux 
    de bruit les plus élevés. Plus la couleur est claire, plus l'environnement sonore a été perturbé.
    """

    elements.append(Paragraph(legend_text, styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>Recommandations :</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(recommendations_text, styles["Normal"]))
    elements.append(Spacer(1, 20))


    # BUILD PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
# ========================================

if data:
    stats = data["stats"]
    grade = data["grade"]
    st.success(f"✅ {len(data['ratings'])} mesures chargées depuis vos données réelles")
else:
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
pdf_file = None

with col_info2:
    if st.button("📄 Générer PDF"):
        pdf_file = generate_pdf_with_graphs(data)
        st.success("✅ PDF généré ! Vous pouvez maintenant le télécharger.")

    st.download_button(
        "Télécharger le PDF",
        data=pdf_file if pdf_file else b"",
        file_name="rapport_dps.pdf",
        mime="application/pdf",
        disabled=pdf_file is None,
    )


st.divider()

# ========================================
# 📑 TABS
# ========================================

tab1, tab2, tab3 = st.tabs(
    ["📊 Synthèse", "📈 Visualisations D3.js", "🤖 Analyse IA et Recommandation"]
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

    # Répartition des bruits
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
            if i < 5:
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
# TAB 2 — VISUALISATIONS D3.js
# ========================================

with tab2:
    st.header("📈 Visualisations Interactives D3.js")
    
    if data:
        # Préparer données dB par heure
        db_min_max_peak_by_hourly = data.get("db_min_max_peak_by_hourly", {})

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

        pie_data = [
            {'category': k, 'value': v}
            for k, v in data['noise_percentage'].items()
        ]
        
        # Préparation des données pour la heatmap (CORRIGÉ)
        heatmap_rows = []
        
        # DEBUG  pour voir la structure de noise_by_hour
        # st.write("🔍 Debug - Structure de noise_by_hour:")
      
        
        if isinstance(data["noise_by_hour"], dict):
            #st.write(f"Nombre d'heures: {len(data['noise_by_hour'])}")
            
            # Afficher les premières heures
            for hour_str, hour_data in list(data["noise_by_hour"].items())[:10]:
                
                # Traitement pour la heatmap
                hour = int(hour_str) if hour_str.isdigit() else 0
                
                if isinstance(hour_data, list):
                    for item in hour_data:
                        if isinstance(item, str):
                            
                            intensity = 29  # Valeur par défaut
                            
                            hour_str_padded = str(hour).zfill(2)
                            if hour_str_padded in data.get("noise_percentage_hourly", {}):
                                noise_info = data["noise_percentage_hourly"][hour_str_padded]
                                if noise_info.get("noise_type") == item:
                                    intensity = noise_info.get("percentage", 50) * 0.8  # Convertir % en intensité
                            
                            heatmap_rows.append({
                                "hour": hour,
                                "category": item,
                                "value": intensity
                            })
        
        heatmap_json = json.dumps(heatmap_rows)
        
        # Convertir en JSON pour JavaScript
        timeline_json = json.dumps(timeline_data)
        pie_json = json.dumps(pie_data)

    else:
        timeline_json = "[]"
        pie_json = "[]"
        heatmap_json = "[]"

    # HTML avec D3.js - AVEC HEATMAP
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
            .heatmap-cell {{
                cursor: pointer;
            }}
            .heatmap-cell:hover {{
                stroke: #333;
                stroke-width: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="chart-container">
            <div class="chart-title">📈 Évolution du Niveau Sonore (24h)</div>
            <div id="timeline"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">🎵 Radar des Sources de Bruit</div>
            <div id="radar"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">🔥 Heatmap des Bruits (Heure × Type)</div>
            <div id="heatmap"></div>
        </div>

        <div class="tooltip" id="tooltip"></div>

        <script>
            // Données depuis Python
            const timelineData = {timeline_json};
            const pieData = {pie_json};
            const heatmapData = {heatmap_json};

            // Timeline Chart
            function drawTimeline() {{
                if (timelineData.length === 0) return;
                
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
                    .attr("transform", `translate(0,${{height}})`);
                
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
                if (!pieData || pieData.length === 0) return;
                
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
                
                const angleSlice = Math.PI * 2 / pieData.length;
                
                // Grid circles
                const levels = 5;
                for (let i = 1; i <= levels; i++) {{
                    svg.append("circle")
                        .attr("r", radius / levels * i)
                        .style("fill", "none")
                        .style("stroke", "#ddd");
                }}
                
                // Axes
                pieData.forEach((d, i) => {{
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
                    .datum(pieData)
                    .attr("d", radarLine)
                    .style("fill", "rgba(102, 126, 234, 0.3)")
                    .style("stroke", "#667eea")
                    .style("stroke-width", "3px");
                
                // Points
                const tooltip = d3.select("#tooltip");
                pieData.forEach((d, i) => {{
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

            // Heatmap
            function drawHeatmap() {{
                if (heatmapData.length === 0) {{
                    d3.select("#heatmap")
                        .append("p")
                        .text("Données insuffisantes pour afficher la heatmap");
                    return;
                }}
                
                const margin = {{top: 40, right: 80, bottom: 40, left: 80}};
                const width = 800 - margin.left - margin.right;
                const height = 400 - margin.top - margin.bottom;
                
                const svg = d3.select("#heatmap")
                    .append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
                
                // Extraire les catégories uniques et les heures
                const categories = [...new Set(heatmapData.map(d => d.category))];
                const hours = [...new Set(heatmapData.map(d => d.hour))].sort((a, b) => a - b);
                
                if (categories.length === 0 || hours.length === 0) return;
                
                // Échelles
                const x = d3.scaleBand()
                    .domain(hours)
                    .range([0, width])
                    .padding(0.05);
                
                const y = d3.scaleBand()
                    .domain(categories)
                    .range([0, height])
                    .padding(0.05);
                
                // Échelle de couleur
                const maxValue = d3.max(heatmapData, d => d.value);
                const colorScale = d3.scaleSequential()
                    .domain([0, maxValue])
                    .interpolator(d3.interpolateYlOrRd);
                
                // Créer les cellules
                svg.selectAll()
                    .data(heatmapData)
                    .enter()
                    .append("rect")
                    .attr("class", "heatmap-cell")
                    .attr("x", d => x(d.hour))
                    .attr("y", d => y(d.category))
                    .attr("width", x.bandwidth())
                    .attr("height", y.bandwidth())
                    .attr("fill", d => colorScale(d.value))
                    .attr("stroke", "#fff")
                    .attr("stroke-width", 1)
                    .on("mouseover", function(event, d) {{
                        tooltip
                            .style("opacity", 1)
                            .html(`Heure: ${{d.hour}}h<br/>
                                   Type: ${{d.category}}<br/>
                                   Intensité: ${{d.value.toFixed(1)}}`)
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 30) + "px");
                    }})
                    .on("mouseout", () => tooltip.style("opacity", 0));
                
                // Axes
                svg.append("g")
                    .attr("transform", `translate(0,${{height}})`)
                    .call(d3.axisBottom(x).tickFormat(d => d + "h"));
                
                svg.append("g")
                    .call(d3.axisLeft(y));
                
                // Labels
                svg.append("text")
                    .attr("x", width / 2)
                    .attr("y", height + 35)
                    .style("text-anchor", "middle")
                    .text("Heure de la journée");
                
                svg.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -height / 2)
                    .attr("y", -50)
                    .style("text-anchor", "middle")
                    .text("Type de bruit");
                
                // Légende
                const legendWidth = 200;
                const legendHeight = 20;
                
                const legend = svg.append("g")
                    .attr("transform", `translate(${{width - legendWidth - 10}}, -30)`);
                
                const defs = legend.append("defs");
                const linearGradient = defs.append("linearGradient")
                    .attr("id", "linear-gradient");
                
                linearGradient.selectAll("stop")
                    .data(colorScale.range().map((color, i, arr) => ({{
                        offset: `${{100 * i / (arr.length - 1)}}%`,
                        color: color
                    }})))
                    .enter()
                    .append("stop")
                    .attr("offset", d => d.offset)
                    .attr("stop-color", d => d.color);
                
                legend.append("rect")
                    .attr("width", legendWidth)
                    .attr("height", legendHeight)
                    .style("fill", "url(#linear-gradient)");
                
                legend.append("text")
                    .attr("x", 0)
                    .attr("y", -5)
                    .style("font-size", "12px")
                    .text("Intensité du bruit");
                
                legend.append("text")
                    .attr("x", 0)
                    .attr("y", legendHeight + 15)
                    .style("font-size", "10px")
                    .text("Faible");
                
                legend.append("text")
                    .attr("x", legendWidth)
                    .attr("y", legendHeight + 15)
                    .style("font-size", "10px")
                    .style("text-anchor", "end")
                    .text("Forte");
            }}

            // Initialiser toutes les visualisations
            drawTimeline();
            drawRadar();
            drawHeatmap();
        </script>
    </body>
    </html>
    """

    # Afficher D3.js
    components.html(d3_html, height=1300, scrolling=True)

# ========================================
# TAB 3 — ANALYSE IA
# ========================================

with tab3:
    st.header("🤖 Analyse IA")

    try :
        stream_response = interpret_json("sonalyse_advisor/dps_analysis_pi3_exemple.json", "sonalyse_advisor/context.txt","data/logement1.json")

        try:
            exec(stream_response)
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'exécution du code : {e}")
    except Exception as e:
        st.error(f"Une erreur s'est produite lors de l'analyse IA : {e}")


# FOOTER
st.divider()
st.caption("🚀 Sonalyze Advisor v1.0 - Hackathon IA Boot2Code")
