import streamlit as st

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sonalyse_advisor.agent_backend import interpret_json

st.set_page_config(page_title="Sonalyze Diagnostic", page_icon="🔊", layout="wide")

# ========================================
# 🔒 CHARGEMENT DES DONNÉES (DÉSACTIVÉ)
# ========================================

"""
# FONCTION dataload — Désactivée pour garder uniquement l’UI

@st.cache_data
def load_data():
    with open('data/dps_analysis_pi3_exemple.json', 'r') as f:
        analysis_data = json.load(f)
    
    with open('data/Config_AI_Classification.json', 'r') as f:
        config_data = json.load(f)
    
    return analysis_data, config_data

try:
    data, config = load_data()
except FileNotFoundError:
    st.stop()
"""

# valeurs placeholders 
stats = {
    "avg_db_day": 42.5,
    "avg_db_night": 33.2,
    "max_db": 78.0,
    "min_db": 22.0
}

grade = "C"

logement = {"nom": "Logement Exemple"}
piece = {"nom": "Chambre"}

st.title("🔊 Diagnostic Sonalyze")
st.markdown("*Votre diagnostic de performance sonore*")

st.caption(f"📍 {logement['nom']} - {piece['nom']}")
st.divider()

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["📊 Synthèse", "📈 Graphiques", "🤖 Analyse IA", "💡 Recommandations"])

# ========================================
# TAB 1 — SYNTHÈSE
# ========================================
with tab1:
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        colors = {
            'A': '#00AA00', 'B': '#55CC00', 'C': '#AADD00', 
            'D': '#FFEE00', 'E': '#FFAA00', 'F': '#FF5500', 'G': '#DD0000'
        }
        st.markdown(f"""
            <div style='text-align: center; padding: 50px; background-color: {colors[grade]}; 
                        border-radius: 20px; margin: 30px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h1 style='font-size: 140px; margin: 0; color: white; font-weight: bold;'>{grade}</h1>
                <p style='font-size: 28px; color: white; margin: 10px 0;'>Note de votre logement</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("☀️ Niveau jour", f"{stats['avg_db_day']} dB")
    col2.metric("🌙 Niveau nuit", f"{stats['avg_db_night']} dB")
    col3.metric("📈 Maximum", f"{stats['max_db']} dB")
    col4.metric("📉 Minimum", f"{stats['min_db']} dB")

    st.divider()

    st.subheader("🎯 En résumé")
    st.warning("""
    ⚠️ Exemple d'interprétation – l'agent IA sera intégré plus tard.
    """)

# ========================================
# TAB 2 — GRAPHIQUES  cndt #todo 
# ========================================

with tab2:
    st.header("📈 Visualisation")
    st.info("🔧 Graphiques basés sur des données fictives pour la démonstration.")

    df_hourly = pd.DataFrame({
        "hour": list(range(24)),
        "db_level": [42, 38, 37, 35, 34, 33, 32, 40, 45, 50, 55, 60,
                     63, 65, 62, 58, 55, 50, 48, 46, 44, 43, 41, 40]
    })

    fig = px.line(df_hourly, x="hour", y="db_level", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# ========================================
# TAB 3 — ANALYSE IA  agent #todo
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
# TAB 4 — RECOMMANDATIONS #  todo 
# ========================================

with tab4:
    st.header("💡 Recommandations")
    st.info("Suggestions génériques pour démonstration.")
    st.write("- Installer des joints de fenêtre")
    st.write("- Rideaux phoniques")
    st.write("- Survitrage")


# FOOTER
st.divider()
st.caption("Prototype UI – Logique désactivée")
