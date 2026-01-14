###############################################
# FTZ Savings – Agentic AI Calculator (B-TEST)
###############################################

import streamlit as st
import pandas as pd
import difflib
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

# =====================================================
# GOOGLE SHEETS LOGGING
# =====================================================
SHEET_NAME = "FTZ_App_B_Test_Log"


LOG_COLUMNS = [
    "timestamp",
    "session_id",
    "net_savings",
    "cost_with_ftz",
    "cost_without_ftz",
    "cta_clicked",
    "cta_name",
    "cta_company",
    "cta_email",
    "cta_phone",
    "cta_message",
    "chat_question",
]

@st.cache_resource
def get_sheet():
    # scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    # creds = Credentials.from_service_account_info(
    #     st.secrets["gcp_service_account"],
    #     scopes=scopes,
    SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    #return client.open(SHEET_NAME).sheet1

    # Ensure headers exist
    if sheet.row_count == 0 or sheet.get_all_values() == []:
        sheet.append_row(LOG_COLUMNS)

    return sheet

def log_to_google_sheets(row: dict):
    sheet = get_sheet()

    # Force EST timestamp
    row["timestamp"] = datetime.now(
        ZoneInfo("America/New_York")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")

    # Build row strictly by column order
    ordered_row = [row.get(col, "") for col in LOG_COLUMNS]

    sheet.append_row(
        ordered_row,
        value_input_option="USER_ENTERED"
    )

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "show_inline_details" not in st.session_state:
    st.session_state.show_inline_details = False

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="FTZ Savings – Agentic AI Calculator - B Testing",
    layout="wide",
    page_icon="💼"
)

# -----------------------------
# MONEY FORMATTER
# -----------------------------
# def money(x):
#     try:
#         x = float(x)
#     except:
#         return x
#     return f"(${abs(x):,.0f})" if x < 0 else f"${x:,.0f}"

def money(x):
    try:
        x = float(x)
    except (ValueError, TypeError):
        return x  # leave strings untouched

    return f"(${abs(x):,.0f})" if x < 0 else f"${x:,.0f}"

