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
RES_LIFELINE_MAX = 30.0
BLOCK_300 = 300.0
LEVY_RATE = 0.05
TAX_RATE = 0.20

# TARIFF DATABASE
TARIFFS = {
    "2026": {
        "Q1": {
            "rates": {
                "RES_LIFELINE": 88.3713 / 100, "RES_B1": 200.2159 / 100, "RES_B2": 264.5527 / 100,
                "NONRES_B1": 180.7634 / 100, "NONRES_B2": 224.6455 / 100,
                "SLT_LV": 269.7753 / 100, "SLT_MV1": 215.3414 / 100, "SLT_MV2": 134.2804 / 100,
            },
            "service": {
                "Residential (Lifeline)": 2.13, "Residential (Other)": 10.730886, "Non-Residential": 12.428245, "SLT": 500.00,
            }
        }
    },
    "2025": {
        "Q1": {
            "rates": {
                "RES_LIFELINE": 80.4389 / 100, "RES_B1": 182.2442 / 100, "RES_B2": 240.8059 / 100,
                "NONRES_B1": 164.5377 / 100, "NONRES_B2": 204.4809 / 100,
                "SLT_LV": 245.5597 / 100, "SLT_MV1": 196.0119 / 100, "SLT_MV2": 127.8861 / 100,
            },
            "service": {
                "Residential (Lifeline)": 2.13, "Residential (Other)": 10.7301, "Non-Residential": 12.428, "SLT": 500.00,
            }
        }
    },
    "2013": {
        "Oct": {
            "rates": {"RES_B1": 15.6750/100, "RES_B2": 31.4479/100, "RES_B3": 40.8134/100, "RES_B4": 45.3481/100, "NR_B1": 45.2102/100, "NR_B2": 48.1084/100, "NR_B3": 75.9089/100, "SLT_LV": 47.1226/100, "SLT_MV": 36.4757/100, "SLT_HV": 33.5182/100},
            "service": {"Residential": 295.7485/100, "Non-Res": 492.9142/100, "SLT_LV": 1971.6569/100, "SLT_MV": 2760.3197/100, "SLT_HV": 2760.3197/100}
        }
    },
    "2012": {
        "March": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 17.5785/100, "RES_B3": 22.8135/100, "RES_B4": 25.3483/100, "NR_B1": 25.2712/100, "NR_B2": 26.8912/100, "NR_B3": 42.4309/100, "SLT_LV": 26.3402/100, "SLT_MV": 20.3889/100, "SLT_HV": 18.7357/100},
            "service": {"Residential_Low": 100.00/100, "Residential": 165.3200/100, "Non-Res": 275.5300/100, "SLT_LV": 1102.2100/100, "SLT_MV_HV": 1542.9400/100}
        },
        "June": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 17.5785/100, "RES_B3": 22.8135/100, "RES_B4": 25.3483/100, "NR_B1": 25.2712/100, "NR_B2": 26.8912/100, "NR_B3": 42.4309/100, "SLT_LV": 26.3402/100, "SLT_MV": 20.3889/100, "SLT_HV": 18.7357/100},
            "service": {"Residential_Low": 100.00/100, "Residential": 165.3200/100, "Non-Res": 275.5300/100, "SLT_LV": 1102.2100/100, "SLT_MV_HV": 1542.9400/100}
        },
        "Sept": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 17.5785/100, "RES_B3": 22.8135/100, "RES_B4": 25.3483/100, "NR_B1": 25.2712/100, "NR_B2": 26.8912/100, "NR_B3": 42.4309/100, "SLT_LV": 26.3402/100, "SLT_MV": 20.3889/100, "SLT_HV": 18.7357/100},
            "service": {"Residential_Low": 100.00/100, "Residential": 165.3200/100, "Non-Res": 275.5300/100, "SLT_LV": 1102.2100/100, "SLT_MV_HV": 1542.9400/100}
        }
    },
    "2011": {
        "March": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 15.95/100, "RES_B3": 20.70/100, "RES_B4": 23.00/100, "NR_B1": 22.93/100, "NR_B2": 24.40/100, "NR_B3": 38.50/100, "SLT_LV": 23.90/100, "SLT_MV": 18.50/100, "SLT_HV": 17.00/100},
            "service": {"Residential": 150.00/100, "Non-Res": 250.00/100, "SLT_LV": 1000.00/100, "SLT_MV_HV": 1400.00/100}
        },
        "June": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 15.95/100, "RES_B3": 20.70/100, "RES_B4": 23.00/100, "NR_B1": 22.93/100, "NR_B2": 24.40/100, "NR_B3": 38.50/100, "SLT_LV": 23.90/100, "SLT_MV": 18.50/100, "SLT_HV": 17.00/100},
            "service": {"Residential_Low": 100.00/100, "Residential": 150.00/100, "Non-Res": 250.00/100, "SLT_LV": 1000.00/100, "SLT_MV_HV": 1400.00/100}
        },
        "Sept": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 17.07/100, "RES_B3": 22.15/100, "RES_B4": 24.61/100, "NR_B1": 24.54/100, "NR_B2": 26.11/100, "NR_B3": 41.20/100, "SLT_LV": 25.57/100, "SLT_MV": 19.80/100, "SLT_HV": 18.19/100},
            "service": {"Residential_Low": 100.00/100, "Residential": 150.00/100, "Non-Res": 267.50/100, "SLT_LV": 1070.00/100, "SLT_MV_HV": 1498.00/100}
        },
        "Dec": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 17.5785/100, "RES_B3": 22.8135/100, "RES_B4": 25.3483/100, "NR_B1": 25.2712/100, "NR_B2": 26.8912/100, "NR_B3": 42.4309/100, "SLT_LV": 26.3402/100, "SLT_MV": 20.3889/100, "SLT_HV": 18.7357/100},
            "service": {"Residential_Low": 100.00/100, "Residential": 165.3200/100, "Non-Res": 275.5300/100, "SLT_LV": 1102.2100/100, "SLT_MV_HV": 1542.9400/100}
        }
    },
    "2010": {
        "June": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 17.00/100, "RES_B3": 21.00/100, "RES_B4": 23.00/100, "NR_B1": 26.00/100, "NR_B2": 29.00/100, "NR_B3": 45.00/100, "SLT_LV": 26.00/100, "SLT_MV": 27.00/100, "SLT_HV": 27.00/100},
            "service": {"Residential": 150.00/100, "Non-Res": 250.00/100, "SLT_LV": 1000.00/100, "SLT_MV_HV": 1500.00/100}
        }
    },
    "2008": {
        "July": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 12.00/100, "RES_B3": 16.00/100, "RES_B4": 19.00/100, "NR_B1": 14.00/100, "NR_B2": 17.00/100, "NR_B3": 19.50/100, "SLT_LV": 16.00/100, "SLT_MV": 9.05/100, "SLT_HV": 8.05/100},
            "service": {"Residential": 50.00/100, "Non-Res": 250.00/100, "SLT_LV": 750.00/100, "SLT_MV_HV": 1250.00/100}
        }
    },
    "2007": {
        "Nov": {
            "rates": {"RES_B1": 9.50/100, "RES_B2": 12.00/100, "RES_B3": 16.00/100, "RES_B4": 19.00/100, "NR_B1": 14.00/100, "NR_B2": 17.00/100, "NR_B3": 19.50/100, "SLT_LV": 16.00/100, "SLT_MV": 9.05/100, "SLT_HV": 8.05/100},
            "service": {"Residential": 50.00/100, "Non-Res": 250.00/100, "SLT_LV": 750.00/100, "SLT_MV_HV": 1250.00/100}
        }
    },
    "2006": {
        "Sept": {
            "rates": {"B1": 700.0, "B2": 1200.0, "B3": 1400.0, "NR_B1": 1020.0, "NR_B2": 1250.0, "NR_B3": 1450.0, "SLT_LV": 1200.0, "SLT_MV": 500.0, "SLT_HV": 450.0},
            "service": {"Residential": 5000.0, "Non-Res": 25000.0, "SLT_LV": 75000.0, "SLT_MV_HV": 125000.0}
        }
    },
    "2005": {
        "May": {
            "rates": {"RES_FLAT_50": 19080.0, "B2": 583.0, "B3": 1018.0, "NR_B1": 848.0, "NR_B2": 1039.0, "SLT_LV": 403.0, "SLT_MV": 382.0, "SLT_HV": 371.0},
            "service": {"Non-Res": 21200.0, "SLT": 63600.0}
        }
    },
    "2003": {
        "March": {
            "rates": {"RES_FLAT_50": 18000.0, "B2": 550.0, "B3": 960.0, "NR_B1": 800.0, "NR_B2": 980.0, "SLT_LV": 380.0, "SLT_MV": 360.0, "SLT_HV": 350.0},
            "service": {"Non-Res": 20000.0, "SLT": 60000.0}
        }
    },
    "2002": {
        "August": {
            "rates": {"RES_FLAT_50": 14000.0, "B2": 400.0, "B3": 960.0, "NR_B1": 750.0, "NR_B2": 980.0, "SLT_LV": 360.0, "SLT_MV": 350.0, "SLT_HV": 340.0},
            "service": {"Non-Res": 20000.0, "SLT": 60000.0}
        }
    },
    "2001": {
        "May": {
            "rates": {"RES_FLAT_50": 7800.0, "B2": 242.0, "B3": 304.0, "B4": 570.0, "NR_B1": 436.0, "NR_B2": 645.0, "SLT_LV": 362.0, "SLT_MV": 350.0, "SLT_HV": 340.0},
            "service": {"Non-Res": 10000.0, "SLT": 40000.0}
        }
    },
    "1998": {
        "Feb": {
            "rates": {"RES_FLAT_50": 2250.0, "B2": 55.0, "B3": 85.0, "B4": 180.0, "NR_B1": 85.0, "NR_B2": 180.0},
            "service": {"Non-Res": 3000.0, "SLT": 10000.0}
        },
        "Sept": {
            "rates": {"RES_FLAT_50": 4000.0, "B2": 120.0, "B3": 150.0, "B4": 220.0, "NR_B1": 220.0, "NR_B2": 320.0},
            "service": {"Non-Res": 5000.0, "SLT": 20000.0}
        }
    }
}

