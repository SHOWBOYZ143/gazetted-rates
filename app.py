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
    is_old_currency: bool = False

@dataclass
class BillResult:
    total: float
    breakdown: List[BillLine]
    currency_label: str

# Constants
RES_LIFELINE_MAX = 30.0
BLOCK_300 = 300.0

# --- TARIFF DATABASE (RESTORING FULL HISTORY) ---
TARIFFS = {
    "2026": {
        "Q1": {
            "rates": {"RES_LIFELINE": 88.3713/100, "RES_B1": 200.2159/100, "RES_B2": 264.5527/100, "NONRES_B1": 180.7634/100, "NONRES_B2": 224.6455/100, "SLT_LV": 269.7753/100},
            "service": {"Residential_Lifeline": 2.13, "Residential": 10.730886, "Non-Residential": 12.428245, "SLT": 500.00}
        }
    },
    "2025": {
        "May": { "rates": {"RES_LIFELINE": 77.6274/100, "RES_B1": 175.8743/100, "RES_B2": 232.3892/100}, "service": {"Residential": 10.73} },
        "July": { "rates": {"RES_LIFELINE": 79.5308/100, "RES_B1": 180.1867/100, "RES_B2": 238.0873/100}, "service": {"Residential": 10.73} },
        "Oct": { "rates": {"RES_LIFELINE": 80.4389/100, "RES_B1": 182.2442/100, "RES_B2": 240.8059/100}, "service": {"Residential": 10.73} }
    },
    "2024": { "Oct": { "rates": {"RES_LIFELINE": 67.6495/100, "RES_B1": 153.2683/100, "RES_B2": 202.5190/100}, "service": {"Residential": 10.73} } },
    "2023": { "Dec": { "rates": {"RES_LIFELINE": 63.4792/100, "RES_B1": 140.5722/100}, "service": {"Residential": 10.73} } }
}

# --- AUTOMATICALLY FILL 1998-2022 FROM TRENDS ---
# This block ensures all your historical years appear in the dropdown
history_map = [
    ("2022", 0.8904), ("2021", 0.6542), ("2020", 0.6542), ("2019", 0.6542), 
    ("2018", 0.5555), ("2017", 0.6733), ("2016", 0.6733), ("2015", 0.6733), 
    ("2014", 0.4121), ("2013", 0.3145), ("2012", 0.1758), ("2011", 0.1758), 
    ("2010", 0.1700), ("2008", 0.0950), ("2007", 0.0950), ("2006", 0.0700), 
    ("2005", 0.0583), ("2003", 0.0550), ("2002", 0.0400), ("2001", 0.0242), 
    ("1998", 0.0055)
]

for year, base_rate in history_map:
    if year not in TARIFFS:
        TARIFFS[year] = {
            "Standard": {
                "rates": {
                    "RES_LIFELINE": base_rate, 
                    "RES_B1": base_rate, 
                    "RES_B2": base_rate,
                    "NONRES_B1": base_rate
                },
                "service": {"Residential": 0.0} # Service charge assumed 0 for older history simplifiction
            }
        }

def is_taxable(category: str) -> bool:
    return not category.startswith("Residential")

def calculate_bill(year: str, category: str, kwh: float, period: str = "Q1") -> BillResult:
    if year not in TARIFFS: return None
    # Auto-select first period if the specific one isn't found
    if period not in TARIFFS[year]: period = list(TARIFFS[year].keys())[0]

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
            if kwh > 300:
                b2 = min(kwh - 300, 300)
                energy += b2 * rates.get("RES_B2", rates["RES_B1"])
            service = services.get("Residential", 0)
    elif category == "Non-Residential":
        energy = kwh * rates.get("NONRES_B1", 0) 
        service = services.get("Non-Res", services.get("Non-Residential", 0))
    else: 
        energy = kwh * rates.get("SLT_LV", 0)
        service = services.get("SLT", 0)

    levy = 0.05 * energy
    tax = (0.20 * (energy + service) if is_taxable(category) else 0.0)
    
    return BillResult(total=energy + service + levy + tax, breakdown=[
        BillLine("Energy Charge (GHS)", energy), 
        BillLine("Service Charge (GHS)", service), 
        BillLine("Levies & Taxes (GHS)", levy + tax)
    ], currency_label="GHS")

def invert_bill_to_kwh(year, category, target, period):
    lo, hi = 0.0, 5000.0
    for _ in range(20):
        mid = (lo + hi) / 2
        res = calculate_bill(year, category, mid, period)
        if res.total < target: lo = mid
        else: hi = mid
    return mid

# ---------------------------------------------------------
# 3. UI SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="PURC Pro Dashboard", layout="wide")

# Prepare Logo
logo_filename = "purc_logo.png"
logo_b64 = get_img_as_base64(logo_filename)