# =====================================================
# STYLES
# =====================================================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#f8fafc,#eef2f7); }
h1,h2,h3,h4 { color:#0f172a; }
.kpi-card {
    background:#0f172a;
    color:white;
    border-radius:10px;
    padding:14px;
    text-align:center;
}
.kpi-value { font-size:20px; font-weight:700; }
.chat-user { color:#0f172a; font-weight:600; }
.chat-ai { color:#2563eb; }
[data-testid="stSidebar"] { display:none; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("<h3 style='text-align:center;'>FTZ Savings – Agentic AI Calculator</h3>", unsafe_allow_html=True)
c1,c2,c3 = st.columns([2,1,2])
with c2:
    st.image("assets/mas_logo.jpg", width=150)

st.markdown("""
<div style="text-align:center; max-width:700px; margin:auto;">
<p style="color:#334155;">
We MAS US Holdings have created a best-in-class, transparent, and conversion-focused digital experience,
ready to drive full spectrum of value unlocks through the FTZ apparel offering.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =====================================================
# INPUTS — CUSTOMER DATA (5 × 2)
# =====================================================
st.subheader("Customer Data Assumptions")

r1 = st.columns(5)
shipments_per_week = r1[0].number_input("Shipments / Week", 1, value=2)
avg_import_value = r1[1].number_input("Avg Import Value ($)", 1000, value=500000, step=1000)
mpf_pct = r1[2].number_input("MPF %", value=0.35, disabled=True)
broker_cost = r1[3].number_input("Broker Cost ($/entry)", value=125.0)
current_interest_rate = r1[4].number_input("Current Interest Rate (%)", value=6.5)

r2 = st.columns(5)
export_pct = r2[0].number_input("Export %", 0.0, 100.0, 1.0)
offspec_pct = r2[1].number_input("Off-Spec %", 0.0, 100.0, 0.25)
hmf_pct = r2[2].number_input("HMF %", value=0.13, disabled=True)
duty_pct = r2[3].number_input("Avg Duty %", 0.0, 100.0, 30.0)
avg_stock_days = r2[4].number_input("Avg # Stock Holding Days", value=45)

st.markdown("**Costs With FTZ (Annual)**")
r3 = st.columns(4)
ftz_consult = r3[0].number_input("FTZ Consulting", value=50000)
ftz_mgmt = r3[1].number_input("FTZ Management", value=150000)
ftz_software = r3[2].number_input("FTZ Software Fee", value=40000)
ftz_bond = r3[3].number_input("FTZ Operator Bond", value=1000)

st.markdown("**Costs Without FTZ (Annual)**")
r4 = st.columns(4)
noftz_consult = r4[0].number_input("Consulting (No FTZ)", value=0)
noftz_mgmt = r4[1].number_input("Management (No FTZ)", value=0)
noftz_software = r4[2].number_input("Software (No FTZ)", value=0)
noftz_bond = r4[3].number_input("Operator Bond (No FTZ)", value=0)

# =====================================================
# CALCULATIONS
# =====================================================
export_sales = export_pct / 100
off_spec = offspec_pct / 100
avg_duty = duty_pct / 100
mpf_rate = mpf_pct / 100
hmf_rate = hmf_pct / 100

total_import_value = shipments_per_week * avg_import_value * 52
entries_per_year = shipments_per_week * 52

total_duty = total_import_value * avg_duty
duty_saved_export = total_import_value * export_sales * avg_duty
duty_saved_offspec = total_import_value * off_spec * avg_duty

total_net_duty_no_ftz = total_duty
total_net_duty_with_ftz = total_duty - duty_saved_export - duty_saved_offspec

per_entry_mpf = min(avg_import_value * mpf_rate, 634.62)
mpf_no_ftz = per_entry_mpf * entries_per_year
mpf_with_ftz = min(shipments_per_week * avg_import_value * mpf_rate, 634.62) * 52

broker_hmf_no_ftz = entries_per_year * broker_cost + shipments_per_week * avg_import_value * hmf_rate
broker_hmf_with_ftz = 52 * broker_cost + shipments_per_week * avg_import_value * hmf_rate

cost_with_ftz = ftz_consult + ftz_mgmt + ftz_software + ftz_bond
cost_without_ftz = noftz_consult + noftz_mgmt + noftz_software + noftz_bond

interest_rate = current_interest_rate / 100
total_wc_saving = total_net_duty_with_ftz * interest_rate * (avg_stock_days / 365)

total_cost_without_ftz = total_net_duty_no_ftz + mpf_no_ftz + broker_hmf_no_ftz + cost_without_ftz
total_cost_with_ftz = total_net_duty_with_ftz + mpf_with_ftz + broker_hmf_with_ftz + cost_with_ftz - total_wc_saving

net_savings_to_brand = total_cost_without_ftz - total_cost_with_ftz


# =====================================================
# BUTTONS
# =====================================================
b1,b2,b3 = st.columns(3)
calculate = b1.button("📊 Calculate Savings", use_container_width=True)
#cta_btn = b2.button("📞 Smart CTA", use_container_width=True)
#details = b3.button("📄 Show Details", use_container_width=True)

# =====================================================
# KPI OUTPUT + LOGGING
# =====================================================
def money(x):
    try:
        x = float(x)
    except (ValueError, TypeError):
        return x  # leave strings untouched

    return f"(${abs(x):,.0f})" if x < 0 else f"${x:,.0f}"


if calculate:
    log_to_google_sheets({
        "session_id": st.session_state.session_id,
        "net_savings": net_savings_to_brand,
        "cost_with_ftz": total_cost_with_ftz,
        "cost_without_ftz": total_cost_without_ftz,
        "cta_clicked": "No",
        "cta_name": "",
        "cta_company": "",
        "cta_email": "",
        "cta_phone": "",
        "cta_message": "",
        "chat_question": "",
    })

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(f"<div class='kpi-card'><div>Total Duty</div><div class='kpi-value'>{money(total_duty)}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi-card'><div>Cost With FTZ</div><div class='kpi-value'>{money(total_cost_with_ftz)}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi-card'><div>Cost Without FTZ</div><div class='kpi-value'>{money(total_cost_without_ftz)}</div></div>", unsafe_allow_html=True)
    #k4.markdown(f"<div class='kpi-card'><div>Net Savings</div><div class='kpi-value'>{money(net_savings)}</div></div>", unsafe_allow_html=True)
    color = "#22c55e" if net_savings_to_brand >= 0 else "#ef4444"
    k4.markdown(f"<div class='kpi-card'><div>Net Savings</div><div class='kpi-value' style='color:{color};'>{money(net_savings_to_brand)}</div></div>", unsafe_allow_html=True)



# =====================================================
# SMART CTA
# =====================================================
# if cta_btn:
#     st.markdown("---")
#     with st.form("cta_form"):
#         name = st.text_input("Full Name *")
#         company = st.text_input("Company *")
#         email = st.text_input("Business Email *")
#         phone = st.text_input("Phone")
#         message = st.text_area("Message")
#         submit = st.form_submit_button("Request a Call")
if "cta_open" not in st.session_state:
    st.session_state.cta_open = False

cta = b2.button("📞 Smart CTA", use_container_width=True)
if cta:
    st.session_state.cta_open = True

if st.session_state.cta_open:
    st.markdown("---")
    st.markdown(
        "<h4 style='color:#0f172a;'>📞 Smart CTA — Request a Consultation</h4>",
        unsafe_allow_html=True
    )

    with st.form("smart_cta_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *")
            company = st.text_input("Company *")
        with c2:
            email = st.text_input("Business Email *")
            phone = st.text_input("Phone Number")
        message = st.text_area("Question", placeholder="Anything specific you'd like us to review before the call?")

        submit = st.form_submit_button("Request a Call")


    if submit and name and company and email:
        if not name or not company or not email:
            st.error("Please fill in all required fields.")
        else:
            log_to_google_sheets({
                "session_id": st.session_state.session_id,
                "net_savings": net_savings_to_brand,
                "cost_with_ftz": total_cost_with_ftz,
                "cost_without_ftz": total_cost_without_ftz,
                "cta_clicked": "Yes",
                "cta_name": name,
                "cta_company": company,
                "cta_email": email,
                "cta_phone": phone,
                "cta_message": message,
                "chat_question": "",
            })
            st.success("✅ Thank you! Your request has been received.\n\n"
                "Our FTZ advisory team will contact you shortly.")

# =====================================================
# INLINE DETAILS (B-TEST)
# =====================================================
# if details:
#     df = pd.DataFrame({
#         "Category": [
#             "Total Duty","Duty Saved (Exports)","Duty Saved (Off-Spec)",
#             "MPF","Broker + HMF","WC Savings","Operating Costs","TOTAL"
#         ],
#         "Without FTZ": [
#             total_duty,0,0,mpf_no_ftz,broker_no_ftz,0,cost_without_ftz,total_cost_without_ftz
#         ],
#         "With FTZ": [
#             total_duty,-duty_saved_export,-duty_saved_offspec,mpf_with_ftz,broker_ftz,
#             -wc_savings,cost_with_ftz,total_cost_with_ftz
#         ],
#         "Savings": [
#             0,duty_saved_export,duty_saved_offspec,
#             mpf_no_ftz-mpf_with_ftz,
#             broker_no_ftz-broker_ftz,
#             wc_savings,
#             cost_without_ftz-cost_with_ftz,
#             net_savings
#         ]
#     })
#     st.dataframe(df.style.format(money), use_container_width=True)

# if details:
#     st.session_state.show_inline_details = not st.session_state.show_inline_details

# if st.session_state.show_inline_details:

#     st.markdown("---")
#     st.markdown("### 📊 FTZ Cost Comparison")

#     df = pd.DataFrame({
#         "Category": [
#             "Total Duty",
#             "Duty Saved of Exported Goods",
#             "Duty Saved on Non-Spec Goods",
#             "Total Net Duty",
#             "Total MPF",
#             "Total Broker Costs + HMF",
#             "Totals",
#             "FTZ Consulting",
#             "FTZ Management",
#             "FTZ Software Fee",
#             "FTZ Operator Bond",
#             "Total Operating Costs",
#             "Net Savings to Brand",
#         ],
#         "Without FTZ ($)": [
#             total_duty,
#             0,
#             0,
#             total_net_duty_no_ftz,
#             mpf_no_ftz,
#             broker_hmf_no_ftz,
#             total_net_duty_no_ftz + mpf_no_ftz + broker_hmf_no_ftz,
#             noftz_consult,
#             noftz_mgmt,
#             noftz_software,
#             noftz_bond,
#             cost_without_ftz,
#             total_cost_without_ftz,
#         ],
#         "With FTZ ($)": [
#             total_duty,
#             -duty_saved_export,
#             -duty_saved_offspec,
#             total_net_duty_with_ftz,
#             mpf_with_ftz,
#             broker_hmf_with_ftz,
#             total_net_duty_with_ftz + mpf_with_ftz + broker_hmf_with_ftz,
#             ftz_consult,
#             ftz_mgmt,
#             ftz_software,
#             ftz_bond,
#             cost_with_ftz - total_wc_saving,
#             total_cost_with_ftz,
#         ],
#         "FTZ Savings ($)": [
#             0,
#             duty_saved_export,
#             duty_saved_offspec,
#             total_net_duty_no_ftz - total_net_duty_with_ftz,
#             mpf_no_ftz - mpf_with_ftz,
#             broker_hmf_no_ftz - broker_hmf_with_ftz,
#             (
#                 (total_net_duty_no_ftz + mpf_no_ftz + broker_hmf_no_ftz)
#                 - (total_net_duty_with_ftz + mpf_with_ftz + broker_hmf_with_ftz)
#             ),
#             noftz_consult - ftz_consult,
#             noftz_mgmt - ftz_mgmt,
#             noftz_software - ftz_software,
#             noftz_bond - ftz_bond,
#             cost_without_ftz - (cost_with_ftz - total_wc_saving),
#             net_savings_to_brand,
#         ]
#     })

#     st.dataframe(
#         df.style
#         .format(money)
#         .hide(axis="index"),
#         use_container_width=True,
#         height=480
#     )


# =====================================================
# CHATBOT (UNMATCHED LOGGING)
# =====================================================
st.markdown("---")
st.markdown("<h4 style='color:#0f172a;'>FTZ Chatbot Assistant</h4>", unsafe_allow_html=True)

faq = {
    "ftz-enabled single-sku omnichannel advantages apparel 3pl": 
    "Think of one, unified inventory heartbeat serving DTC, marketplaces, and retail. "
    "In our FTZ, that single-SKU pool removes duplicate stock, cuts stockouts, and enables "
    "two-day promises—while the zone’s duty advantages keep more margin in your pocket. "
    "It’s the apparel-native system founders wish they had from day one.",

    "direct cash flow savings immediate not deferral": 
    "You’ll feel savings right away: duties vanish on exports and off-spec goods, MPF fees drop "
    "when we consolidate entries weekly, and you only part with duty when product enters U.S. commerce. "
    "It’s immediate cash you can redirect to growth, not just an accounting fiction.",

    "brands benefit most ftz omnichannel": 
    "Brands that import, move fast, and sell across channels—DTC expanding to wholesale, "
    "marketplace-heavy, international entrants, seasonal or high-SKU lines—see the biggest lift.",

    "how are numbers calculated": 
    "The calculator uses your operational inputs—shipments per week, average import value, "
    "export %, off-spec %, broker fees, and average duty rate. FTZ rules are applied to show "
    "duty saved on exports, off-spec relief, and MPF savings from weekly consolidation.",

    "numbers unusual outside typical ranges": 
    "No problem—outliers are fine. The calculator is directional. For unusual flows, "
    "a consultation unlocks a tuned, custom analysis.",

    "why savings negative": 
    "Negative savings signal volume, cost structure, or assumption issues. "
    "Higher consolidation, better HTS averages, and stronger export/off-spec flows "
    "often flip results positive.",

    "data bring consultation precise analysis": 
    "Bring HTS mix, channel split, return rates, freight modes, and your cost stack. "
    "These inputs unlock precision and actionable ROI insights.",

    "how estimate savings exported off spec inputs": 
    "Using shipments per week, average import value, export %, off-spec %, broker fees, "
    "and duty rate, the calculator converts flows into duty savings and entry reductions.",

    "what are mpf hmf weekly entry consolidation": 
    "MPF is capped per entry; HMF applies to ocean freight. Weekly consolidation "
    "reduces how often fees are paid—so savings compound quickly.",

    "hmf air land freight": 
    "HMF applies only to ocean freight. If your flow is air or land, it is excluded "
    "so results reflect reality.",

    "varying duty rates hts season accuracy": 
    "We start with an average duty rate to show direction. SKU-level precision "
    "comes during a consult.",

    "entries per shipment vs weekly consolidated entries": 
    "Non-FTZ assumes one entry per shipment; FTZ assumes one weekly entry. "
    "Enter shipments per week and the calculator models both automatically.",

    "difference vs global 3pls d2c brokers": 
    "We combine FTZ economics, apparel-native workflows, and omnichannel execution—"
    "speed, compliance, and margin in one system.",

    "support retail edi asn marketplace prep": 
    "Yes. One FTZ inventory pool feeds retail, marketplaces, and DTC—"
    "eliminating duplicate stock.",

    "how fast pilot go live 60 90 days": 
    "Our 60–90 day pilot connects systems, activates FTZ inventory, "
    "and runs live orders quickly.",

    "what not included calculator results": 
    "We focus on immediate savings. Working capital, inventory days, "
    "and deeper ROI come in custom models.",

    "quantify working capital inventory days": 
    "Yes—deferral, inventory pooling, and margin impacts are quantified "
    "during consultation.",

    "compliance guardrails audit ready apparel": 
    "Tight inventory controls, auditable entries, and apparel-specific SOPs "
    "keep operations compliant and scalable.",

    "export off spec ranges validation": 
    "Exports typically 0–30%; off-spec usually under 5%. "
    "Outliers are fine but directional.",

    "export share results pdf excel consult": 
    "Export PDF/Excel directly and use the consult CTA "
    "to turn estimates into execution."
}

faq_keys = list(faq.keys())

import difflib

def match_question(user_question: str):
    cleaned = user_question.lower().strip()

    match = difflib.get_close_matches(
        cleaned,
        faq_keys,
        n=1,
        cutoff=0.55
    )

    if match:
        return faq[match[0]]

    return None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_q = st.text_input("Ask your question:")

if st.button("Ask AI") and user_q:
    if user_q.strip():
        response = match_question(user_q)
        if not response:
            log_to_google_sheets({
                "session_id": st.session_state.session_id,
                "net_savings": net_savings_to_brand,
                "cost_with_ftz": total_cost_with_ftz,
                "cost_without_ftz": total_cost_without_ftz,
                "cta_clicked": "No",
                "cta_name": "",
                "cta_company": "",
                "cta_email": "",
                "cta_phone": "",
                "cta_message": "",
                "chat_question": user_q,
            })
            response = "Thank you for your question, Your question will be directed to the Customer Success Lead at MAS US Holdings at oscarc@masholdings.com."

    st.session_state.chat_history.append(("You", user_q))
    st.session_state.chat_history.append(("AI", response))

# for s,m in st.session_state.chat_history:
#     st.markdown(f"**{s}:** {m}")
# -------------------------
# RENDER CHAT HISTORY
# -------------------------
for speaker, msg in st.session_state.chat_history:
    if speaker == "You":
        st.markdown(
            f"<div class='chat-user'><strong>You:</strong> {msg}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-ai'><strong>AI:</strong> {msg}</div>",
            unsafe_allow_html=True
        )

st.markdown("---")
st.markdown("**Disclaimer:** This calculator provides directional estimates only and does not constitute financial, legal, or compliance advice.")
