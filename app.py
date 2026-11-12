import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
import datetime
import io

# ============================================================================
# 🎨 頁面設定與主題
# ============================================================================
st.set_page_config(
    page_title="新北市防災都更權利變換試算模型",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit 版本相容：新版以 width="stretch" 取代 use_container_width
def _st_version() -> tuple:
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


FULL_WIDTH = {"width": "stretch"} if _st_version() >= (1, 50) else {"use_container_width": True}

# ============================================================================
# 📊 五案件統計數據（論文表3-1、表3-2；各項費用占營建費用之比例，單位 %）
# ============================================================================
# === CORE-BEGIN ===
ITEMS = [
    ("bonus_mgmt", "容獎管理維護費"), ("design", "建築設計費"), ("rights", "權變費用"),
    ("demo_comp", "拆遷補償"), ("reloc", "拆遷安置"), ("interest", "貸款利息"),
    ("tax", "稅捐"), ("mgmt", "管理費用"),
]

FIVE_CASES_DATA = {
    "案件1": {"location": "蘆洲光華965", "area_ping": 941.985, "floors": "17F+16F+B4", "developer": "更新會",
              "total_cost": 2056098558, "in_situ": False,
              "bonus_mgmt": 0.59, "design": 1.80, "rights": 2.80, "demo_comp": 2.35, "reloc": 8.45,
              "interest": 6.12, "tax": 0.10, "mgmt": 33.81},
    "案件2": {"location": "新莊思源段", "area_ping": 603.4633, "floors": "15F+B5", "developer": "建設公司",
              "total_cost": 1392840119, "in_situ": False,
              "bonus_mgmt": 1.34, "design": 3.13, "rights": 3.31, "demo_comp": 5.75, "reloc": 5.59,
              "interest": 5.24, "tax": 3.74, "mgmt": 30.42},
    "案件3": {"location": "新店316", "area_ping": 500.731, "floors": "19F+B4", "developer": "建設公司",
              "total_cost": 1422714391, "in_situ": False,
              "bonus_mgmt": 0.62, "design": 2.41, "rights": 2.50, "demo_comp": 3.54, "reloc": 6.25,
              "interest": 5.19, "tax": 5.30, "mgmt": 30.39},
    "案件4": {"location": "三重381", "area_ping": 1098.284, "floors": "23F+B5", "developer": "建設公司",
              "total_cost": 2881408210, "in_situ": False,
              "bonus_mgmt": 2.00, "design": 2.05, "rights": 2.78, "demo_comp": 2.00, "reloc": 5.00,
              "interest": 5.00, "tax": 4.00, "mgmt": 32.00},
    "案件5": {"location": "淡水930", "area_ping": 584.403, "floors": "14F+B5", "developer": "更新會",
              "total_cost": 1422332224, "in_situ": True,   # 原地安置：無拆遷補償與安置費
              "bonus_mgmt": 0.069, "design": 1.89, "rights": 4.00, "demo_comp": 0.0, "reloc": 0.0,
              "interest": 5.00, "tax": 0.10, "mgmt": 27.00},
}

# 五案統計平均（表3-2；拆遷兩項為有該費用之四案平均、稅捐為建設公司三案平均）
STATISTICS_AVG = {"bonus_mgmt": 0.92, "design": 2.26, "rights": 3.08, "demo_comp": 3.41,
                  "reloc": 6.32, "interest": 5.31, "tax": 4.35, "mgmt": 30.72}
# 官方對照值（表3-2「官方基準」欄；為本研究參照基準提列方式設定之對照值，非基準條文明定費率）
OFFICIAL_REF = {"bonus_mgmt": 1.0, "design": 2.5, "rights": 3.3, "demo_comp": 3.5,
                "reloc": 7.0, "interest": 5.5, "tax": 4.0, "mgmt": 30.0}
# 更新會自辦案件之稅捐比例（統計 0.10%；官方對照 0%）
TAX_ASSOCIATION = {"stat": 0.10, "official": 0.0}

# 基準附表三（112年8月17日修正發布）：RC造16-20層標準單價（萬元/坪，物價基準日112年4月），依總樓地板面積級距
UNIT_COST_RC_16_20 = [(2500, 17.0481, "未滿2,500坪"), (7500, 16.2316, "2,500坪以上未滿7,500坪"),
                      (float("inf"), 15.7442, "7,500坪以上")]
# 拆除費概估單價（萬元/坪，以總樓地板面積計）；沿用論文附表4-1「營建工程費（含拆除）」之口徑
DEMOLITION_UNIT_DEFAULT = 0.0341
# 規模分層門檻（基地面積，坪）與分層管理費率（論文3.3.2、3.7.3）
SMALL_MAX, LARGE_MIN = 600, 900
STRATIFIED_MGMT = {"small": 27.5, "mid": 30.72, "large": 33.0}


def get_risk_fee_rate(gfa_ping: float, owners: float) -> float:
    """風險管理費率查表（新北市110年版基準；論文附表3-1）"""
    row = 0 if gfa_ping <= 2500 else (1 if gfa_ping <= 7500 else 2)
    col = 0 if owners < 30 else (1 if owners <= 100 else 2)
    return [[0.12, 0.125, 0.13], [0.125, 0.13, 0.135], [0.13, 0.135, 0.14]][row][col]


def lookup_unit_cost(gfa_ping: float):
    """依總樓地板面積查基準附表三 RC造16-20層單價級距，回傳 (單價, 級距說明)"""
    for limit, cost, label in UNIT_COST_RC_16_20:
        if gfa_ping < limit:
            return cost, label
    return UNIT_COST_RC_16_20[-1][1:]


def estimate_construction_months(floors: int, basements: int, per_floor: float, top_down: bool = False) -> float:
    """施工期間估算（論文3.5.5）：地下一層4個月、每多一層加2個月；地上每層 per_floor 個月；逆打每地下層減1.5個月"""
    under = (4 + 2 * (basements - 1)) if basements > 0 else 0
    if top_down:
        under = max(under - 1.5 * basements, 0)
    return under + floors * per_floor


def annualized_irr(equity: float, profit: float, dev_months: float,
                   invest_frac: float = 2 / 3, lag_months: int = 6):
    """實施者年化IRR（論文4.3.1簡化現金流）：
    權益資金於開發期前 invest_frac 期間按月平均投入，完工後 lag_months 個月回收本金並取得報酬。
    報酬為負或權益為零時回傳 None（虧損，無正值解）。"""
    if equity <= 0 or profit <= 0:
        return None
    dev = int(round(dev_months))
    n = max(1, int(round(dev * invest_frac)))
    horizon = dev + int(lag_months)
    cf = [0.0] * (horizon + 1)
    for k in range(1, n + 1):
        cf[k] -= equity / n
    cf[horizon] += equity + profit
    m = npf.irr(cf)
    if m is None or np.isnan(m):
        return None
    return (1 + m) ** 12 - 1


def compute_model(p: dict) -> dict:
    """核心試算（金額單位：萬元）。預設參數可重現論文表4-2、表4-3與附表4-1。"""
    area_far = p["base_area"] * p["far_exist"] * p["bonus"]
    area_total = area_far * p["k_gfa"]
    area_sale = area_far * p["k_sale"]
    num_parking = int(area_total / 35)

    # 工程費
    c_build = area_total * p["unit_cost"]
    c_demo = area_total * p["demo_unit"]
    c_engineering = c_build + c_demo
    c_advanced = p["cost_adv"]

    # 以營建費為基礎之費用
    c_design = c_build * p["r_design"] / 100
    if p.get("reloc_linked"):
        reg_area = p["base_area"] * p["far_exist"] * p["reg_factor"]
        c_reloc = reg_area * p["rent_per_ping"] * p["subsidy_months"] / 10000
    else:
        c_reloc = c_build * p["r_reloc"] / 100
    inc = p.get("include_extra", False)
    c_demo_comp = c_build * p["r_demo_comp"] / 100 if inc else 0.0
    c_rights = c_build * p["r_rights"] / 100 if inc else 0.0
    c_bonus_mgmt = c_build * p["r_bonus_mgmt"] / 100 if inc else 0.0

    # 管理費（風險管理費查表 + 人事行政 + 銷售管理）
    risk_rate = p["risk_rate"] if p.get("risk_rate") is not None else get_risk_fee_rate(area_total, p["owners"])
    c_risk = c_build * risk_rate
    c_personnel = c_build * p["rate_personnel"]
    c_sales = area_sale * p["price_sale"] * p["rate_sales"]
    c_mgmt = c_risk + c_personnel + c_sales

    # 貸款利息：資金需求 × 貸款成數 × 年利率 × 年數 × 0.5
    fund_demand = c_engineering + c_advanced + c_design + c_reloc + c_demo_comp + c_rights
    c_interest = fund_demand * p["loan_ratio"] * p["loan_rate"] * (p["dev_months"] / 12) * 0.5
    c_tax = c_build * p["r_tax"] / 100

    c_total = (c_engineering + c_advanced + c_design + c_reloc + c_demo_comp + c_rights
               + c_bonus_mgmt + c_mgmt + c_interest + c_tax)

    val_parking = num_parking * p["price_parking"]
    val_new = area_sale * p["price_sale"] + val_parking
    ratio_burden = c_total / val_new if val_new > 0 else 0.0

    # 實施者報酬：以風險管理費提列額為上限；實付營建單價高於提列單價時，差額自報酬扣減
    paid = p.get("paid_unit_cost") or p["unit_cost"]
    overrun = max(paid - p["unit_cost"], 0.0) * area_total
    profit = c_risk - overrun
    equity = p["equity_ratio"] * (fund_demand + overrun)
    irr = annualized_irr(equity, profit, p["dev_months"], p["invest_frac"], p["lag_months"])

    details = {
        "營建工程費": c_build, "拆除費（概估）": c_demo, "容積獎勵申請與審議費": c_advanced,
        "建築設計費": c_design, "拆遷安置費": c_reloc,
        "拆遷補償費": c_demo_comp, "權利變換費": c_rights, "容獎管理維護費": c_bonus_mgmt,
        "風險管理費": c_risk, "人事行政管理費": c_personnel, "銷售管理費": c_sales,
        "貸款利息": c_interest, "稅捐": c_tax,
    }
    return {
        "area_far": area_far, "GFA": area_total, "area_sale": area_sale, "num_parking": num_parking,
        "Total_Cost": c_total, "Total_Value": val_new, "Burden_Ratio": ratio_burden,
        "Landlord_Ratio": 1 - ratio_burden, "IRR": irr, "Risk_Rate": risk_rate,
        "Fund_Demand": fund_demand, "Equity": equity, "Profit": profit, "Overrun": overrun,
        "Build_Cost": c_build, "Mgmt_Total": c_mgmt, "Reloc_Linked": bool(p.get("reloc_linked")),
        "Subsidy_Months": p.get("subsidy_months") if p.get("reloc_linked") else None,
        "Mgmt_Ratio": c_mgmt / c_build if c_build > 0 else 0.0,
        "Details": details,
    }


def wmape(actual: list, pred: list) -> float:
    """加權平均絕對百分比誤差（論文3.7.2）"""
    return sum(abs(a - b) for a, b in zip(actual, pred)) / sum(actual) * 100


def backtest_prediction(case: dict, mode: str) -> list:
    """回測三種模式之預測費率（論文3.7.3）：official／preset／stratified。
    三種模式均依實施主體設定稅捐，並對原地安置案件排除拆遷補償與安置費。"""
    ref = OFFICIAL_REF if mode == "official" else STATISTICS_AVG
    pred = dict(ref)
    if case["developer"] == "更新會":
        pred["tax"] = TAX_ASSOCIATION["official" if mode == "official" else "stat"]
    if case["in_situ"]:
        pred["demo_comp"] = pred["reloc"] = 0.0
    if mode == "stratified":
        a = case["area_ping"]
        pred["mgmt"] = STRATIFIED_MGMT["small" if a < SMALL_MAX else ("mid" if a < LARGE_MIN else "large")]
    return [pred[k] for k, _ in ITEMS]


def backtest_table() -> list:
    """回傳各案三種模式之 WMAPE（%）"""
    rows = []
    for name, c in FIVE_CASES_DATA.items():
        actual = [c[k] for k, _ in ITEMS]
        rows.append({"案件": f"{name}：{c['location']}", "基地面積(坪)": round(c["area_ping"], 2),
                     "實施主體": c["developer"],
                     **{label: round(wmape(actual, backtest_prediction(c, mode)), 2)
                        for mode, label in [("official", "官方基準模式"), ("preset", "統計預設模式"),
                                            ("stratified", "分層校準模式")]}})
    return rows
# === CORE-END ===

# ============================================================================
# 🎨 現代化 CSS 設計系統
# ============================================================================
st.markdown(
    """
<style>
    /* ===== 色彩與基礎變數 ===== */
    :root {
        --primary: #2E7D87;
        --primary-light: #4A9FB5;
        --primary-dark: #1F5561;
        --accent: #E67E22;
        --success: #27AE60;
        --warning: #F39C12;
        --error: #E74C3C;
        --gray-light: #ECF0F1;
        --gray-medium: #BDC3C7;
        --gray-dark: #34495E;
        --text-primary: #2C3E50;
        --text-secondary: #7F8C8D;
        --border-radius: 12px;
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
    }

    /* ===== 全局樣式 ===== */
    body {
        font-family: 'Segoe UI', 'Roboto', '-apple-system', 'BlinkMacSystemFont', sans-serif;
        color: var(--text-primary);
        background-color: #F8FAFB;
    }

    /* ===== 標題美化 ===== */
    h1 {
        color: var(--primary-dark) !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 24px !important;
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    h2 {
        color: var(--primary) !important;
        font-weight: 600 !important;
        margin-top: 28px !important;
        margin-bottom: 16px !important;
        border-bottom: 2px solid var(--primary-light);
        padding-bottom: 8px !important;
    }

    h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-top: 16px !important;
    }

    /* ===== 卡片與容器 ===== */
    .metric-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFB 100%);
        border-radius: var(--border-radius);
        padding: 20px;
        border: 1px solid var(--gray-light);
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
        border-left: 5px solid var(--primary);
    }

    .metric-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .metric-card.accent {
        border-left-color: var(--accent);
    }

    .metric-card.success {
        border-left-color: var(--success);
    }

    .metric-card.warning {
        border-left-color: var(--warning);
    }

    /* ===== Metrics 樣式 ===== */
    [data-testid="metric-container"] {
        background: transparent;
        padding: 0 !important;
    }

    [data-testid="metric-container"] [data-testid="metric-container-card"] {
        border-radius: var(--border-radius);
        border: none;
        padding: 12px 16px;
    }

    /* ===== 標籤與徽章 ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        border-bottom: 2px solid var(--gray-light) !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px !important;
        white-space: pre-wrap !important;
        background-color: transparent !important;
        border-radius: var(--border-radius) var(--border-radius) 0 0 !important;
        border: 2px solid transparent !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary-light) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(46, 125, 135, 0.1) 0%, rgba(46, 125, 135, 0.05) 100%) !important;
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }

    /* ===== 按鈕樣式 ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--border-radius) !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ===== 輸入框美化 ===== */
    .stNumberInput > div > div > input,
    .stSlider > div > div > div > input,
    .stSelectbox > div > div > select,
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 2px solid var(--gray-light) !important;
        padding: 10px 12px !important;
        transition: all 0.3s ease !important;
    }

    .stNumberInput > div > div > input:focus,
    .stSlider > div > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(46, 125, 135, 0.1) !important;
    }

    /* ===== 側邊欄美化 ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFB 100%);
    }

    .stSidebar .stExpander {
        background-color: transparent;
    }

    /* ===== Expander 美化 ===== */
    .stExpander {
        border: 1px solid var(--gray-light);
        border-radius: var(--border-radius);
        overflow: hidden;
    }

    .streamlit-expanderHeader {
        background-color: var(--gray-light) !important;
        color: var(--text-primary) !important;
        border-radius: var(--border-radius) !important;
        padding: 12px 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: rgba(46, 125, 135, 0.1) !important;
    }

    /* ===== Info / Warning 訊息框 ===== */
    .stInfo, [data-testid="stAlert"] {
        border-radius: var(--border-radius) !important;
        border: 1px solid rgba(46, 125, 135, 0.3) !important;
        background-color: rgba(46, 125, 135, 0.05) !important;
        padding: 16px !important;
    }

    .stWarning {
        border: 1px solid rgba(243, 156, 18, 0.3) !important;
        background-color: rgba(243, 156, 18, 0.05) !important;
    }

    .stError {
        border: 1px solid rgba(231, 76, 60, 0.3) !important;
        background-color: rgba(231, 76, 60, 0.05) !important;
    }

    /* ===== 表格美化 ===== */
    .stDataFrame {
        border-radius: var(--border-radius) !important;
        border: 1px solid var(--gray-light) !important;
    }

    /* ===== Divider 美化 ===== */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, var(--primary-light) 50%, transparent 100%);
        margin: 24px 0 !important;
    }

    /* ===== 響應式設計 ===== */
    @media (max-width: 768px) {
        h1 {
            font-size: 24px !important;
        }

        h2 {
            font-size: 18px !important;
        }

        .metric-card {
            padding: 12px 16px !important;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px !important;
            font-size: 12px !important;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# 📋 標題與說明區
# ============================================================================
st.title("🏙️ 新北市防災都更權利變換試算模型")
st.markdown("**論文實證版 | 整合五案件統計數據 | v3.2**")

st.info(
    """
    🔍 **模型說明**

    ✅ 整合新北市五個已送件審議之防災都更案件（其中蘆洲案已核定）之共同負擔費用統計
    ✅ 費率可切換「本研究統計」與「官方對照值」，並依實施主體與安置型態調整
    ✅ 風險管理費率查表、營建單價級距提示、工期估算
    ✅ 實施者 IRR 採論文第 4.3.1 節之簡化現金流假設；預設參數可重現論文表 4-2、表 4-3 與附表 4-1

    💡 左側面板調整參數，結果即時更新。本模型為前期溝通與初步評估之輔助工具，不取代法定估價與審議程序。
    """
)

# ============================================================================
# ⚙️ 側邊欄：參數設定
# ============================================================================
st.sidebar.markdown(
    """
    <div style='background: linear-gradient(135deg, #2E7D87 0%, #4A9FB5 100%);
                color: white; padding: 16px; border-radius: 12px; margin-bottom: 20px;'>
        <h2 style='margin: 0; font-size: 18px; color: white;'>⚙️ 參數設定面板</h2>
        <p style='margin: 4px 0 0 0; font-size: 12px; opacity: 0.9;'>即時調整計算模型</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ========== 0. 參考案件 ==========
st.sidebar.markdown("### 📌 五案件參考模式")
CASE_LABELS = {"自訂設定": None}
CASE_LABELS.update({f"{k}｜{v['location']}（{v['developer']}）": k for k, v in FIVE_CASES_DATA.items()})
case_label = st.sidebar.selectbox(
    "參考案件", list(CASE_LABELS.keys()),
    help="載入該案之實施主體、安置型態與費率（建築設計、拆遷安置、稅捐等）；基地與容積參數請自行輸入",
)
case_key = CASE_LABELS[case_label]
case_data = FIVE_CASES_DATA[case_key] if case_key else None
if case_data:
    st.sidebar.success(f"✅ 已載入 {case_data['location']} 之實施主體與費率")

# ========== 1. 基地與容積 ==========
with st.sidebar.expander("1️⃣ 基地與容積參數", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        base_area = st.number_input("基地面積 (坪)", value=300.0, step=10.0, min_value=1.0)
        far_legal = st.number_input("法定容積率 (%)", value=200.0, step=10.0) / 100
    with col_b:
        far_base_exist = st.number_input("原建築容積率 (%)", value=300.0, step=10.0, min_value=1.0) / 100
        bonus_multiplier = st.number_input("防災獎勵倍數", value=1.5, step=0.1, min_value=0.1)
    col_c, col_d = st.columns(2)
    with col_c:
        coeff_gfa = st.number_input("總樓地板係數 K_GFA", value=1.8, step=0.1, min_value=0.1,
                                    help="總樓地板面積 ÷ 容積樓地板面積")
    with col_d:
        coeff_sale = st.number_input("銷售面積係數 K_Sale", value=1.6, step=0.1, min_value=0.1,
                                     help="可銷售面積 ÷ 容積樓地板面積")

area_far_now = base_area * far_base_exist * bonus_multiplier
area_total_now = area_far_now * coeff_gfa

# ========== 2. 營建與建材 ==========
with st.sidebar.expander("2️⃣ 營建與建材設定", expanded=True):
    const_type = st.selectbox("建材結構等級", ["RC 一般標準 (S0)", "RC 高階 (+0.11)", "SRC/SC (+0.30)"])
    mat_coeff = 0.11 if "高階" in const_type else (0.30 if "SRC" in const_type else 0.0)
    base_unit_cost = st.number_input("提列營建單價 (萬/坪)", value=16.23, step=0.5, min_value=0.1,
                                     help="共同負擔提列所採之營建單價")
    final_unit_cost = base_unit_cost * (1 + mat_coeff)
    paid_unit_input = st.number_input(
        "實付營建單價 (萬/坪，0＝同提列)", value=0.0, step=0.5, min_value=0.0,
        help="用於模擬「核定單價低於實際營造成本」（論文情境 B′）；差額由實施者報酬吸收，不影響共同負擔",
    )
    tier_cost, tier_label = lookup_unit_cost(area_total_now)
    st.markdown(
        f"""
        <div style='background: rgba(230, 126, 34, 0.08); border-left: 4px solid #E67E22;
                    padding: 12px; border-radius: 8px; margin-top: 8px; font-size: 12px;'>
            <strong style='color: #E67E22;'>💡 基準附表三（RC造16–20層，112年8月修正）</strong><br>
            目前總樓地板面積 {area_total_now:,.0f} 坪，屬「{tier_label}」級距：<strong>{tier_cost:.2f} 萬/坪</strong><br>
            您的設定：<strong>{final_unit_cost:.2f} 萬/坪</strong>（建材係數 +{mat_coeff}）<br>
            <span style='color: #7F8C8D;'>三級距單價：17.05／16.23／15.74 萬/坪（物價基準日112年4月）；市場發包價約 21–24 萬/坪（專家訪談）</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ========== 3. 財務與風險 ==========
with st.sidebar.expander("3️⃣ 財務與風險參數", expanded=True):
    col_e, col_f = st.columns(2)
    with col_e:
        num_owners = st.number_input("產權級別 (筆)", value=20, step=5, min_value=1,
                                     help="(門牌戶數＋土地及合法建築物所有權人數聯集)÷2")
        loan_ratio = st.slider("貸款成數 (%)", 40, 80, 60, help="貸款利息提列所採之融資比例") / 100
    with col_f:
        rate_personnel = st.number_input("人事行政管理費率 (%)", value=3.0, step=0.5, min_value=0.0) / 100
        rate_sales = st.number_input("銷售管理費率 (%)", value=6.0, step=0.5, min_value=0.0,
                                     help="以住宅銷售額為基礎") / 100
    col_g, col_h = st.columns(2)
    with col_g:
        loan_rate = st.number_input("貸款年利率 (%)", value=3.0, step=0.1, min_value=0.0) / 100
    with col_h:
        dev_months = st.number_input("開發期程 (月)", value=48, step=6, min_value=12)

    risk_rate = get_risk_fee_rate(area_total_now, num_owners)
    st.markdown(
        f"""
        <div style='background: rgba(39, 174, 96, 0.08); border-left: 4px solid #27AE60; padding: 10px; border-radius: 8px;'>
            <strong style='color: #27AE60;'>✅ 風險管理費率（查表，論文附表3-1）</strong><br>
            <span style='font-size: 14px; font-weight: 700; color: #2C3E50;'>{risk_rate * 100:.1f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar.expander("📈 IRR 試算假設（論文4.3.1）", expanded=False):
    equity_ratio = st.slider("自有資金比例 (%)", 20, 50, 30,
                             help="權益資金＝資金需求×自有資金比例") / 100
    invest_frac = st.slider("權益資金投入期間（占開發期比例）", 0.3, 1.0, 2 / 3, step=0.01,
                            help="權益資金於開發期前段按月平均投入")
    lag_months = st.number_input("完工後銷售結算期 (月)", value=6, step=1, min_value=0)
    st.caption("實施者報酬以風險管理費提列額為上限；實付營建成本高於提列時，差額自報酬扣減。")

with st.sidebar.expander("🏗️ 工期估算（論文3.5.5）", expanded=False):
    col_i, col_j = st.columns(2)
    with col_i:
        floors_up = st.number_input("地上層數", value=16, step=1, min_value=1)
        per_floor = st.selectbox("地上層每層工期 (月)", [1.5, 1.2, 1.0],
                                 format_func=lambda v: {1.5: "1.5（本研究延長情境）", 1.2: "1.2（SRC概估）", 1.0: "1.0（現行基準）"}[v])
    with col_j:
        floors_down = st.number_input("地下層數", value=4, step=1, min_value=0)
        top_down = st.checkbox("逆打工法", value=False)
    build_months = estimate_construction_months(floors_up, floors_down, per_floor, top_down)
    st.caption(f"估算施工期間 **{build_months:.1f} 個月**；加計前期 6 個月與完工後 6 個月，"
               f"建議開發期程約 **{build_months + 12:.0f} 個月**（僅供參考，請於上方「開發期程」自行設定）。")
    st.markdown("**拆遷安置費依工期連動**")
    reloc_linked = st.checkbox("安置費＝登記面積×租金×補貼月數（取代固定比例）", value=False,
                               help="論文4.4.3：未勾選時以營建費×固定比例估列（第四章示例）；勾選後依工期連動計算")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        reg_factor = st.number_input("登記面積係數（×原容積樓地板）", value=1.15, step=0.05, min_value=0.5,
                                     disabled=not reloc_linked, help="論文3.4.3：登記面積≈原建築容積樓地板×1.15")
        pre_months = st.number_input("拆遷至開工 (月)", value=6, step=1, min_value=0, disabled=not reloc_linked)
    with col_r2:
        rent_per_ping = st.number_input("租金水準 (元/坪/月)", value=1000, step=50, min_value=0,
                                        disabled=not reloc_linked, help="受訪者所述約800–1,200元")
        post_months = st.number_input("完工後至產權登記 (月)", value=6, step=1, min_value=0, disabled=not reloc_linked)
    subsidy_months = build_months + pre_months + post_months
    if reloc_linked:
        st.caption(f"補貼月數 {subsidy_months:.0f} 個月（施工 {build_months:.0f}＋前 {pre_months}＋後 {post_months}）；"
                   f"受訪估價師所述實務補貼期約 50–55 個月。")

# ========== 4. 費率設定 ==========
with st.sidebar.expander("4️⃣ 費率設定（占營建費用 %）", expanded=True):
    src_options = ["本研究統計（五案平均）", "官方對照值"] + (["參考案件"] if case_data else [])
    rate_source = st.radio("費率來源", src_options, index=len(src_options) - 1 if case_data else 0,
                           key=f"src_{case_key}")
    developer = st.selectbox("實施主體", ["建設公司", "更新會"],
                             index=1 if (case_data and case_data["developer"] == "更新會") else 0,
                             key=f"dev_{case_key}", help="更新會自辦案件免徵營業稅，稅捐比例較低")
    in_situ = st.checkbox("原地安置（無拆遷補償與安置費）", value=bool(case_data and case_data["in_situ"]),
                          key=f"insitu_{case_key}")

    if rate_source == "參考案件":
        base_rates = {k: case_data[k] for k, _ in ITEMS}
    else:
        base_rates = dict(OFFICIAL_REF if rate_source == "官方對照值" else STATISTICS_AVG)
        if developer == "更新會":
            base_rates["tax"] = TAX_ASSOCIATION["official" if rate_source == "官方對照值" else "stat"]
    if in_situ:
        base_rates["demo_comp"] = base_rates["reloc"] = 0.0

    wkey = f"{case_key}_{rate_source}_{developer}_{in_situ}"
    col_k, col_l = st.columns(2)
    with col_k:
        r_design = st.number_input("建築設計費 (%)", value=float(base_rates["design"]), step=0.1, min_value=0.0, key=f"rd_{wkey}")
        r_tax = st.number_input("稅捐 (%)", value=float(base_rates["tax"]), step=0.1, min_value=0.0, key=f"rt_{wkey}")
    with col_l:
        r_reloc = st.number_input("拆遷安置費 (%)", value=float(base_rates["reloc"]), step=0.1, min_value=0.0, key=f"rr_{wkey}")

    include_extra = st.checkbox(
        "納入拆遷補償費、權變費、容獎管理維護費", value=False,
        help="論文第四章示例試算未計入此三項（見附表4-1註2）；勾選後依下列費率計入共同負擔",
    )
    col_m, col_n = st.columns(2)
    with col_m:
        r_demo_comp = st.number_input("拆遷補償費 (%)", value=float(base_rates["demo_comp"]), step=0.1, min_value=0.0,
                                      key=f"rc_{wkey}", disabled=not include_extra)
        r_bonus_mgmt = st.number_input("容獎管理維護費 (%)", value=float(base_rates["bonus_mgmt"]), step=0.1, min_value=0.0,
                                       key=f"rb_{wkey}", disabled=not include_extra)
    with col_n:
        r_rights = st.number_input("權利變換費 (%)", value=float(base_rates["rights"]), step=0.1, min_value=0.0,
                                   key=f"rg_{wkey}", disabled=not include_extra)

# ========== 5. 進階費用 ==========
with st.sidebar.expander("5️⃣ 進階費用設定（定額估列）", expanded=False):
    cost_bonus_app = st.number_input("容積獎勵申請費 (萬)", value=500, step=50, min_value=0)
    cost_urban_plan = st.number_input("都計變更 / 審議費 (萬)", value=300, step=50, min_value=0)
    cost_transfer = st.number_input("容積移轉 / 折繳代金 (萬)", value=0, step=100, min_value=0)
    demo_unit = st.number_input("拆除費概估單價 (元/坪，以總樓地板面積計)", value=DEMOLITION_UNIT_DEFAULT * 10000,
                                step=50.0, min_value=0.0,
                                help="沿用論文附表4-1「營建工程費（含拆除）」之口徑；金額甚小") / 10000

# ========== 6. 銷售與估價 ==========
with st.sidebar.expander("6️⃣ 估價與銷售參數", expanded=False):
    val_old_total = st.number_input("更新前現況總值 (億元)", value=5.4, step=0.1, min_value=0.0) * 10000
    price_unit_sale = st.number_input("更新後預售單價 (萬/坪)", value=60.0, step=2.0, min_value=1.0)
    price_parking = st.number_input("車位單價 (萬/個)", value=220, step=10, min_value=0)

# ============================================================================
# 🔧 執行模型
# ============================================================================
PARAMS = {
    "base_area": base_area, "far_exist": far_base_exist, "bonus": bonus_multiplier,
    "k_gfa": coeff_gfa, "k_sale": coeff_sale,
    "unit_cost": final_unit_cost, "paid_unit_cost": paid_unit_input if paid_unit_input > 0 else None,
    "price_sale": price_unit_sale, "price_parking": price_parking,
    "risk_rate": None, "owners": num_owners,
    "rate_personnel": rate_personnel, "rate_sales": rate_sales,
    "loan_ratio": loan_ratio, "loan_rate": loan_rate, "dev_months": dev_months,
    "r_design": r_design, "r_reloc": r_reloc, "r_tax": r_tax,
    "include_extra": include_extra, "r_demo_comp": r_demo_comp, "r_rights": r_rights, "r_bonus_mgmt": r_bonus_mgmt,
    "cost_adv": cost_bonus_app + cost_urban_plan + cost_transfer, "demo_unit": demo_unit,
    "equity_ratio": equity_ratio, "invest_frac": invest_frac, "lag_months": lag_months,
    "reloc_linked": reloc_linked, "reg_factor": reg_factor, "rent_per_ping": rent_per_ping, "subsidy_months": subsidy_months,
}


def run(**override) -> dict:
    return compute_model({**PARAMS, **override})


def fmt_irr(v) -> str:
    return "虧損（無正值解）" if v is None else f"{v * 100:.2f}%"


res = run()

# ============================================================================
# 🎯 結果看板
# ============================================================================
st.markdown("### 📊 運算結果看板")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 更新後總價值", f"{res['Total_Value'] / 10000:.2f}億", help="住宅銷售額＋車位價值")
with col2:
    st.metric("📈 共同負擔", f"{res['Total_Cost'] / 10000:.2f}億",
              delta=f"共同負擔率 {res['Burden_Ratio'] * 100:.2f}%", delta_color="off")
with col3:
    st.metric("👥 地主分回比", f"{res['Landlord_Ratio'] * 100:.2f}%", help="1－共同負擔率")
with col4:
    st.metric("📊 實施者年化 IRR", fmt_irr(res["IRR"]),
              delta="受訪專家期望區間 12–15%", delta_color="off",
              help="論文4.3.1簡化現金流：報酬以風險管理費提列額為上限")

area_reg_old = base_area * far_base_exist * 1.15
area_back = res["area_sale"] * res["Landlord_Ratio"]
st.caption(
    f"總樓地板面積 {res['GFA']:,.0f} 坪｜可銷售面積 {res['area_sale']:,.0f} 坪｜車位 {res['num_parking']} 個｜"
    f"管理費合計相當營建費 {res['Mgmt_Ratio'] * 100:.1f}%（五案統計 30.72%）｜"
    f"地主分回面積約 {area_back:,.0f} 坪，為更新前登記面積（原容積×1.15≈{area_reg_old:,.0f} 坪）之 {area_back / area_reg_old:.2f} 倍"
)
if abs(final_unit_cost - tier_cost) > 0.005 and mat_coeff == 0:
    st.caption(f"ℹ️ 提列營建單價 {final_unit_cost:.2f} 萬/坪與基準附表三查表級距（{tier_label}：{tier_cost:.2f} 萬/坪）不同。")

st.divider()

# ============================================================================
# 📑 標籤頁
# ============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📈 成本結構", "🎲 敏感度分析", "📚 情境比較", "📋 詳細明細", "📊 五案件統計", "🧪 回測（WMAPE）"]
)

# ===== TAB 1: 成本結構 =====
with tab1:
    st.subheader("共同負擔成本結構拆解")
    df_cost = pd.DataFrame({"項目": list(res["Details"].keys()), "金額(萬元)": list(res["Details"].values())})
    df_cost = df_cost[df_cost["金額(萬元)"] > 0].reset_index(drop=True)
    df_cost["佔比(%)"] = (df_cost["金額(萬元)"] / df_cost["金額(萬元)"].sum() * 100).round(2)
    fig_cost = px.pie(
        df_cost, values="金額(萬元)", names="項目", hole=0.4,
        color_discrete_sequence=["#2E7D87", "#E67E22", "#27AE60", "#3498DB", "#9B59B6", "#E74C3C",
                                 "#F39C12", "#1ABC9C", "#34495E", "#95A5A6", "#D35400", "#16A085", "#8E44AD"],
        title="成本結構比例（圓環圖）",
    )
    fig_cost.update_layout(height=500, font=dict(size=12), showlegend=True)
    col_chart, col_table = st.columns([0.6, 0.4])
    with col_chart:
        st.plotly_chart(fig_cost, **FULL_WIDTH)
    with col_table:
        st.markdown("#### 成本明細")
        st.dataframe(df_cost.style.format({"金額(萬元)": "{:,.0f}", "佔比(%)": "{:.2f}%"}),
                     **FULL_WIDTH, hide_index=True)
    st.caption("管理費拆為風險管理費（具報酬性質）、人事行政管理費與銷售管理費三項分列。")

# ===== TAB 2: 敏感度分析 =====
with tab2:
    st.subheader("單因子敏感度（±10%）")
    sens_rows = []
    for label, key, base_val in [("住宅預售單價", "price_sale", price_unit_sale), ("營建單價", "unit_cost", final_unit_cost),
                                 ("施工工期（開發期程）", "dev_months", dev_months), ("貸款利率", "loan_rate", loan_rate)]:
        lo, hi = run(**{key: base_val * 0.9}), run(**{key: base_val * 1.1})
        sens_rows.append({"變數": label, "−10%": f"{lo['Landlord_Ratio'] * 100:.2f}%",
                          "基準": f"{res['Landlord_Ratio'] * 100:.2f}%", "＋10%": f"{hi['Landlord_Ratio'] * 100:.2f}%"})
    st.dataframe(pd.DataFrame(sens_rows), **FULL_WIDTH, hide_index=True)
    st.caption("表中數值為地主分回比例。以營建單價 21 萬/坪為基準時，可重現論文表4-3。")

    st.subheader("雙因子熱力圖（房價 × 營建單價）")
    col_sens_a, col_sens_b = st.columns(2)
    with col_sens_a:
        price_range = st.slider("房價變動範圍 (萬/坪)", -15, 15, (-10, 10), key="price_range")
    with col_sens_b:
        cost_range = st.slider("營建單價變動範圍 (萬/坪)", -6, 8, (-4, 6), key="cost_range")
    prices = np.arange(price_unit_sale + price_range[0], price_unit_sale + price_range[1] + 1, 2)
    costs = np.arange(final_unit_cost + cost_range[0], final_unit_cost + cost_range[1] + 1, 1)
    costs = costs[costs > 0]
    z_matrix = [[run(price_sale=float(pv), unit_cost=float(cv))["Landlord_Ratio"] * 100 for pv in prices] for cv in costs]
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_matrix, x=prices, y=np.round(costs, 2), colorscale="Viridis",
        text=[[f"{v:.1f}%" for v in r] for r in z_matrix], texttemplate="%{text}", colorbar=dict(title="地主分回%")))
    fig_heat.update_layout(title="地主分回比例敏感度熱力圖（與主模型同一計算邏輯）",
                           xaxis_title="房價 (萬/坪)", yaxis_title="營建單價 (萬/坪)", height=500, font=dict(size=11))
    st.plotly_chart(fig_heat, **FULL_WIDTH)
    with st.expander("💡 判讀說明"):
        st.markdown("""
        - 顏色越亮（黃色）：地主分回比例越高；顏色越深（紫色）：分回比例越低
        - 房價與營建單價為影響分回比例之兩項主導變數，方向相反
        - 工期與利率對分回比例影響有限，主要影響實施者報酬與時間相關費用
        """)

# ===== TAB 3: 情境比較 =====
with tab3:
    st.subheader("雙軌情境比較（論文表4-2）")
    scen = [("A 官方對標（目前提列單價）", final_unit_cost, None), ("B-1 市場校準", 21.0, None),
            ("B-2 市場校準", 24.0, None), ("B-3 市場校準＋標章成本6.5%", 21.0 * 1.065, None),
            ("B′ 提列受限（實付21）", final_unit_cost, 21.0), ("B′ 提列受限（實付24）", final_unit_cost, 24.0)]
    rows = []
    for name, unit, paid in scen:
        r = run(unit_cost=unit, paid_unit_cost=paid)
        rows.append({"情境": name, "提列單價(萬/坪)": f"{unit:.2f}", "實付單價(萬/坪)": f"{(paid or unit):.2f}",
                     "共同負擔(億元)": f"{r['Total_Cost'] / 10000:.2f}", "共同負擔率": f"{r['Burden_Ratio'] * 100:.2f}%",
                     "地主分回比例": f"{r['Landlord_Ratio'] * 100:.2f}%",
                     "實施者報酬(億元)": f"{r['Profit'] / 10000:.2f}", "年化IRR": fmt_irr(r["IRR"])})
    st.dataframe(pd.DataFrame(rows), **FULL_WIDTH, hide_index=True)
    st.caption("其餘參數沿用左側設定。B′ 情境之共同負擔仍以提列單價核算，實付超出部分自實施者報酬（風險管理費）扣減。")

    st.markdown("#### 費率對照")
    st.dataframe(pd.DataFrame({
        "費用項目": [label for _, label in ITEMS],
        "官方對照值": [f"{OFFICIAL_REF[k]:.2f}%" for k, _ in ITEMS],
        "本研究統計": [f"{STATISTICS_AVG[k]:.2f}%" for k, _ in ITEMS],
    }), **FULL_WIDTH, hide_index=True)
    st.markdown("""
    - **官方對照值**：本研究參照新北市共同負擔基準之提列方式所設定之對照值（基準本身未以營建費固定百分比明定費率）
    - **本研究統計**：五案件實際提列結果之平均（論文表3-2）；更新會自辦案件稅捐約 0.10%
    - **營建單價**：基準附表三（112年8月修正）RC造16–20層 15.74–17.05 萬/坪；專家訪談之市場發包價約 21–24 萬/坪
    """)

# ===== TAB 4: 詳細明細 =====
with tab4:
    st.subheader("詳細成本明細表")
    base_note = {
        "營建工程費": "總樓地板面積×提列營建單價", "拆除費（概估）": "總樓地板面積×概估單價",
        "容積獎勵申請與審議費": "定額估列", "建築設計費": f"營建費×{r_design:.2f}%", "拆遷安置費": (f"登記面積×{rent_per_ping}元×{subsidy_months:.0f}月" if reloc_linked else f"營建費×{r_reloc:.2f}%"),
        "拆遷補償費": f"營建費×{r_demo_comp:.2f}%" if include_extra else "未計入",
        "權利變換費": f"營建費×{r_rights:.2f}%" if include_extra else "未計入",
        "容獎管理維護費": f"營建費×{r_bonus_mgmt:.2f}%" if include_extra else "未計入",
        "風險管理費": f"營建費×{res['Risk_Rate'] * 100:.1f}%（查表）", "人事行政管理費": f"營建費×{rate_personnel * 100:.1f}%",
        "銷售管理費": f"住宅銷售額×{rate_sales * 100:.1f}%",
        "貸款利息": f"資金需求×{loan_ratio * 100:.0f}%×{loan_rate * 100:.2f}%×({dev_months}/12)×0.5", "稅捐": f"營建費×{r_tax:.2f}%",
    }
    detail_rows = [{"費用項目": k, "計算基礎": base_note[k], "金額(萬元)": f"{v:,.0f}"} for k, v in res["Details"].items()]
    detail_rows += [
        {"費用項目": "共同負擔合計", "計算基礎": "—", "金額(萬元)": f"{res['Total_Cost']:,.0f}"},
        {"費用項目": "更新後總價值", "計算基礎": "可銷售面積×預售單價＋車位", "金額(萬元)": f"{res['Total_Value']:,.0f}"},
        {"費用項目": "共同負擔率", "計算基礎": "合計÷更新後總價值", "金額(萬元)": f"{res['Burden_Ratio'] * 100:.2f}%"},
        {"費用項目": "地主分回比例", "計算基礎": "1－共同負擔率", "金額(萬元)": f"{res['Landlord_Ratio'] * 100:.2f}%"},
    ]
    st.dataframe(pd.DataFrame(detail_rows), **FULL_WIDTH, hide_index=True)
    st.markdown("#### 實施者報酬試算（論文4.3.1）")
    benefit = (res["Total_Value"] - val_old_total) / val_old_total if val_old_total > 0 else float("nan")
    st.dataframe(pd.DataFrame([
        {"項目": "資金需求", "數值": f"{res['Fund_Demand']:,.0f} 萬"},
        {"項目": f"權益資金（資金需求×{equity_ratio * 100:.0f}%）", "數值": f"{res['Equity']:,.0f} 萬"},
        {"項目": "風險管理費提列額", "數值": f"{res['Details']['風險管理費']:,.0f} 萬"},
        {"項目": "實付超出提列之營建成本", "數值": f"{res['Overrun']:,.0f} 萬"},
        {"項目": "實施者報酬", "數值": f"{res['Profit']:,.0f} 萬"},
        {"項目": "年化 IRR", "數值": fmt_irr(res["IRR"])},
        {"項目": "開發效益比 (V_New−V_Old)/V_Old", "數值": f"{benefit * 100:.1f}%"},
    ]), **FULL_WIDTH, hide_index=True)

# ===== TAB 5: 五案件統計 =====
with tab5:
    st.subheader("五案件統計數據（論文表3-1、表3-2）")
    st.markdown("#### 表3-1：統計案件基本資訊")
    st.dataframe(pd.DataFrame({
        "案件編號": list(FIVE_CASES_DATA.keys()),
        "地點": [c["location"] for c in FIVE_CASES_DATA.values()],
        "基地面積(坪)": [c["area_ping"] for c in FIVE_CASES_DATA.values()],
        "樓層": [c["floors"] for c in FIVE_CASES_DATA.values()],
        "實施主體": [c["developer"] for c in FIVE_CASES_DATA.values()],
        "共同負擔總額(億)": [round(c["total_cost"] / 1e8, 2) for c in FIVE_CASES_DATA.values()],
    }), **FULL_WIDTH, hide_index=True)

    st.markdown("#### 表3-2：共同負擔費用占營建費用比例")
    tbl = {"費用項目": [label for _, label in ITEMS]}
    for name, c in FIVE_CASES_DATA.items():
        tbl[name] = [f"{c[k]:.2f}%" if c[k] >= 0.1 or c[k] == 0 else f"{c[k]:.3f}%" for k, _ in ITEMS]
    tbl["平均值"] = [f"{STATISTICS_AVG[k]:.2f}%" for k, _ in ITEMS]
    tbl["官方對照值"] = [f"{OFFICIAL_REF[k]:.2f}%" for k, _ in ITEMS]
    tbl["符合度"] = [f"{min(STATISTICS_AVG[k], OFFICIAL_REF[k]) / max(STATISTICS_AVG[k], OFFICIAL_REF[k]) * 100:.0f}%" for k, _ in ITEMS]
    st.dataframe(pd.DataFrame(tbl), **FULL_WIDTH, hide_index=True)
    st.markdown("""
    **說明**
    - 拆遷補償與拆遷安置之平均值以有該項費用之四案計算（排除原地安置之案件5）；稅捐平均以建設公司實施之三案計算
    - 多數項目之統計平均與官方對照值符合度達 90% 以上；拆遷相關費用（0%–8.45%）與稅捐（0.10%–5.30%）之案件間差異較大，分別與安置型態及實施主體有關
    - 管理費用介於 27%–34%，平均 30.72%
    - 樣本僅五案，統計結果之外推性有其限制
    """)

# ===== TAB 6: 回測 =====
with tab6:
    st.subheader("五案例回測（論文3.7.3、表3-10）")
    bt = pd.DataFrame(backtest_table())
    mode_cols = ["官方基準模式", "統計預設模式", "分層校準模式"]
    avg_row = {"案件": "五案平均 WMAPE", "基地面積(坪)": "—", "實施主體": "—",
               **{c: round(bt[c].mean(), 2) for c in mode_cols}}
    bt_show = pd.concat([bt.astype({"基地面積(坪)": str}), pd.DataFrame([avg_row])], ignore_index=True)
    st.dataframe(bt_show.style.format({c: "{:.2f}%" for c in mode_cols}), **FULL_WIDTH, hide_index=True)
    st.markdown(f"""
    - WMAPE＝Σ｜實際比例－預測比例｜／Σ實際比例×100%，比對表3-2之八項費用
    - 三種模式均依實施主體設定稅捐，並對原地安置案件排除拆遷補償與安置費
    - 分層校準：基地未滿 {SMALL_MAX} 坪採管理費 {STRATIFIED_MGMT['small']}%、{SMALL_MAX}–{LARGE_MIN} 坪採 {STRATIFIED_MGMT['mid']}%、{LARGE_MIN} 坪以上採 {STRATIFIED_MGMT['large']}%
    - 「個案精確校準模式」需依各案估價報告與合約逐項微調費率（左側「費率設定」），不在此自動計算
    """)

st.divider()

# ============================================================================
# 📥 報告與下載
# ============================================================================
def generate_report(r: dict) -> str:
    lines = [
        "【新北市防災都更權利變換試算模型｜試算報告】",
        f"產生時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "【版本】v3.2（IRR 依論文4.3.1簡化現金流假設）",
        "=" * 60, "",
        "【一、基地與容積】",
        f"基地面積：{base_area:.2f} 坪｜原建築容積率：{far_base_exist * 100:.1f}%｜防災獎勵倍數：{bonus_multiplier:.2f}",
        f"K_GFA：{coeff_gfa:.2f}｜K_Sale：{coeff_sale:.2f}",
        f"總樓地板面積：{r['GFA']:,.0f} 坪｜可銷售面積：{r['area_sale']:,.0f} 坪｜車位：{r['num_parking']} 個", "",
        "【二、營建與財務】",
        f"提列營建單價：{final_unit_cost:.2f} 萬/坪｜實付營建單價：{(paid_unit_input or final_unit_cost):.2f} 萬/坪",
        f"貸款成數：{loan_ratio * 100:.0f}%｜貸款利率：{loan_rate * 100:.2f}%｜開發期程：{dev_months:.0f} 月",
        f"風險管理費率（查表）：{r['Risk_Rate'] * 100:.1f}%｜實施主體：{developer}｜費率來源：{rate_source}",
        f"拆遷安置費：{'依工期連動（補貼 ' + format(subsidy_months, '.0f') + ' 個月）' if reloc_linked else '營建費×' + format(r_reloc, '.2f') + '%'}", "",
        "【三、共同負擔明細（萬元）】",
    ]
    lines += [f"{k:<14}{v:>14,.0f}" for k, v in r["Details"].items()]
    lines += [
        f"{'共同負擔合計':<14}{r['Total_Cost']:>14,.0f}", "",
        "【四、分配結果】",
        f"更新後總價值：{r['Total_Value'] / 10000:.3f} 億元",
        f"共同負擔率：{r['Burden_Ratio'] * 100:.2f}%｜地主分回比例：{r['Landlord_Ratio'] * 100:.2f}%", "",
        "【五、實施者報酬（論文4.3.1）】",
        f"權益資金：{r['Equity']:,.0f} 萬（資金需求×{equity_ratio * 100:.0f}%）｜報酬：{r['Profit']:,.0f} 萬",
        f"年化 IRR：{fmt_irr(r['IRR'])}（受訪專家期望區間 12–15%）", "",
        "※ 本試算為前期溝通與初步評估之輔助，不取代法定估價與審議程序。",
    ]
    return "\n".join(lines)


def generate_excel(r: dict) -> io.BytesIO:
    output = io.BytesIO()
    df_c = pd.DataFrame(list(r["Details"].items()), columns=["項目", "金額(萬元)"])
    df_s = pd.DataFrame([
        ("更新後總價值(萬元)", r["Total_Value"]), ("共同負擔合計(萬元)", r["Total_Cost"]),
        ("共同負擔率", r["Burden_Ratio"]), ("地主分回比例", r["Landlord_Ratio"]),
        ("資金需求(萬元)", r["Fund_Demand"]), ("權益資金(萬元)", r["Equity"]), ("實施者報酬(萬元)", r["Profit"]),
        ("年化IRR", r["IRR"] if r["IRR"] is not None else "虧損"),
    ], columns=["指標", "數值"])
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_c.to_excel(writer, sheet_name="成本拆解", index=False)
        df_s.to_excel(writer, sheet_name="分配與報酬", index=False)
        pd.DataFrame(backtest_table()).to_excel(writer, sheet_name="回測WMAPE", index=False)
    output.seek(0)
    return output


st.markdown("### 📥 報告與試算結果下載")
col_a, col_b = st.columns(2)
with col_a:
    st.download_button("📝 TXT 報告", data=generate_report(res), file_name="Urban_Renewal_Report_v3.2.txt", mime="text/plain")
with col_b:
    st.download_button("📊 Excel 數據", data=generate_excel(res), file_name="Urban_Renewal_Model_v3.2.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.markdown(
    """
    <div style='text-align: center; margin-top: 40px; color: #7F8C8D; font-size: 12px;'>
        <p>🏫 <strong>論文模型版本 v3.2</strong> | 最後更新：2026年11月10日</p>
        <p>⚠️ 本模型僅供教育研究之用，不構成投資建議；正式權利變換計畫仍應以法定估價與審議程序為準</p>
    </div>
    """,
    unsafe_allow_html=True,
)
