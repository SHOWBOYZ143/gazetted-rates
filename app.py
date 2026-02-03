import streamlit as st
import base64
import os
from dataclasses import dataclass
from typing import List, Dict

# ----------------------------
# 1. CONSTANTS & CONFIG
# ----------------------------
RES_LIFELINE_MAX = 30.0
BLOCK_300 = 300.0
LEVY_RATE = 0.05
TAX_RATE = 0.20

# ----------------------------
# 2. DATA MODELS
# ----------------------------
@dataclass
class BillLine:
    label: str
    amount: float

@dataclass
class BillResult:
    year: str
    period: str
    category: str
    kwh: float
    energy_charge: float
    service_charge: float
    levy: float
    tax: float
    total: float
    breakdown: List[BillLine]

# ----------------------------
# 3. TARIFF DATA
# ----------------------------
TARIFFS = {
    "2026": {
        "Feb 1": {
            "rates": {
                "RES_LIFELINE": 88.3739 / 100, "RES_B1": 200.2218 / 100, "RES_B2": 264.5604 / 100,
                "NONRES_B1": 180.7687 / 100, "NONRES_B2": 224.6521 / 100,
                "SLT_LV": 269.7832 / 100, "SLT_MV1": 215.3477 / 100, "SLT_MV2": 134.2804 / 100, "SLT_HV": 215.3477 / 100,
            },
            "service": {
                "Residential (Lifeline)": 2.13, "Residential (Other)": 10.730886,
                "Non-Residential": 12.428245, "SLT": 500.00,
            }
        }
    },
    "2025": {
        "Feb 1": {
            "rates": {
                "RES_LIFELINE": 80.4389 / 100, "RES_B1": 182.2442 / 100, "RES_B2": 240.8059 / 100,
                "NONRES_B1": 164.5377 / 100, "NONRES_B2": 204.4809 / 100,
                "SLT_LV": 245.5597 / 100, "SLT_MV1": 196.0119 / 100, "SLT_MV2": 127.8861 / 100, "SLT_HV": 196.0119 / 100,
            },
            "service": {
                "Residential (Lifeline)": 2.13, "Residential (Other)": 10.7301,
                "Non-Residential": 12.428, "SLT": 500.00,
            }
        }
    }
}

history_data = [
    ("2024", ["Jan 1", "Apr 1", "Jul 1", "Oct 1"], 0.6765), ("2023", ["Jan 1", "Dec 1"], 1.4057),
    ("2022", ["Jan 1", "Apr 1", "Jul 1", "Sept 1"], 0.8904), ("2021", ["Jan 1", "Oct 1"], 0.6542),
    ("2020", ["Jan 1", "Apr 1", "Jul 1", "Oct 1"], 0.6542), ("2019", ["July 1", "Oct 1"], 0.6542),
    ("2018", ["Mar 15"], 0.5555), ("2017", ["Sept 1"], 0.6733), ("2016", ["July 1"], 0.6733),
    ("2015", ["Dec 1"], 0.6733), ("2014", ["Oct 1"], 0.4121), ("2013", ["Oct 1"], 0.3145),
    ("2012", ["Sept 1"], 0.1758), ("2011", ["Dec 1"], 0.1758), ("2010", ["June 1"], 0.1700),
    ("2008", ["July 1"], 0.0950), ("2007", ["Jan 1", "Apr 1", "Nov 1"], 0.0950),
    ("2006", ["Nov 1"], 0.0700), ("2005", ["Aug 1"], 0.0583), ("2003", ["Aug 1"], 0.0550),
    ("2002", ["Aug 1"], 0.0400), ("2001", ["May 1"], 0.0242), ("1998", ["Sept 1"], 0.0055)
]

for year, periods, base in history_data:
    if year not in TARIFFS: TARIFFS[year] = {}
    for p in periods:
        TARIFFS[year][p] = {
            "rates": {
                "RES_LIFELINE": base, "RES_B1": base, "RES_B2": base * 1.3,
                "NONRES_B1": base * 1.2, "NONRES_B2": base * 1.5,
                "SLT_LV": base * 1.5, "SLT_MV1": base * 1.1,
                "SLT_MV2": base * 0.8, "SLT_HV": base * 0.9,
            },
            "service": {
                "Residential (Lifeline)": 2.13, "Residential (Other)": 10.73,
                "Non-Residential": 12.42, "SLT": 100.00,
            }
        }

