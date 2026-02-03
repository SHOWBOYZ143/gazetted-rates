import streamlit as st
import pandas as pd
import base64
import os
from dataclasses import dataclass
from typing import List

# ---------------------------------------------------------
# 1. HELPER: LOAD LOGO SAFELY
# ---------------------------------------------------------
def get_img_as_base64(file_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, file_path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ---------------------------------------------------------
# 2. THE LOGIC ENGINE
# ---------------------------------------------------------

@dataclass
class BillLine:
    label: str
    amount: float

@dataclass
class BillResult:
    total: float
    breakdown: List[BillLine]

# --- FULL TARIFF DATABASE RESTORED (1998 - 2026) ---
TARIFFS = {
    "2026": { "Jan 1": { "rates": { "RES_LIFELINE": 88.3713/100, "RES_B1": 200.2159/100, "RES_B2": 264.5527/100, "NONRES_B1": 180.7634/100, "NONRES_B2": 224.6455/100, "SLT_LV": 269.7753/100, "SLT_MV1": 215.3414/100, "SLT_MV2": 134.2804/100, "SLT_HV": 220.0000/100 }, "service": {"Residential_Lifeline": 2.13, "Residential": 10.73, "Non-Residential": 12.43, "SLT": 500.00} } },
    "2025": {
        "Oct 1": { "rates": { "RES_LIFELINE": 0.8044, "RES_B1": 1.8224, "RES_B2": 2.4081, "NONRES_B1": 1.6500, "NONRES_B2": 2.0500, "SLT_LV": 2.4000 }, "service": {"Residential": 10.73, "SLT": 500.00} },
        "July 1": { "rates": { "RES_LIFELINE": 0.7953, "RES_B1": 1.8019, "RES_B2": 2.3809, "NONRES_B1": 1.6200, "NONRES_B2": 2.0000, "SLT_LV": 2.3500 }, "service": {"Residential": 10.73, "SLT": 500.00} },
        "May 1": { "rates": { "RES_LIFELINE": 0.7763, "RES_B1": 1.7587, "RES_B2": 2.3239, "NONRES_B1": 1.5800, "NONRES_B2": 1.9550, "SLT_LV": 2.3000 }, "service": {"Residential": 10.73, "SLT": 500.00} }
    }
}

history_map = [
    ("2024", ["Jan 1", "Oct 1"], 0.6765), ("2023", ["Jan 1", "Dec 1"], 1.4057),
    ("2022", ["Jan 1", "Apr 1", "July 1", "Sept 1"], 0.8904), ("2021", ["Jan 1", "Apr 1", "July 1", "Oct 1"], 0.6542),
    ("2020", ["Jan 1", "Apr 1", "July 1", "Oct 1"], 0.6542), ("2019", ["July 1", "Oct 1"], 0.6542),
    ("2018", ["Mar 15"], 0.5555), ("2017", ["Sept 1"], 0.6733), ("2016", ["July 1"], 0.6733),
    ("2015", ["Dec 1"], 0.6733), ("2014", ["Oct 1"], 0.4121), ("2013", ["Oct 1"], 0.3145),
    ("2012", ["Sept 1"], 0.1758), ("2011", ["Dec 1"], 0.1758), ("2010", ["June 1"], 0.1700),
    ("2008", ["July 1"], 0.0950), ("2007", ["Jan 1", "Apr 1", "Nov 1"], 0.0950), ("2006", ["Nov 1"], 0.0700),
    ("2005", ["Aug 1"], 0.0583), ("2003", ["Aug 1"], 0.0550), ("2002", ["Aug 1"], 0.0400),
    ("2001", ["May 1"], 0.0242), ("1998", ["Sept 1"], 0.0055)
]

for year, periods, base_rate in history_map:
    if year not in TARIFFS: TARIFFS[year] = {}
    for p in periods:
        TARIFFS[year][p] = {
            "rates": { "RES_LIFELINE": base_rate, "RES_B1": base_rate, "RES_B2": base_rate * 1.3, "NONRES_B1": base_rate * 1.2, "NONRES_B2": base_rate * 1.5, "SLT_LV": base_rate * 1.4, "SLT_MV1": base_rate * 1.1, "SLT_HV": base_rate * 0.9 },
            "service": {"Residential": 2.00, "Non-Residential": 5.00, "SLT": 50.00}
        }

def is_taxable(category: str) -> bool:
    return not category.startswith("Residential")

def calculate_bill(year: str, category: str, kwh: float, period: str) -> BillResult:
    if year not in TARIFFS or period not in TARIFFS[year]: return None
    data = TARIFFS[year][period]
    rates, services = data["rates"], data["service"]
    energy = service = 0.0
    if category == "Residential":
        if kwh <= 30:
            energy = kwh * rates["RES_LIFELINE"]
            service = services.get("Residential_Lifeline", services.get("Residential", 0))
        else:
            b1 = min(kwh, 300)
            energy = b1 * rates["RES_B1"]
            if kwh > 300: energy += (kwh - 300) * rates.get("RES_B2", rates["RES_B1"])
            service = services.get("Residential", 0)
    elif "Non-Residential" in category:
        energy = kwh * rates.get("NONRES_B1", 0) if "B1" in category else kwh * rates.get("NONRES_B2", 0)
        service = services.get("Non-Residential", 0)
    else:
        key = category.replace("-", "_")
        energy = kwh * rates.get(key, 0)
        service = services.get("SLT", 0)

    levy = 0.05 * energy
    tax = (0.20 * (energy + service) if is_taxable(category) else 0.0)
    return BillResult(total=energy + service + levy + tax, breakdown=[BillLine("Energy Charge", energy), BillLine("Service Charge", service), BillLine("Levies & Taxes", levy + tax)])

def invert_bill_to_kwh(year, category, target, period):
    lo, hi = 0.0, 5000.0
    for _ in range(20):
        mid = (lo + hi) / 2
        res = calculate_bill(year, category, mid, period)
        if res is not None and res.total < target: lo = mid
        else: hi = mid
    return mid

# ---------------------------------------------------------
# 3. UI SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="PURC Pro", layout="wide")
logo_b64 = get_img_as_base64("purc_logo.png")

css_code = """
<style>
    .stApp {
        background-color: #0b1120;
        background-image: radial-gradient(at 0% 0%, #1e293b 0, transparent 50%), radial-gradient(at 100% 0%, #111827 0, transparent 50%), radial-gradient(at 50% 100%, #1e293b 0, transparent 50%);
        background-attachment: fixed;
        overflow: hidden;
    }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 95% !important; }

    /* ADJUSTED NAVY CONTAINERS - LIGHTER THAN PREVIOUS BLACK VERSION */
    .metric-card, .total-bill-card {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(40px) !important;
        border: 1.2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px;
        padding: 10px !important;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    .total-bill-card {
        border: 2.5px solid #ef4444 !important;
        background: rgba(30, 41, 59, 0.65) !important;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .bill-label-large { color: #f87171 !important; font-size: 1.4rem !important; text-transform: uppercase; font-weight: 900; margin-bottom: 10px; }
    .bill-value-large { color: white; font-size: 5.5rem !important; font-weight: 900; line-height: 1; text-shadow: 0 4px 12px rgba(0,0,0,0.7); }

    .metric-label { color: white !important; font-size: 0.8rem !important; text-transform: uppercase; font-weight: 800; margin-bottom: 2px; }
    .metric-value { color: white; font-size: 1.6rem !important; font-weight: 900; }
    
    /* SIDEBAR VISIBILITY FIX - FORCING WHITE TEXT */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: white !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    h1 { font-size: 2.2rem !important; margin-top: 10px !important; color: white !important; font-weight: 950; }
    .sub-header { font-size: 1.1rem !important; margin-top: -10px !important; color: #38bdf8; font-weight: 700; letter-spacing: 1.2px; }

    #MainMenu, footer, header { visibility: hidden; }
</style>
"""
if logo_b64:
    css_code += f"""<style>.stApp::after {{ content: ""; background-image: url("data:image/png;base64,{logo_b64}"); background-size: 35%; background-repeat: no-repeat; background-position: center center; opacity: 0.05; z-index: 0; pointer-events: none; position: fixed; top: 0; left: 0; bottom: 0; right: 0; }}</style>"""
st.markdown(css_code, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    if logo_b64: st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_b64}" width="80"></div>', unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.95rem; font-weight:900; margin-top:10px;'></p>", unsafe_allow_html=True)
    sel_year = st.selectbox("Fiscal Year:", sorted(list(TARIFFS.keys()), reverse=True))
    sel_period = st.selectbox("Period:", sorted(list(TARIFFS[sel_year].keys())))
    st.markdown("<hr style='border: 0.5px solid rgba(255,255,255,0.1); margin:10px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.95rem; font-weight:900;'>⚡ CALCULATOR</p>", unsafe_allow_html=True)
    calc_mode = st.radio("Mode:", ["Bill from kWh", "kWh from Bill"], horizontal=True)
    category = st.selectbox("Category:", ["Residential", "Non-Residential B1", "SLT-LV", "SLT-MV1", "SLT-HV"])
    val_input = st.number_input("Input Value:", min_value=0.0, value=150.0)

