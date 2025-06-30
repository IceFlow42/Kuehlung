import math
import streamlit as st

from PIL import Image

# Konstanten
C_BIER = 4180  # J/(kg*K), spezifische Wärmekapazität von Wasser/Bier
H_WERT = 150  # W/(m^2*K), angenommener Wärmeübergangskoeffizient (wird durch Rotation erhöht)

# Kontaktfaktoren basierend auf Eisstruktur
KONTAKTFAKTOREN = {
    "Große Eiswürfel (50 % Kontakt)": 0.5,
    "Kleine Eiswürfel (75 % Kontakt)": 0.75,
    "Crushed Ice / Slush (95 % Kontakt)": 0.95
}

# Benutzeroberfläche
logo = Image.open("IceFlow.jpeg")
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image(logo, width=210)  # Breite kannst du anpassen

st.markdown("</div>", unsafe_allow_html=True)

st.title("Bierkühlung mit Eis – ")
st.subheader("Cooler Kopf. Kaltes Bier. Berechnet mit IceFlow.")

# Eingaben
start_temp = st.slider("Starttemperatur des Biers (°C)", 5.0, 30.0, 20.0)
ziel_temp = st.slider("Zieltemperatur des Biers (°C)", 0.0, 15.0, 8.0)

biergroesse = st.selectbox("Dosengröße", ["0.33 L", "0.5 L"])
volumen_bier = 0.33 if biergroesse == "0.33 L" else 0.5
masse_bier = volumen_bier  # in kg, Dichte ≈ 1 kg/L

rotation = st.slider("Rotationsgeschwindigkeit (U/min)", 0, 1000, 200)
eisstruktur = st.selectbox("Eisstruktur", list(KONTAKTFAKTOREN.keys()))
kontaktfaktor = KONTAKTFAKTOREN[eisstruktur]

salzmenge = st.slider("Salzmenge im Eisbad (kg)", 0.0, 0.3, 0.01)

# Oberfläche der Dose (Zylinder + Deckel): genähert
hoehe_dose = 0.115 if volumen_bier == 0.33 else 0.168  # in m
radius_dose = 0.033  # in m
oberflaeche_dose = 2 * math.pi * radius_dose**2 + 2 * math.pi * radius_dose * hoehe_dose

effektive_oberflaeche = oberflaeche_dose * kontaktfaktor

# Wärmeübergangskoeffizient dynamisch anpassen
if rotation == 0:
    h_eff = 100  # sehr geringer Übergang
elif rotation < 300:
    h_eff = H_WERT + rotation * 1.5
else:
    h_eff = 600 + (rotation - 300) * 0.3  # abflachend

# Temperatur des Eis-Salz-Bads (vereinfachte Gefrierpunktdepression)
T_BAD = min(0, -1.86 * (salzmenge / (1 + salzmenge)))

# Benötigte Wärmemenge
Q = masse_bier * C_BIER * (start_temp - ziel_temp)

# Übertragbare Wärmeenergie durch Eisbad (angenommen max 1 kg Eis im Kontakt)
MASSE_EIS_MAX = 1.0  # kg, maximaler Kontaktbereich
SCHMELZWÄRME_EIS = 334000  # J/kg
Q_MAX = MASSE_EIS_MAX * SCHMELZWÄRME_EIS

# Effektive Kühlrate
delta_T_mittel = (start_temp - T_BAD + ziel_temp - T_BAD) / 2
waermefluss = h_eff * effektive_oberflaeche * delta_T_mittel  # in Watt

if Q > Q_MAX:
    st.error("Zieltemperatur nicht erreichbar: zu wenig Eis im Kontakt. Nur {:.1f} °C wären erreichbar.".format(
        start_temp - (Q_MAX / (masse_bier * C_BIER))
    ))
else:
    zeit = Q / waermefluss  # in Sekunden
    st.success("Kühlzeit: {:.1f} Sekunden (≈ {:.1f} Minuten)".format(zeit, zeit / 60))

# Debug-Anzeige (optional)
st.write("**Details:**")
st.write(f"Effektive Oberfläche: {effektive_oberflaeche:.4f} m²")
st.write(f"Wärmeübergangskoeffizient: {h_eff:.1f} W/m²K")
st.write(f"Eisbad-Temperatur: {T_BAD:.2f} °C")
st.write(f"Benötigte Energie: {Q:.0f} J")
st.write(f"Maximale Kühlenergie aus Eis: {Q_MAX:.0f} J")