# ----------------------------
# 4. ENGINES (Calculation & Reverse)
# ----------------------------
def is_taxable(category: str) -> bool:
    return not category.startswith("Residential")

def calculate_bill(year: str, period: str, category: str, kwh: float) -> BillResult:
    if year not in TARIFFS or period not in TARIFFS[year]: return None
    tariff = TARIFFS[year][period]; rates = tariff["rates"]; services = tariff["service"]
    breakdown = []
    if category == "Residential":
        if kwh <= RES_LIFELINE_MAX:
            energy = kwh * rates["RES_LIFELINE"]; service = services["Residential (Lifeline)"]
            breakdown.append(BillLine("Energy Charge (GHS)", energy))
        else:
            kwh_b1 = min(kwh, BLOCK_300); kwh_b2 = max(0.0, kwh - BLOCK_300)
            e1 = kwh_b1 * rates["RES_B1"]; e2 = kwh_b2 * rates["RES_B2"]
            energy = e1 + e2; service = services["Residential (Other)"]
            breakdown.append(BillLine("Energy Charge (GHS)", energy))
    elif category == "Non-Residential":
        kwh_b1 = min(kwh, BLOCK_300); kwh_b2 = max(0.0, kwh - BLOCK_300)
        energy = (kwh_b1 * rates["NONRES_B1"]) + (kwh_b2 * rates["NONRES_B2"])
        service = services["Non-Residential"]
        breakdown.append(BillLine("Energy Charge (GHS)", energy))
    else:
        rate_key = category.replace("-", "_")
        energy = kwh * rates.get(rate_key, rates["SLT_LV"])
        service = services["SLT"]
        breakdown.append(BillLine("Energy Charge (GHS)", energy))
    levy = LEVY_RATE * energy; tax = TAX_RATE * (energy + service) if is_taxable(category) else 0.0
    breakdown.append(BillLine("Service Charge (GHS)", service))
    breakdown.append(BillLine("Levies & Taxes (GHS)", levy + tax))
    return BillResult(year, period, category, kwh, energy, service, levy, tax, energy + service + levy + tax, breakdown)

def calculate_kwh_from_bill(year: str, period: str, category: str, target: float) -> float:
    if year not in TARIFFS or period not in TARIFFS[year]: return 0.0
    tariff = TARIFFS[year][period]; rates = tariff["rates"]; services = tariff["service"]
    taxable = is_taxable(category); mult_E = 1.25 if taxable else 1.05; mult_S = 1.20 if taxable else 1.0
    if category == "Non-Residential":
        s = services["Non-Residential"] * mult_S
        if target <= s: return 0.0
        m = (target - s) / mult_E
        c_max = BLOCK_300 * rates["NONRES_B1"]
        return m / rates["NONRES_B1"] if m <= c_max else 300 + (m - c_max) / rates["NONRES_B2"]
    elif category == "Residential":
        s_life = services["Residential (Lifeline)"]; c_life = (RES_LIFELINE_MAX * rates["RES_LIFELINE"] * 1.05) + s_life
        if target <= c_life: return 0.0 if target <= s_life else (target - s_life) / (rates["RES_LIFELINE"] * 1.05)
        s_other = services["Residential (Other)"]; c_b1 = (BLOCK_300 * rates["RES_B1"] * 1.05) + s_other
        return (target - s_other) / (rates["RES_B1"] * 1.05) if target <= c_b1 else 300 + (target - c_b1) / (rates["RES_B2"] * 1.05)
    else:
        s = services["SLT"] * mult_S; r = rates.get(category.replace("-", "_"), rates["SLT_LV"])
        return 0.0 if target <= s else ((target - s) / mult_E) / r

# ----------------------------
# 5. UI SETUP
# ----------------------------
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

st.set_page_config(page_title="PURC Pro", layout="wide", initial_sidebar_state="collapsed")
logo_b64 = get_img_as_base64("purc_logo.png")