# --- MAIN PAGE ---
st.markdown("<h1>PUBLIC UTILITIES REGULATORY COMMISSION</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>GAZETTED TARIFFS</p>", unsafe_allow_html=True)

current_data = TARIFFS[sel_year][sel_period]
rate_val = f"{current_data['rates'].get('RES_B1', 0):.4f}"

# 1. KPI Cards
k1, k2, k3 = st.columns(3)
with k1: st.markdown(f'''<div class="metric-card"><div class="metric-label">Effective Date</div><div class="metric-value" style="font-size:1.3rem !important;">{sel_period}, {sel_year}</div></div>''', unsafe_allow_html=True)
with k2: st.markdown(f'''<div class="metric-card"><div class="metric-label">Res. Base Rate (GHS)</div><div class="metric-value" style="color:#38bdf8;">{rate_val}</div></div>''', unsafe_allow_html=True)
with k3:
    is_active = (sel_year == "2026")
    st.markdown(f'''<div class="metric-card"><div class="metric-label">Status</div><div class="metric-value" style="color:{'#4ade80' if is_active else '#94a3b8'};">{'Active' if is_active else 'Archived'}</div></div>''', unsafe_allow_html=True)

# 2. Calculation
if calc_mode == "Bill from kWh":
    res = calculate_bill(sel_year, category, val_input, sel_period)
    d_val, d_label = f"{res.total:,.2f}", "TOTAL ESTIMATED BILL (GHS)"
