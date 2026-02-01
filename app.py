import streamlit as st
import pandas as pd
from dataclasses import dataclass
from typing import List

# ---------------------------------------------------------
# 1. THE LOGIC ENGINE
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
RES_LIFELINE_MAX_LEGACY = 50.0
RES_LIFELINE_MAX_MODERN = 30.0
BLOCK_300 = 300.0

# TARIFF DATABASE
TARIFFS = {
    "2026": {
        "Q1": {
            "rates": {"RES_LIFELINE": 88.3713/100, "RES_B1": 200.2159/100, "RES_B2": 264.5527/100, "NONRES_B1": 180.7634/100, "NONRES_B2": 224.6455/100, "SLT_LV": 269.7753/100, "SLT_MV1": 215.3414/100, "SLT_MV2": 134.2804/100},
            "service": {"Residential_Lifeline": 2.13, "Residential": 10.730886, "Non-Residential": 12.428245, "SLT": 500.00}
        }
    },
    "2025": {
        "May": {
            "rates": {"RES_LIFELINE": 77.6274/100, "RES_B1": 175.8743/100, "RES_B2": 232.3892/100, "NONRES_B1": 158.7868/100, "NONRES_B2": 197.3338/100, "SLT_LV": 236.9769/100, "SLT_MV": 189.1609/100, "SLT_MV2": 123.4162/100, "SLT_HV": 189.1609/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "July": {
            "rates": {"RES_LIFELINE": 79.5308/100, "RES_B1": 180.1867/100, "RES_B2": 238.0873/100, "NONRES_B1": 162.6801/100, "NONRES_B2": 202.1723/100, "SLT_LV": 242.7874/100, "SLT_MV": 193.7990/100, "SLT_MV2": 126.4423/100, "SLT_HV": 193.7990/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "Oct": {
            "rates": {"RES_LIFELINE": 80.4389/100, "RES_B1": 182.2442/100, "RES_B2": 240.8059/100, "NONRES_B1": 164.5377/100, "NONRES_B2": 204.4809/100, "SLT_LV": 245.5597/100, "SLT_MV": 196.0119/100, "SLT_MV2": 127.8861/100, "SLT_HV": 196.0119/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        }
    },
    "2024": {
        "April": {
            "rates": {"RES_LIFELINE": 63.4792/100, "RES_B1": 140.5722/100, "RES_B2": 182.4354/100, "RES_B3": 202.7060/100, "NR_B1": 126.9145/100, "NR_B2": 135.0506/100, "NR_B3": 201.6051/100, "SLT_LV": 191.0709/100, "SLT_MV": 152.5176/100, "SLT_HV": 160.0738/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "July": {
            "rates": {"RES_LIFELINE": 65.6664/100, "RES_B1": 148.7753/100, "RES_B2": 196.5822/100, "RES_B3": 218.4239/100, "NR_B1": 134.3206/100, "NR_B2": 142.9324/100, "NR_B3": 213.3692/100, "SLT_LV": 200.4630/100, "SLT_MV": 160.0146/100, "SLT_HV": 167.9427/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "Oct": {
            "rates": {"RES_LIFELINE": 67.6495/100, "RES_B1": 153.2683/100, "RES_B2": 202.5190/100, "RES_B3": 225.0203/100, "NR_B1": 138.3771/100, "NR_B2": 147.2489/100, "NR_B3": 219.8129/100, "SLT_LV": 206.5170/100, "SLT_MV": 164.8471/100, "SLT_HV": 173.0125/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        }
    },
    "2023": {
        "Feb": {
            "rates": {"RES_LIFELINE": 54.4627/100, "RES_B1": 115.7212/100, "RES_B2": 150.1837/100, "RES_B3": 166.8708/100, "NR_B1": 108.8876/100, "NR_B2": 115.8681/100, "NR_B3": 172.9692/100, "SLT_LV": 172.3461/100, "SLT_MV": 130.8541/100, "SLT_HV": 137.3370/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "June": {
            "rates": {"RES_LIFELINE": 64.4620/100, "RES_B1": 136.9676/100, "RES_B2": 177.7574/100, "RES_B3": 197.5082/100, "NR_B1": 128.8793/100, "NR_B2": 137.1414/100, "NR_B3": 204.7263/100, "SLT_LV": 203.9889/100, "SLT_MV": 154.8788/100, "SLT_HV": 162.5521/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "Sept": {
            "rates": {"RES_LIFELINE": 64.4620/100, "RES_B1": 142.7485/100, "RES_B2": 185.2598/100, "RES_B3": 205.8442/100, "NR_B1": 128.8793/100, "NR_B2": 137.1414/100, "NR_B3": 204.7263/100, "SLT_LV": 203.9889/100, "SLT_MV": 154.8788/100, "SLT_HV": 162.5521/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        },
        "Dec": {
            "rates": {"RES_LIFELINE": 63.4792/100, "RES_B1": 140.5722/100, "RES_B2": 182.4354/100, "RES_B3": 202.7060/100, "NR_B1": 126.9145/100, "NR_B2": 135.0506/100, "NR_B3": 201.6051/100, "SLT_LV": 200.8789/100, "SLT_MV": 152.5176/100, "SLT_HV": 160.0738/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        }
    },
    "2022": {
        "Sept": {
            "rates": {"RES_LIFELINE": 41.9065/100, "RES_B1": 89.0422/100, "RES_B2": 115.5595/100, "RES_B3": 128.3995/100, "NR_B1": 83.7841/100, "NR_B2": 89.1552/100, "NR_B3": 133.0919/100, "SLT_LV": 132.6125/100, "SLT_MV": 100.6863/100, "SLT_HV": 105.6746/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 1073.09/100, "Non-Res": 1242.82/100, "SLT": 50000.00/100}
        }
    },
    "2021": {
        "Jan": {
            "rates": {"RES_B1": 32.6060/100, "RES_B2": 65.4161/100, "RES_B3": 84.8974/100, "RES_B4": 94.3304/100, "NR_B1": 79.7943/100, "NR_B2": 84.9097/100, "NR_B3": 133.9765/100, "SLT_LV": 104.7303/100, "SLT_MV": 79.5167/100, "SLT_HV": 83.4562/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 745.69/100, "Non-Res": 1242.82/100, "SLT_LV": 4971.29/100, "SLT_MV": 6959.81/100}
        }
    },
    "2020": {
        "Jan": {
            "rates": {"RES_B1": 32.6060/100, "RES_B2": 65.4161/100, "RES_B3": 84.8974/100, "RES_B4": 94.3304/100, "NR_B1": 79.7943/100, "NR_B2": 84.9097/100, "NR_B3": 133.9765/100, "SLT_LV": 104.7303/100, "SLT_MV": 79.5167/100, "SLT_HV": 83.4562/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 745.69/100, "Non-Res": 1242.82/100, "SLT_LV": 4971.29/100, "SLT_MV": 6959.81/100}
        },
        "April": {
            "rates": {"RES_B1": 32.6060/100, "RES_B2": 65.4161/100, "RES_B3": 84.8974/100, "RES_B4": 94.3304/100, "NR_B1": 79.7943/100, "NR_B2": 84.9097/100, "NR_B3": 133.9765/100, "SLT_LV": 104.7303/100, "SLT_MV": 79.5167/100, "SLT_HV": 83.4562/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 745.69/100, "Non-Res": 1242.82/100, "SLT_LV": 4971.29/100, "SLT_MV": 6959.81/100}
        },
        "July": {
            "rates": {"RES_B1": 32.6060/100, "RES_B2": 65.4161/100, "RES_B3": 84.8974/100, "RES_B4": 94.3304/100, "NR_B1": 79.7943/100, "NR_B2": 84.9097/100, "NR_B3": 133.9765/100, "SLT_LV": 104.7303/100, "SLT_MV": 79.5167/100, "SLT_HV": 83.4562/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 745.69/100, "Non-Res": 1242.82/100, "SLT_LV": 4971.29/100, "SLT_MV": 6959.81/100}
        },
        "Oct": {
            "rates": {"RES_B1": 32.6060/100, "RES_B2": 65.4161/100, "RES_B3": 84.8974/100, "RES_B4": 94.3304/100, "NR_B1": 79.7943/100, "NR_B2": 84.9097/100, "NR_B3": 133.9765/100, "SLT_LV": 104.7303/100, "SLT_MV": 79.5167/100, "SLT_HV": 83.4562/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 745.69/100, "Non-Res": 1242.82/100, "SLT_LV": 4971.29/100, "SLT_MV": 6959.81/100}
        }
    },
    "2019": {
        "July": {
            "rates": {"RES_B1": 30.7780/100, "RES_B2": 61.7488/100, "RES_B3": 80.1380/100, "RES_B4": 89.0422/100, "NR_B1": 75.3210/100, "NR_B2": 75.3210/100, "NR_B3": 80.1496/100, "SLT_LV": 98.8591/100, "SLT_MV": 75.0589/100, "SLT_HV": 78.7776/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 703.89/100, "Non-Res": 1173.15/100, "SLT_LV": 4692.60/100, "SLT_MV": 6569.64/100}
        },
        "Oct": {
            "rates": {"RES_B1": 32.6060/100, "RES_B2": 65.4161/100, "RES_B3": 84.8974/100, "RES_B4": 94.3304/100, "NR_B1": 79.7943/100, "NR_B2": 79.7943/100, "NR_B3": 84.9097/100, "SLT_LV": 104.7303/100, "SLT_MV": 79.5167/100, "SLT_HV": 83.4562/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 745.69/100, "Non-Res": 1242.82/100, "SLT_LV": 4971.29/100, "SLT_MV": 6959.81/100}
        }
    },
    "2018": {
        "March": {
            "rates": {"RES_B1": 27.6858/100, "RES_B2": 55.5450/100, "RES_B3": 72.0866/100, "RES_B4": 80.0963/100, "NR_B1": 67.7536/100, "NR_B2": 67.7536/100, "NR_B3": 72.0971/100, "SLT_LV": 75.6640/100, "SLT_MV": 58.5683/100, "SLT_HV": 53.8196/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 633.17/100, "Non-Res": 1055.28/100, "SLT_LV": 4221.14/100, "SLT_MV": 5909.60/100}
        },
        "July": {
            "rates": {"RES_B1": 27.6858/100, "RES_B2": 55.5450/100, "RES_B3": 72.0866/100, "RES_B4": 80.0963/100, "NR_B1": 67.7536/100, "NR_B2": 67.7536/100, "NR_B3": 72.0971/100, "SLT_LV": 75.6640/100, "SLT_MV": 58.5683/100, "SLT_HV": 53.8196/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 633.17/100, "Non-Res": 1055.28/100, "SLT_LV": 4221.14/100, "SLT_MV": 5909.60/100}
        },
        "Oct": {
            "rates": {"RES_B1": 27.6858/100, "RES_B2": 55.5450/100, "RES_B3": 72.0866/100, "RES_B4": 80.0963/100, "NR_B1": 67.7536/100, "NR_B2": 67.7536/100, "NR_B3": 72.0971/100, "SLT_LV": 75.6640/100, "SLT_MV": 58.5683/100, "SLT_HV": 53.8196/100},
            "service": {"Residential_Lifeline": 213.00/100, "Residential": 633.17/100, "Non-Res": 1055.28/100, "SLT_LV": 4221.14/100, "SLT_MV": 5909.60/100}
        }
    }
}

def is_taxable(category: str) -> bool:
    return not category.startswith("Residential")

def calculate_bill(year: str, category: str, kwh: float, period: str = "Q1") -> BillResult:
    if year not in TARIFFS: return None
    if period not in TARIFFS[year]: period = list(TARIFFS[year].keys())[0]

    data = TARIFFS[year][period]
    rates, services = data["rates"], data["service"]
    energy = service = 0.0
    
    # --- MODERN LOGIC (Focus on 2018-2026) ---
    if category == "Residential":
        lifeline_limit = 30.0 if int(year) >= 2022 else 50.0
        
        if kwh <= lifeline_limit:
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
# 2. UI SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="PURC Pro Dashboard", layout="wide")

# CSS INJECTION
st.markdown("""<style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #0f172a;
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        background-attachment: fixed;
    }
    
    /* GLASS CARDS */
    .glass-container {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255, 255, 255, 0.3);
        border-left: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 24px;
        padding: 25px;
        margin-bottom: 25px;
    }

    /* TEXT STYLING FOR VISIBILITY */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 800 !important;
        text-shadow: 0px 3px 6px rgba(0, 0, 0, 0.8) !important;
    }

    /* Widget Labels */
    .stSelectbox label, .stNumberInput label, .stRadio label, p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.8) !important;
        opacity: 1 !important;
    }

    /* Custom Labels */
    .label-text {
        color: #f8fafc;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 800;
        text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.9);
        margin-bottom: 5px;
    }
    
    /* Value Text */
    .value-text {
        font-size: 2.8rem;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0px 4px 12px rgba(0, 0, 0, 0.9);
    }
    
    /* Breakdown Text */
    .breakdown-label {
        color: #e2e8f0;
        font-weight: 600;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.9);
    }
    
    .breakdown-value {
        color: #ffffff;
        font-weight: 700;
        font-family: monospace;
        font-size: 1.1rem;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.9);
    }

    .status-active { color: #4ade80; text-shadow: 0px 0px 15px rgba(74, 222, 128, 0.6); }
    .status-archived { color: #cbd5e1; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255,255,255,0.1); border-radius: 30px; color: #ffffff; border: 1px solid rgba(255,255,255,0.2); padding: 0px 30px; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%) !important; color: white !important; border: none !important; }
    
    </style>""", unsafe_allow_html=True)

st.markdown("<h1>GAZETTED TARIFFS</h1>", unsafe_allow_html=True)

# *** CRITICAL FIX: Initialize tabs BEFORE using them ***
tab1, tab2, tab3 = st.tabs(["OVERVIEW", "CALCULATOR", "TRENDS"])

with tab1:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col_sel, col_q, col_space = st.columns([1, 1, 2])
    with col_sel:
        all_years = sorted(list(TARIFFS.keys()), reverse=True)
        sel_year = st.selectbox("Select Fiscal Year:", all_years, index=0, help="The reporting year for the tariff.")
    with col_q:
        q_opts = list(TARIFFS[sel_year].keys())
        sel_period = st.selectbox("Select Period / Quarter:", q_opts, help="The specific effective date or quarter.")

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
        st.markdown(f'''<div class="glass-container"><div class="label-text">Res. Base Rate (GHS)</div><div class="value-text" style="color:#38bdf8; text-shadow: 0px 2px 8px rgba(0,0,0,0.8);">{rate_val}</div></div>''', unsafe_allow_html=True)
    
    status_cls = "status-active" if sel_year == "2026" else "status-archived"
    status_txt = "Active" if sel_year == "2026" else "Archived"
    with c3:
        st.markdown(f'''<div class="glass-container"><div class="label-text">Status</div><div class="value-text {status_cls}">{status_txt}</div></div>''', unsafe_allow_html=True)

    # --- NEW BOTTOM SECTION FOR "RAW" SPACE ---
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
            
            df_display = pd.DataFrame(table_data)
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn("Tariff Category", width="medium"),
                    "Rate (GHS/kWh)": st.column_config.TextColumn("Rate (GHS)", width="small")
                }
            )

    with bot2:
        st.markdown('<h3 style="margin-bottom: 15px;">💡 Quick Notes</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-container" style="padding: 20px; border-left: 4px solid #38bdf8;">
            <p style="font-size: 0.85rem; margin-bottom: 10px; color: #e2e8f0; font-weight: 500; text-shadow: none;">
                <strong style="color: #38bdf8;">Lifeline:</strong> Subsidized rate for consumption below 30 kWh (50 kWh before 2022).
            </p>
            <p style="font-size: 0.85rem; margin-bottom: 10px; color: #e2e8f0; font-weight: 500; text-shadow: none;">
                <strong style="color: #38bdf8;">Service Charge:</strong> Fixed monthly fee applied regardless of usage.
            </p>
            <p style="font-size: 0.85rem; margin-bottom: 0px; color: #e2e8f0; font-weight: 500; text-shadow: none;">
                <strong style="color: #38bdf8;">SLT:</strong> Special Load Tariff for industrial heavy users.
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="glass-container"><h2 style="color:white; margin:0; font-size:1.8rem; font-weight:800; text-shadow: 0 2px 5px rgba(0,0,0,0.8);">Bill Simulator</h2></div>', unsafe_allow_html=True)
    
    rc1, rc_spacer = st.columns([2, 3])
    with rc1:
        calc_mode = st.radio("Mode", ["Bill from kWh", "kWh from Bill"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col_l, col_r, col_s = st.columns([1, 1, 2])
    with col_l:
        category = st.selectbox("Customer Category", ["Residential", "Non-Residential", "SLT-LV"], help="Residential: Homes. Non-Res: Commercial. SLT-LV: Industrial Low Voltage.")
    with col_r:
        val_input = st.number_input("Consumption (kWh)" if calc_mode == "Bill from kWh" else "Budget Amount (GHS)", min_value=0.0, value=150.0, help="Enter your monthly usage or budget.")

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

    # Result Card
    st.markdown(f'''
    <div style="margin-top:20px; background:rgba(255,255,255,0.05); border:1px solid {d_color}; border-radius:24px; padding:30px; text-align:center; box-shadow: 0 0 30px {d_color}30;">
        <div style="color:{d_color}; font-size:1rem; font-weight:800; text-transform:uppercase; text-shadow: 0 1px 3px rgba(0,0,0,0.9); margin-bottom:5px;">{d_label}</div>
        <div style="color:white; font-size:3.5rem; font-weight:900; text-shadow: 0 4px 15px rgba(0,0,0,1);">{d_val}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    for line in res.breakdown:
        st.markdown(f'''
        <div style="display:flex; justify-content:space-between; padding:15px 0; border-bottom:1px solid rgba(255,255,255,0.15);">
            <span class="breakdown-label">{line.label}</span>
            <span class="breakdown-value">{line.amount:,.2f}</span>
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