# --- UPDATE THIS SECTION IN YOUR CODE ---
st.markdown("""
<style>
    /* 1. HIDE THE TOP WHITE BAR */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* 2. LOCK WINDOW HEIGHT & DISABLE SCROLLING */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 3. PUSH CONTENT TO THE TOP */
    .block-container {
        padding-top: 0rem !important;
        max-width: 1100px !important;
        margin: auto;
    }
</style>
""", unsafe_allow_html=True)

if logo_b64: st.markdown(f'<div style="text-align: center; margin-top:0px;"><img src="data:image/png;base64,{logo_b64}" width="200"></div>', unsafe_allow_html=True)
st.markdown("<h1>PUBLIC UTILITIES REGULATORY COMMISSION</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>GAZETTED TARIFFS</p>", unsafe_allow_html=True)

# --- TIER 1: INPUTS ---
# We keep this as a simple 3-column row
c1, c2, c3 = st.columns(3)
with c1:
    sel_year = st.selectbox("Fiscal Year:", sorted(list(TARIFFS.keys()), reverse=True))
with c2:
    val_input = st.number_input("Enter Value:", min_value=0.0, value=150.0)
with c3:
    category = st.selectbox("Customer Category:", ["Residential", "Non-Residential", "SLT-LV", "SLT-MV1", "SLT-MV2", "SLT-HV"])

# --- TIER 2 & 3: PREFERENCES & RESULTS (Combined for Alignment) ---
# 1. Logic Setup
periods = sorted(list(TARIFFS[sel_year].keys()))
auto_p = periods[0] if periods else "Standard"

# 2. Create the 3-column grid for Results
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    # PREFERENCE now sits exactly under 'Fiscal Year'
    st.markdown('<p style="font-size:20px; font-weight:800; margin-top:20px;">PREFERENCE</p>', unsafe_allow_html=True)
    calc_mode = st.radio(
        "Res",
        ["Bill from kWh", "kWh from Bill"],
        horizontal=True,
        label_visibility="collapsed",
        key="unique_calc_mode"
    )

# 3. Run Calculations based on the radio selection above
if calc_mode == "Bill from kWh":
    kwh = val_input
    res = calculate_bill(sel_year, auto_p, category, kwh)
else:
    kwh = calculate_kwh_from_bill(sel_year, auto_p, category, val_input)
    res = calculate_bill(sel_year, auto_p, category, kwh)

with res_col2:
    # TOTAL now sits exactly under 'Enter Value'
    l = "TOTAL ESTIMATED BILL (GHS)" if calc_mode == "Bill from kWh" else "REQUIRED CONSUMPTION (kWh)"
    display_val = res.total if calc_mode == "Bill from kWh" else kwh
    
    st.markdown(f'<p style="font-size:20px; font-weight:800; color:#ef4444; margin-top:20px;">{l}</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:3rem; font-weight:900; margin-top:-15px;">{display_val:,.2f}</p>', unsafe_allow_html=True)

with res_col3:
    # BREAKDOWN now sits exactly under 'Customer Category'
    st.markdown("<p style='font-weight:950; border-bottom:2px solid #38bdf8; font-size:1.2rem; padding-bottom:5px; margin-top:20px;'>🧾 BILL BREAKDOWN</p>", unsafe_allow_html=True)
    # RESTORED: OLD CURRENCY WARNING
    if int(sel_year) <= 2007:
        st.markdown(f'<div style="background: rgba(245, 158, 11, 0.2); color: #fbbf24 !important; padding: 10px; border: 2px solid #fbbf24; font-weight: 900; margin-bottom: 15px; text-align: center;">⚠️ 1 GHS = 10,000 Old Cedis (GHC)</div>', unsafe_allow_html=True)
    
    if res and res.breakdown:
        for line in res.breakdown:
            b1, b2 = st.columns([2, 1])
            b1.markdown(f"**{line.label}**")
            b2.markdown(f"<p style='text-align:right; font-family:monospace; font-size:1.1rem; font-weight:900;'>{line.amount:,.2f}</p>", unsafe_allow_html=True)
            st.markdown("<div style='border-bottom: 1px solid rgba(255,255,255,0.1); margin: 3px 0;'></div>", unsafe_allow_html=True)
