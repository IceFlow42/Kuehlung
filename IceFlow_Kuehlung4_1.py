from PIL import Image
import streamlit as st
import numpy as np

# --- Grundkonstanten der Physik ---
CP_GETRAENK = 4182  # Spezifische Wärmekapazität von Wasser in J/(kg·K)
CP_EIS = 2090       # Spezifische Wärmekapazität von Eis in J/(kg·K)
LF_EIS = 334000     # Spezifische Schmelzenthalpie von Eis in J/kg
T_EIS_START = -18   # Standard-Temperatur von Eis aus dem Tiefkühler in °C

# --- Geometrie der Getränke (Masse und Oberfläche) ---
# Annahmen basierend auf Standard-Dosen
GETRAENKE_DATEN = {
    "330 ml": {"masse": 0.33, "oberflaeche": 0.038},
    "500 ml": {"masse": 0.50, "oberflaeche": 0.050}
}

# --- UI-Konfiguration und Titel ---
logo = Image.open("IceFlow.jpeg")
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image(logo, width=300)  # Breite kannst du anpassen

st.set_page_config(page_title="IceFlow- Der Getränkekühlung-Rechner", layout="wide")
st.title("IceFlow - Tool zur Berechnung der Getränkekühlung 🥤")
st.markdown("""
Dieses Tool berechnet die theoretische Abkühlzeit für ein Getränk, das in einem Eisbad durch Rotation gekühlt wird. 
Zusätzlich wird die Gesamtkapazität von 1 kg Eis abgeschätzt.
""")

# --- Eingabeparameter in der Sidebar ---
st.sidebar.header("Ihre Einstellungen")

getraenk_groesse = st.sidebar.selectbox(
    "Wählen Sie die Getränkegröße:",
    options=list(GETRAENKE_DATEN.keys())
)

t_start = st.sidebar.slider(
    "Starttemperatur des Getränks (°C)",
    min_value=0, max_value=30, value=22, step=1
)

t_ziel = st.sidebar.slider(
    "Zieltemperatur des Getränks (°C)",
    min_value=0, max_value=12, value=6, step=1
)

# Hole die spezifischen Daten für das ausgewählte Getränk
m_getraenk = GETRAENKE_DATEN[getraenk_groesse]["masse"]
a_getraenk = GETRAENKE_DATEN[getraenk_groesse]["oberflaeche"]

st.sidebar.markdown("---")

# --- Einstellungen für das Kühlmedium ---
rotation = st.sidebar.slider(
    "Rotation (U/min)",
    min_value=0, max_value=400, value=400, step=10
)

eis_typ = st.sidebar.selectbox(
    "Art des Eises (Kontaktfläche)",
    options=["Große Eiswürfel", "Kleine Eiswürfel", "Crushed Ice"]
)

salz_menge_prozent = st.sidebar.slider(
    "Relative Salzmenge (%)",
    min_value=0, max_value=100, value=80, step=5,
    help="0% = reines Eis, 30% = optimale Salzmenge, 100% = 1:1 Verhältnis von Eis und Salz."
)


# --- Berechnungslogik ---

# 1. Temperatur des Kühlmediums basierend auf Salzmenge
# Lineares Modell: 0% Salz -> 0°C, 100% Salz -> -21°C
t_kuehlmedium = 0 - (21 * (salz_menge_prozent / 100.0))

# 2. Wärmeübergangskoeffizient 'h' abschätzen
# Dies ist ein empirisches Modell, das die Effekte von Eisart und Rotation kombiniert
h_basis = 150  # Basiswert für große Würfel, keine Rotation, natürliche Konvektion

# Faktor für die Eisart
if eis_typ == "Kleine Eiswürfel":
    eis_faktor = 1.4
elif eis_typ == "Crushed Ice":
    eis_faktor = 1.8
else: # Große Eiswürfel
    eis_faktor = 1.0

# Faktor für die Rotation (erzwungene Konvektion)
# Einfaches Modell: Faktor steigt von 1 (bei 0 U/min) bis 5 (bei 400 U/min)
rotations_faktor = 1 + 4 * (rotation / 400.0)

h = h_basis * eis_faktor * rotations_faktor

# 3. Berechnung der Abkühlkonstante 'k'
k = (h * a_getraenk) / (m_getraenk * CP_GETRAENK)