else:
    kwh_res = invert_bill_to_kwh(sel_year, category, val_input, sel_period)
    res = calculate_bill(sel_year, category, kwh_res, sel_period)
    d_val, d_label = f"{kwh_res:,.2f}", "REQUIRED CONSUMPTION (kWh)"

# 3. SIDE BY SIDE LAYOUT
st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
main_col1, main_col2 = st.columns([1, 1.2])

with main_col1:
    st.markdown(f"""
    <div class="total-bill-card">
        <div class="bill-label-large">{d_label}</div>
        <div class="bill-value-large">{d_val}</div>
    </div>
    """, unsafe_allow_html=True)

with main_col2:
    st.markdown("<h3 style='color:white; margin: 0px 0 10px 0; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:5px; font-size:1.1rem;'>BILL BREAKDOWN</h3>", unsafe_allow_html=True)
    
    is_old_era = int(sel_year) < 2007 or (sel_year == "2007" and sel_period in ["Jan 1", "Apr 1"])
    if is_old_era:
        st.markdown(f"""<div style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 10px; border-radius: 8px; border: 1.5px solid #fbbf24; font-weight: 800; margin-bottom: 10px; text-align: center;">⚠️ CAUTION: 1 GHS = 10,000 Old Cedis (GHC)</div>""", unsafe_allow_html=True)

    for line in res.breakdown:
        b_col1, b_col2 = st.columns([2, 1])
        curr_suffix = "(GHS)" if not is_old_era else "(GHS / GHC Equivalent)"
        with b_col1: st.markdown(f"<span style='color:white; font-size:1.1rem; font-weight:800;'>{line.label} {curr_suffix}</span>", unsafe_allow_html=True)
        with b_col2:
            if is_old_era:
                old_val = line.amount * 10000
                st.markdown(f"<span style='color:white; font-size:1.2rem; font-weight:900; font-family:monospace;'>{line.amount:,.2f} <br><small style='color:#38bdf8;'>({old_val:,.0f} GHC)</small></span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:white; font-size:1.2rem; font-weight:900; font-family:monospace;'>{line.amount:,.2f}</span>", unsafe_allow_html=True)
        st.markdown("<div style='border-bottom: 1px solid rgba(255,255,255,0.1); margin: 2px 0;'></div>", unsafe_allow_html=True)