def is_taxable(category: str) -> bool:
    return not category.startswith("Residential")

def calculate_bill(year: str, category: str, kwh: float, period: str = "Q1") -> BillResult:
    if year not in TARIFFS: return None
    
    # --- LEGACY LOGIC (Pre-2007) ---
    if int(year) < 2007:
        t = TARIFFS[year][period]
        r, s = t["rates"], t["service"]
        energy_old = service_old = 0.0
        
        if category == "Residential":
            if year == "2006":
                b1 = min(kwh, 300); energy_old = b1 * r["B1"]
                if kwh > 300:
                    b2 = min(kwh - 300, 300); energy_old += b2 * r["B2"]
                    if kwh > 600: energy_old += (kwh - 600) * r["B3"]
                service_old = s["Residential"]
            else:
                if kwh <= 50: energy_old = r["RES_FLAT_50"]
                else:
                    energy_old = r["RES_FLAT_50"]
                    kwh_rem = kwh - 50
                    if year in ["2002", "2003", "2005"]:
                        b2 = min(kwh_rem, 250); energy_old += b2 * r["B2"]
                        if kwh_rem > 250: energy_old += (kwh_rem - 250) * r["B3"]
                    else:
                        b2_sz, b3_sz = (100, 150) if year == "2001" else (250, 300)
                        b2 = min(kwh_rem, b2_sz); energy_old += b2 * r["B2"]
                        if kwh_rem > b2_sz:
                            rem2 = kwh_rem - b2_sz; b3 = min(rem2, b3_sz); energy_old += b3 * r["B3"]
                            if rem2 > b3_sz: energy_old += (rem2 - b3_sz) * r["B4"]
        elif category == "Non-Residential":
            if year == "2006":
                b1 = min(kwh, 300); energy_old = b1 * r["NR_B1"]
                if kwh > 300:
                    b2 = min(kwh - 300, 300); energy_old += b2 * r["NR_B2"]
                    if kwh > 600: energy_old += (kwh - 600) * r["NR_B3"]
            else:
                nr_b1 = 300 if year in ["2001", "2002", "2003", "2005"] else 600
                b1, b2 = min(kwh, nr_b1), max(0, kwh - nr_b1)
                energy_old = (b1 * r["NR_B1"]) + (b2 * r["NR_B2"])
            service_old = s["Non-Res"]
        else: # SLT
            rmap = {"SLT-LV": r.get("SLT_LV", 0), "SLT-MV1/HV": r.get("SLT_MV", 0), "SLT-MV2": r.get("SLT_MV", 0)}
            energy_old, service_old = kwh * rmap.get(category, 0), (s["SLT_LV"] if year=="2006" and category=="SLT-LV" else s.get("SLT", 0) if year!="2006" else s["SLT_MV_HV"])

        conv = 10000.0
        levy_old = energy_old * 0.05
        return BillResult(total=(energy_old + service_old + levy_old) / conv, breakdown=[
            BillLine(f"Energy Charge (¢{energy_old:,.0f})", energy_old / conv, True),
            BillLine(f"Service Charge (¢{service_old:,.0f})", service_old / conv, True),
            BillLine(f"Levies (¢{levy_old:,.0f})", levy_old / conv, True)
        ], currency_label="GHS")

    # --- MODERN LOGIC (2007 onwards) ---
    else:
        # Fallback
        available_periods = list(TARIFFS[year].keys())
        data = TARIFFS[year].get(period, TARIFFS[year][available_periods[0]])
        rates, services = data["rates"], data["service"]
        energy = service = 0.0
        
        if category == "Residential":
            if year in ["2007", "2008", "2010", "2011", "2012", "2013"]:
                b1 = min(kwh, 50); energy = b1 * rates["RES_B1"]
                if kwh > 50:
                    b2 = min(kwh - 50, 250); energy += b2 * rates["RES_B2"]
                    if kwh > 300:
                        b3 = min(kwh - 300, 300); energy += b3 * rates["RES_B3"]
                        if kwh > 600: energy += (kwh - 600) * rates["RES_B4"]
                
                # Service charge logic
                if year in ["2011", "2012"] and kwh <= 50 and "Residential_Low" in services:
                    service = services["Residential_Low"]
                else:
                    service = services["Residential"]
            else:
                if kwh <= RES_LIFELINE_MAX: energy, service = kwh * rates["RES_LIFELINE"], services["Residential (Lifeline)"]
                else:
                    kb1, kb2 = min(kwh, BLOCK_300), max(0.0, kwh - BLOCK_300)
                    energy, service = (kb1 * rates["RES_B1"]) + (kb2 * rates["RES_B2"]), services["Residential (Other)"]
        elif category == "Non-Residential":
            if year in ["2007", "2008", "2010", "2011", "2012", "2013"]:
                b1 = min(kwh, 300); energy = b1 * rates["NR_B1"]
                if kwh > 300:
                    b2 = min(kwh - 300, 300); energy += b2 * rates["NR_B2"]
                    if kwh > 600: energy += (kwh - 600) * rates["NR_B3"]
                service = services["Non-Res"]
            else:
                kb1, kb2 = min(kwh, BLOCK_300), max(0.0, kwh - BLOCK_300)
                energy, service = (kb1 * rates["NONRES_B1"]) + (kb2 * rates["NONRES_B2"]), services["Non-Residential"]
        else: # SLT
            rate_map = {"SLT-LV": rates["SLT_LV"], "SLT-MV1/HV": rates["SLT_MV"], "SLT-MV2": rates.get("SLT_MV2", rates["SLT_MV"])}
            energy = kwh * rate_map.get(category, rates.get("SLT_LV", 0))
            
            # Smart service charge lookup
            if "SLT" in services:
                service = services["SLT"]
            elif category == "SLT-LV":
                service = services["SLT_LV"]
            elif category in ["SLT-MV1/HV", "SLT-MV2"]:
                service = services.get("SLT_MV", services.get("SLT_MV_HV", 0))
            else:
                service = services.get("SLT_HV", 0)

        levy = 0.05 * energy
        tax = (0.20 * (energy + service) if is_taxable(category) else 0.0)
        return BillResult(total=energy + service + levy + tax, breakdown=[
            BillLine("Energy Charge (GHS)", energy), BillLine("Service Charge (GHS)", service), BillLine("Levies & Taxes (GHS)", levy + tax)
        ], currency_label="GHS")