# --- Anzeige der Ergebnisse ---
col1, col2 = st.columns(2)

with col1:
    st.header("⏱️ Berechnung der Kühlzeit")

    # Logik-Prüfungen vor der Berechnung
    if t_start <= t_ziel:
        st.warning("Die Starttemperatur muss höher als die Zieltemperatur sein.")
        zeit_sekunden = 0
    elif t_ziel < t_kuehlmedium:
        st.error(f"Die Zieltemperatur ({t_ziel}°C) kann nicht erreicht werden, da sie unter der Temperatur des Kühlmediums ({t_kuehlmedium:.1f}°C) liegt.")
        zeit_sekunden = -1
    else:
        # Finale Zeitberechnung nach Newtons Abkühlungsgesetz
        ln_term = (t_ziel - t_kuehlmedium) / (t_start - t_kuehlmedium)
        zeit_sekunden = (-1 / k) * np.log(ln_term)

    # Anzeige des Ergebnisses
    if zeit_sekunden > 0:
        minuten, sekunden = divmod(zeit_sekunden, 60)
        st.success(f"Geschätzte Kühlzeit: **{int(minuten)} Minuten und {int(sekunden)} Sekunden**")
        st.metric(label="Zeit in Sekunden", value=f"{zeit_sekunden:.1f} s")
    
    st.subheader("Berechnete Systemparameter")
    st.markdown(f"""
    - **Kühlmedium-Temperatur:** `{t_kuehlmedium:.1f} °C`
    - **Geschätzter Wärmeübergangskoeffizient (h):** `{h:.0f} W/(m²·K)`
    """)
    st.info("Hinweis: Dies ist eine theoretische Berechnung. Reale Zeiten können durch Faktoren wie Behältermaterial und Isolierung abweichen.")


with col2:
    st.header("🧊 Berechnung der Kühlkapazität")
    st.markdown("Wie viele Getränke können mit **1 kg Eis** gekühlt werden?")

    # Energie, die pro Getränk entzogen werden muss
    delta_t_getraenk = t_start - t_ziel
    if delta_t_getraenk > 0:
        q_getraenk = m_getraenk * CP_GETRAENK * delta_t_getraenk

        # Energie, die 1kg Eis aufnehmen kann (Erwärmung + Schmelzen)
        q_eis_erwaermung = 1.0 * CP_EIS * (0 - T_EIS_START)
        q_eis_schmelzen = 1.0 * LF_EIS
        q_eis_total = q_eis_erwaermung + q_eis_schmelzen

        # Finale Kapazitätsberechnung
        anzahl_getraenke = q_eis_total / q_getraenk
        
        st.success(f"Theoretische Kapazität: **ca. {anzahl_getraenke:.1f} Getränke**")
        
        st.metric(label="Energie pro Getränk", value=f"{q_getraenk/1000:.1f} kJ")
        st.metric(label="Gesamtkapazität von 1kg Eis", value=f"{q_eis_total/1000:.1f} kJ")
        
        st.info("""
        **Wichtig:** Die Salzmenge und Rotation beeinflussen die *Geschwindigkeit*, aber kaum die *Gesamtkapazität* des Eises. 
        In der Praxis wird die reale Anzahl etwas geringer sein, da Wärme aus der Umgebung aufgenommen wird.
        """)
    else:
        st.warning("Keine Kühlung erforderlich, daher keine Kapazitätsberechnung möglich.")

st.markdown("---")
st.subheader("Physikalische Hintergründe")
st.markdown("""
- **Rotation:** Erhöht den Wärmeübergangskoeffizienten (h) durch *erzwungene Konvektion*. Die Wärme wird viel schneller von der Dose an das umgebende Schmelzwasser abgegeben.
- **Salz:** Senkt den Schmelzpunkt des Eises (Gefrierpunkterniedrigung). Dadurch entsteht ein extrem kaltes Schmelzwasser (Salzlake), was die Temperaturdifferenz und damit die Kühlgeschwindigkeit drastisch erhöht.
- **Eis-Typ:** Beeinflusst die Kontaktfläche zwischen Dose und Kühlmedium. Crushed Ice bietet die größte Fläche und damit den besten Wärmeübergang.
""")