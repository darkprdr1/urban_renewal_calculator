# modules/input_handler.py
import streamlit as st
from typing import Dict, Any, Tuple

class InputHandler:
    def __init__(self):
        self.defaults = {
            'total_land_area': 100.0,
            'personal_land_area': 25.0,
            'personal_building_area': 80.0,
            'legal_far': 2.25,
            'unit_cost': 180000,
            'relocation_cost': 4000,
            'design_rate': 0.04,
            'finance_rate': 0.03,
            'management_rate': 0.22,
            'tax_rate': 0.02,
            'market_price': 600000,
            'scenario_factor': 1.0,
            'efficiency_coef': 0.90,
            'sales_coef': 1.45,
            'num_floors': 5,
            'building_year': 1990
        }

    def create_sidebar_inputs(self) -> Dict[str, Any]:
        st.sidebar.title("📝 輸入參數設定")
        st.sidebar.subheader("🏢 基地基本資訊")
        total = st.sidebar.number_input("整塊基地面積（坪）", 10.0, 1000.0, self.defaults['total_land_area'])
        personal = st.sidebar.number_input("個人土地面積（坪）", 1.0, total, self.defaults['personal_land_area'])
        building = st.sidebar.number_input("個人建物面積（坪）", 0.0, 500.0, self.defaults['personal_building_area'])
        legal = st.sidebar.number_input("法定容積率（%）", 100, 800, max(225, int(self.defaults['legal_far']*100))) / 100
        st.sidebar.info(f"持分比例：{personal/total:.2%}")
        far_title = building/ personal if personal>0 else 0
        far_floor = st.sidebar.number_input("建物樓層數", 1, 20, self.defaults['num_floors'])
        far_floor_val = far_floor * 0.6
        est_far = (far_title + far_floor_val)/2
        st.sidebar.info(f"推估原建築容積率：{est_far:.1%}")
        st.sidebar.markdown("---")
        st.sidebar.subheader("📐 容積轉換參數")
        eff = st.sidebar.slider("容積效率係數 η", 0.85, 0.95, self.defaults['efficiency_coef'])
        sal = st.sidebar.slider("銷售係數 σ", 1.30, 1.70, self.defaults['sales_coef'])
        st.sidebar.markdown("---")
        st.sidebar.subheader("💰 共同負擔費用設定")
        uc = st.sidebar.number_input("工程費用單價（元/坪）",100000,300000,self.defaults['unit_cost'])
        rc = st.sidebar.number_input("拆遷補償安置費用（元/坪）",2000,20000,self.defaults['relocation_cost'])
        dr = st.sidebar.slider("設計規劃費率（%）",2.0,8.0,self.defaults['design_rate']*100)/100
        fr = st.sidebar.slider("融資利息率（%）",1.0,8.0,self.defaults['finance_rate']*100)/100
        mr = st.sidebar.slider("管理費率（%）",15.0,30.0,self.defaults['management_rate']*100)/100
        tr = st.sidebar.slider("稅捐及其他費率（%）",1.0,5.0,self.defaults['tax_rate']*100)/100
        st.sidebar.markdown("---")
        st.sidebar.subheader("📈 市場價格設定")
        mp = st.sidebar.number_input("市場單價（萬元/坪）",30.0,150.0,self.defaults['market_price']/10000)*10000
        scen = st.sidebar.selectbox("情境設定",["悲觀（0.9）","基準（1.0）","樂觀（1.1）"],index=1)
        sf = float(scen.split("（")[1].replace("）",""))
        return {
            'total_land_area': total, 'personal_land_area': personal,
            'personal_building_area': building, 'legal_far': legal,
            'estimated_original_far': est_far, 'ownership_ratio': personal/total,
            'num_floors': far_floor, 'building_year': self.defaults['building_year'],
            'efficiency_coef': eff, 'sales_coef': sal,
            'unit_cost': uc, 'relocation_cost': rc,
            'design_rate': dr, 'finance_rate': fr,
            'management_rate': mr, 'tax_rate': tr,
            'market_price': mp, 'scenario_factor': sf
        }

    def validate_inputs(self, p: Dict[str, Any]) -> Tuple[bool, str]:
        if p['total_land_area']<=0: return False,"基地面積必須大於0"
        if p['personal_land_area']<=0: return False,"個人土地面積必須大於0"
        if p['personal_land_area']>p['total_land_area']: return False,"個人土地不能大於基地"
        if p['efficiency_coef']<0.8 or p['efficiency_coef']>1.0: return False,"效率係數應在0.8-1.0"
        if p['sales_coef']<1.2 or p['sales_coef']>1.8: return False,"銷售係數應在1.2-1.8"
        return True,"參數驗證通過"
