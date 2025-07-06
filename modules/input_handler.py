import streamlit as st
from typing import Dict, Any, Tuple

class InputHandler:
    """輸入參數處理類別"""
    
    def __init__(self):
        self.defaults = {
            'total_land_area': 100.0,
            'personal_land_area': 25.0,
            'personal_building_area': 80.0,
            'legal_far': 2.25,     # 225%
            'unit_cost': 180000,
            'demo_unit_cost': 4000,
            'design_rate': 0.10,
            'finance_rate': 0.03,
            'management_rate': 0.025,
            'tax_rate': 0.01,
            'market_price': 600000,
            'scenario_factor': 1.0,
            'saleable_ratio': 0.75
        }

    def create_sidebar_inputs(self) -> Dict[str, Any]:
        """創建側邊欄輸入介面"""
        st.sidebar.title("📝 輸入參數設定")
        
        # 基地基本資訊
        st.sidebar.subheader("🏢 基地基本資訊")
        
        total_land_area = st.sidebar.number_input(
            "整塊基地面積（坪）",
            min_value=10.0, 
            max_value=1000.0,
            value=self.defaults['total_land_area'], 
            step=1.0,
            help="整個都更範圍的總土地面積"
        )
        
        personal_land_area = st.sidebar.number_input(
            "個人土地面積（坪）",
            min_value=1.0, 
            max_value=total_land_area,
            value=min(self.defaults['personal_land_area'], total_land_area), 
            step=0.1,
            help="您個人名下的土地面積"
        )
        
        personal_building_area = st.sidebar.number_input(
            "個人建物面積（坪）",
            min_value=0.0, 
            max_value=500.0,
            value=self.defaults['personal_building_area'], 
            step=1.0,
            help="現有建物的樓地板面積"
        )
        
        legal_far = st.sidebar.number_input(
            "法定容積率（%）",
            min_value=100,  # 修正：確保最小值合理
            max_value=800,
            value=max(225, int(self.defaults['legal_far'] * 100)), 
            step=25,
            help="依都市計畫規定的容積率"
        ) / 100  # 轉換為小數
        
        # 自動計算並顯示相關資訊
        ownership_ratio = personal_land_area / total_land_area
        st.sidebar.info(f"💡 土地持分比例：{ownership_ratio:.2%}")
        
        if personal_building_area > 0 and personal_land_area > 0:
            estimated_original_far = personal_building_area / personal_land_area
            st.sidebar.info(f"💡 推估原建築容積率：{estimated_original_far:.1%}")
        else:
            estimated_original_far = 3.0  # 300%
        
        st.sidebar.markdown("---")
        
        # 成本參數設定
        st.sidebar.subheader("💰 成本參數設定")
        
        unit_cost = st.sidebar.number_input(
            "營建單價（元/坪）", 
            min_value=100000, 
            max_value=300000,
            value=self.defaults['unit_cost'], 
            step=5000,
            help="參考新北市提列基準，依建築等級調整"
        )
        
        demo_unit_cost = st.sidebar.number_input(
            "拆除單價（元/坪）", 
            min_value=2000, 
            max_value=8000,
            value=self.defaults['demo_unit_cost'], 
            step=200,
            help="建物拆除費用單價"
        )
        
        design_rate = st.sidebar.slider(
            "設計監造率（%）", 
            min_value=5.0, 
            max_value=15.0,
            value=self.defaults['design_rate'] * 100, 
            step=0.5,
            help="設計監造費用占營建費用比例"
        ) / 100
        
        finance_rate = st.sidebar.slider(
            "融資利率（%）", 
            min_value=1.0, 
            max_value=8.0,
            value=self.defaults['finance_rate'] * 100, 
            step=0.1,
            help="建設期間融資利率"
        ) / 100
        
        management_rate = st.sidebar.slider(
            "管理費率（%）", 
            min_value=1.0, 
            max_value=5.0,
            value=self.defaults['management_rate'] * 100, 
            step=0.1,
            help="管理費用占營建費用比例"
        ) / 100
        
        tax_rate = st.sidebar.slider(
            "稅捐費率（%）", 
            min_value=0.5, 
            max_value=3.0,
            value=self.defaults['tax_rate'] * 100, 
            step=0.1,
            help="稅捐及其他費用比例"
        ) / 100
        
        st.sidebar.markdown("---")
        
        # 市場價格設定
        st.sidebar.subheader("📈 市場價格設定")
        
        market_price = st.sidebar.number_input(
            "市場單價（萬元/坪）", 
            min_value=30.0, 
            max_value=150.0,
            value=self.defaults['market_price'] / 10000, 
            step=5.0,
            help="參考實價登錄附近行情"
        ) * 10000  # 轉換為元/坪
        
        scenario = st.sidebar.selectbox(
            "情境設定", 
            ["悲觀（0.9）", "基準（1.0）", "樂觀（1.1）"],
            index=1,
            help="市場價格情境假設"
        )
        scenario_factor = float(scenario.split("（")[1].replace("）", ""))
        
        saleable_ratio = st.sidebar.slider(
            "可售係數", 
            min_value=0.65, 
            max_value=0.85,
            value=self.defaults['saleable_ratio'], 
            step=0.01,
            help="實際可銷售面積佔總樓地板面積比例"
        )
        
        # 整合所有參數
        params = {
            'total_land_area': total_land_area,
            'personal_land_area': personal_land_area,
            'personal_building_area': personal_building_area,
            'legal_far': legal_far,
            'estimated_original_far': estimated_original_far,
            'ownership_ratio': ownership_ratio,
            'unit_cost': unit_cost,
            'demo_unit_cost': demo_unit_cost,
            'design_rate': design_rate,
            'finance_rate': finance_rate,
            'management_rate': management_rate,
            'tax_rate': tax_rate,
            'market_price': market_price,
            'scenario_factor': scenario_factor,
            'saleable_ratio': saleable_ratio
        }
        
        return params
    
    def validate_inputs(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證輸入參數"""
        # 基本數值檢查
        if params['total_land_area'] <= 0:
            return False, "基地面積必須大於0"
            
        if params['personal_land_area'] <= 0:
            return False, "個人土地面積必須大於0"
            
        if params['personal_land_area'] > params['total_land_area']:
            return False, "個人土地面積不能大於總基地面積"
            
        if params['legal_far'] <= 0:
            return False, "法定容積率必須大於0"
            
        if params['unit_cost'] <= 0:
            return False, "營建單價必須大於0"
            
        if params['market_price'] <= 0:
            return False, "市場單價必須大於0"
        
        return True, "參數驗證通過"