def invert_bill_to_kwh(year, category, target, period):
    lo, hi = 0.0, 1.0
    while calculate_bill(year, category, hi, period).total < target: hi *= 2
    for _ in range(40):
        mid = (lo + hi) / 2
        if calculate_bill(year, category, mid, period).total < target: lo = mid
        else: hi = mid
    return mid

# ---------------------------------------------------------
# 2. UI SETUP (STRICT ORIGINAL GLASSMORPHISM DESIGN)
# ---------------------------------------------------------
st.set_page_config(page_title="PURC Pro Dashboard", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #0f172a; background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%); background-attachment: fixed; }
    .glass-container { background: linear-gradient(135deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0.05)); backdrop-filter: blur(20px); border-top: 1px solid rgba(255, 255, 255, 0.3); border-left: 1px solid rgba(255, 255, 255, 0.3); border-radius: 24px; padding: 25px; margin-bottom: 25px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; border-radius: 30px; color: rgba(255,255,255,0.7); border: 1px solid rgba(255,255,255,0.2); padding: 0px 30px; font-weight: 600; text-transform: uppercase; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%) !important; color: white !important; border: none !important; }
    h1 { font-size: 3.5rem !important; font-weight: 800 !important; background: linear-gradient(to right, #e2e8f0, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .label-text { color: rgba(255,255,255,0.6); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; }
    .value-text { font-size: 2.5rem; font-weight: 700; color: white; }
    </style>""", unsafe_allow_html=True)

st.markdown("<h1>GAZETTED TARIFFS</h1>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["OVERVIEW", "CALCULATOR", "TRENDS"])

with tab1:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col_sel, col_q, col_space = st.columns([1, 1, 2])
    with col_sel:
        all_years = sorted(list(TARIFFS.keys()), reverse=True)
        sel_year = st.selectbox("Select Fiscal Year:", all_years, index=0)
    with col_q:
        q_opts = list(TARIFFS[sel_year].keys())
        sel_period = st.selectbox("Select Period / Quarter:", q_opts)

    if int(sel_year) < 2007:
        brate = TARIFFS[sel_year][sel_period]['rates'].get('B1', TARIFFS[sel_year][sel_period]['rates'].get('B2', 0))
        rate_val = f"{brate/10000:.4f}"
    else:
        if sel_year in ["2007", "2008", "2010", "2011", "2012", "2013"]:
            rate_val = f"{TARIFFS[sel_year][sel_period]['rates'].get('RES_B2', 0):.4f}"
        else:
            rate_val = f"{TARIFFS[sel_year][sel_period]['rates'].get('RES_B1', 0):.4f}"
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="glass-container"><div class="label-text">Effective Date</div><div class="value-text">{sel_period + " " + sel_year if int(sel_year)<2010 else "Oct 1, " + sel_year if sel_year=="2013" else "March 1, " + sel_year if sel_year=="2012" else "Jan 1, " + sel_year}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="glass-container"><div class="label-text">Res. Base Rate (GHS)</div><div class="value-text" style="color:#38bdf8;">{rate_val}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="glass-container"><div class="label-text">Status</div><div class="value-text" style="color:{"#4ade80" if sel_year=="2026" else "#94a3b8"};">{"Active" if sel_year=="2026" else "Archived"}</div></div>', unsafe_allow_html=True)

with tab2:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="glass-container"><h2 style="color:white; margin:0; font-size:1.8rem;">Bill Simulator</h2></div>', unsafe_allow_html=True)
    rc1, rc_spacer = st.columns([2, 3])
    with rc1: calc_mode = st.radio("Mode", ["Bill from kWh", "kWh from Bill"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    col_l, col_r, col_s = st.columns([1, 1, 2])
    with col_l: category = st.selectbox("Customer Category", ["Residential", "Non-Residential", "SLT-LV", "SLT-MV1/HV", "SLT-MV2"])
    with col_r: val_input = st.number_input("Consumption (kWh)" if calc_mode == "Bill from kWh" else "Budget Amount (GHS)", min_value=0.0, value=150.0)

    res = calculate_bill(sel_year, category, val_input, sel_period) if calc_mode == "Bill from kWh" else calculate_bill(sel_year, category, invert_bill_to_kwh(sel_year, category, val_input, sel_period), sel_period)
    d_val = f"GHS {res.total:,.2f}" if calc_mode == "Bill from kWh" else f"{invert_bill_to_kwh(sel_year, category, val_input, sel_period):,.2f} kWh"
    d_label, d_color = ("Total Estimated Bill", "#06b6d4") if calc_mode == "Bill from kWh" else ("Estimated Consumption", "#a855f7")

    st.markdown(f'<div style="margin-top:20px; background:rgba(255,255,255,0.05); border:1px solid {d_color}; border-radius:24px; padding:30px; text-align:center;"><div style="color:{d_color}; font-size:0.9rem; text-transform:uppercase;">{d_label}</div><div style="color:white; font-size:3.5rem; font-weight:800;">{d_val}</div></div>', unsafe_allow_html=True)
    
    if int(sel_year) < 2007: st.info(f"💡 Breakdown displays original Old Cedis (¢) for the {sel_year} schedule.")
    for line in res.breakdown: st.markdown(f'<div style="display:flex; justify-content:space-between; padding:15px 0; border-bottom:1px solid rgba(255,255,255,0.1);"><span style="color:#cbd5e1;">{line.label}</span><span style="color:white; font-weight:bold;">{line.amount:,.2f}</span></div>', unsafe_allow_html=True)

with tab3:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown("### Historical Trends (GHS Equiv)")
    
    # Properly labeled dataframe
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
        {"Year": "2025", "Base Rate (GHS)": 1.8224},
        {"Year": "2026", "Base Rate (GHS)": 2.0022}
    ]
    df_trends = pd.DataFrame(trend_data)
    st.dataframe(df_trends, use_container_width=True, hide_index=True)
    
    # Line chart using the dataframe
    st.line_chart(df_trends.set_index("Year"))