# BASE CSS (Original Vibrant Look)
css_code = """
<style>
    .stApp { 
        background-color: #0f172a; 
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%); 
        background-attachment: fixed; 
    }
"""

if logo_b64:
    css_code += f"""
    .stApp::after {{
        content: "";
        background-image: url("data:image/png;base64,{logo_b64}");
        background-size: 35%;
        background-repeat: no-repeat;
        background-position: center center;
        opacity: 0.12; 
        position: fixed;
        top: 0; left: 0; bottom: 0; right: 0;
        z-index: 0;
        pointer-events: none;
        filter: grayscale(100%) contrast(1.5);
    }}
    """

css_code += """
    .glass-container { 
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(20px); 
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255, 255, 255, 0.3); 
        border-left: 1px solid rgba(255, 255, 255, 0.3); 
        border-radius: 24px; 
        padding: 25px; 
        margin-bottom: 25px; 
        position: relative; 
        z-index: 1;
    }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 800 !important; text-shadow: 0px 3px 6px rgba(0, 0, 0, 0.8) !important; position: relative; z-index: 1; }
    .stSelectbox label, .stNumberInput label, .stRadio label, p { color: #ffffff !important; font-weight: 700 !important; font-size: 0.95rem !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.8) !important; opacity: 1 !important; }
    .label-text { color: #f8fafc; font-size: 0.85rem; text-transform: uppercase; font-weight: 800; text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.9); margin-bottom: 5px; }
    .value-text { font-size: 2.8rem; font-weight: 900; color: #ffffff; text-shadow: 0px 4px 12px rgba(0, 0, 0, 0.9); }
    .breakdown-label { color: #e2e8f0; font-weight: 600; text-shadow: 0px 1px 3px rgba(0,0,0,0.9); }
    .breakdown-value { color: #ffffff; font-weight: 700; font-family: monospace; font-size: 1.1rem; text-shadow: 0px 1px 3px rgba(0,0,0,0.9); }
    .status-active { color: #4ade80; text-shadow: 0px 0px 15px rgba(74, 222, 128, 0.6); }
    .status-archived { color: #cbd5e1; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; position: relative; z-index: 1; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255,255,255,0.1); border-radius: 30px; color: #ffffff; border: 1px solid rgba(255,255,255,0.2); padding: 0px 30px; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%) !important; color: white !important; border: none !important; }
    [data-testid="stDataFrame"] { position: relative; z-index: 1; }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

st.markdown("<h1>GAZETTED TARIFFS</h1>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["OVERVIEW", "CALCULATOR", "TRENDS"])

with tab1:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col_sel, col_q, col_space = st.columns([1, 1, 2])
    with col_sel:
        # Sort years descending
        all_years = sorted(list(TARIFFS.keys()), reverse=True)
        sel_year = st.selectbox("Select Fiscal Year:", all_years, index=0)
    with col_q:
        q_opts = list(TARIFFS[sel_year].keys())
        sel_period = st.selectbox("Select Period / Quarter:", q_opts)

    rate_val = "N/A"
    current_data = TARIFFS[sel_year][sel_period]
    if "rates" in current_data:
        r = current_data["rates"]
        val = r.get("RES_B1", r.get("RES_LIFELINE", 0))
        rate_val = f"{val:.4f}"

    c1, c2, c3 = st.columns(3)
    with c1: 
        st.markdown(f'''<div class="glass-container"><div class="label-text">Effective Date</div><div class="value-text">{sel_period}, {sel_year}</div></div>''', unsafe_allow_html=True)
    with c2: 
        st.markdown(f'''<div class="glass-container"><div class="label-text">Res. Base Rate (GHS)</div><div class="value-text" style="color:#38bdf8;">{rate_val}</div></div>''', unsafe_allow_html=True)
    
    status_cls = "status-active" if sel_year == "2026" else "status-archived"
    status_txt = "Active" if sel_year == "2026" else "Archived"
    with c3: 
        st.markdown(f'''<div class="glass-container"><div class="label-text">Status</div><div class="value-text {status_cls}">{status_txt}</div></div>''', unsafe_allow_html=True)

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    bot1, bot2 = st.columns([2, 1])
    
    with bot1:
        st.markdown('<h3 style="margin-bottom: 15px;">📋 Full Tariff Schedule</h3>', unsafe_allow_html=True)
        if "rates" in current_data:
            rates_dict = current_data["rates"]
            table_data = []
            for k, v in rates_dict.items():
                clean_name = k.replace("RES_", "Residential ").replace("NONRES_", "Non-Res ").replace("SLT_", "SLT ").replace("_", " ")
                table_data.append({"Category": clean_name, "Rate (GHS/kWh)": f"{v:.4f}"})
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    with bot2:
        st.markdown('<h3 style="margin-bottom: 15px;">💡 Quick Notes</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-container" style="padding: 20px; border-left: 4px solid #38bdf8;">
            <p style="font-size: 0.85rem; margin-bottom: 10px;"><strong>Lifeline:</strong> Subsidized rate for < 30 kWh.</p>
            <p style="font-size: 0.85rem; margin-bottom: 10px;"><strong>Service Charge:</strong> Fixed monthly fee.</p>
            <p style="font-size: 0.85rem; margin-bottom: 0px;"><strong>SLT:</strong> Special Load Tariff (Industrial).</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="glass-container"><h2 style="color:white; margin:0;">Bill Simulator</h2></div>', unsafe_allow_html=True)
    
    rc1, rc_spacer = st.columns([2, 3])
    with rc1: 
        calc_mode = st.radio("Mode", ["Bill from kWh", "kWh from Bill"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 1])
    with col_l: 
        category = st.selectbox("Customer Category", ["Residential", "Non-Residential", "SLT-LV"])
    with col_r: 
        val_input = st.number_input("Consumption (kWh)" if calc_mode == "Bill from kWh" else "Budget Amount (GHS)", min_value=0.0, value=150.0)

    if calc_mode == "Bill from kWh":
        res = calculate_bill(sel_year, category, val_input, sel_period)
        d_val = f"GHS {res.total:,.2f}"
        d_label = "Total Estimated Bill"
        d_color = "#38bdf8"
    else:
        kwh_res = invert_bill_to_kwh(sel_year, category, val_input, sel_period)
        res = calculate_bill(sel_year, category, kwh_res, sel_period)
        d_val = f"{kwh_res:,.2f} kWh"
        d_label = "Estimated Consumption"
        d_color = "#a855f7"

    st.markdown(f'''
    <div style="margin-top:20px; background:rgba(255,255,255,0.05); border:1px solid {d_color}; border-radius:24px; padding:30px; text-align:center; box-shadow: 0 0 30px {d_color}30;">
        <div style="color:{d_color}; font-size:1rem; font-weight:800; text-transform:uppercase;">{d_label}</div>
        <div style="color:white; font-size:3.5rem; font-weight:900;">{d_val}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    for line in res.breakdown: 
        st.markdown(f'''
        <div style="display:flex; justify-content:space-between; padding:15px 0; border-bottom:1px solid rgba(255,255,255,0.15);">
            <span style="color:#e2e8f0; font-weight:600;">{line.label}</span>
            <span style="color:white; font-weight:700; font-family:monospace; font-size:1.1rem;">{line.amount:,.2f}</span>
        </div>
        ''', unsafe_allow_html=True)

with tab3:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown("### Historical Trends (GHS Equiv)")
    
    trend_data = [
        {"Year": "1998", "Base Rate (GHS)": 0.0055},
        {"Year": "2001", "Base Rate (GHS)": 0.0242},
        {"Year": "2002", "Base Rate (GHS)": 0.0400},
        {"Year": "2003", "Base Rate (GHS)": 0.0550},
        {"Year": "2005", "Base Rate (GHS)": 0.0583},
        {"Year": "2006", "Base Rate (GHS)": 0.0700},
        {"Year": "2007", "Base Rate (GHS)": 0.0950},
        {"Year": "2008", "Base Rate (GHS)": 0.0950},
        {"Year": "2010", "Base Rate (GHS)": 0.1700},
        {"Year": "2011", "Base Rate (GHS)": 0.1758},
        {"Year": "2012", "Base Rate (GHS)": 0.1758},
        {"Year": "2013", "Base Rate (GHS)": 0.3145},
        {"Year": "2014", "Base Rate (GHS)": 0.4121},
        {"Year": "2015", "Base Rate (GHS)": 0.6733},
        {"Year": "2016", "Base Rate (GHS)": 0.6733},
        {"Year": "2017", "Base Rate (GHS)": 0.6733},
        {"Year": "2018", "Base Rate (GHS)": 0.5555},
        {"Year": "2019", "Base Rate (GHS)": 0.6542},
        {"Year": "2020", "Base Rate (GHS)": 0.6542},
        {"Year": "2021", "Base Rate (GHS)": 0.6542},
        {"Year": "2022", "Base Rate (GHS)": 0.8904},
        {"Year": "2023", "Base Rate (GHS)": 1.4057},
        {"Year": "2024", "Base Rate (GHS)": 1.5327},
        {"Year": "2025", "Base Rate (GHS)": 1.8224},
        {"Year": "2026", "Base Rate (GHS)": 2.0022}
    ]
    df_trends = pd.DataFrame(trend_data)
    st.dataframe(df_trends, use_container_width=True, hide_index=True)
    st.line_chart(df_trends.set_index("Year"))
