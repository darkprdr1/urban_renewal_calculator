import streamlit as st
from typing import Dict, Any, Tuple

class InputHandler:
    """輸入參數處理類別（修正版）"""
    
    def __init__(self):
        self.defaults = {
            'total_land_area': 100.0,
            'personal_land_area': 25.0,
            'personal_building_area': 80.0,
            'legal_far': 2.25,     # 225%
            'unit_cost': 180000,   # 工程費用（原營建費用）
            'relocation_cost': 4000,  # 拆遷補償安置費用（原拆除費用）
            'design_rate': 0.04,   # 設計及其他規劃費（修正為4%）
            'finance_rate': 0.03,
            'management_rate': 0.22,  # 管理費（修正為22%）
            'tax_rate': 0.01,
            'market_price': 600000,
            'scenario_factor': 1.0,
            # 新增：拆分可售係數為兩個參數
            'efficiency_coef': 0.90,  # 容積效率係數（0.85-0.95）
            'sales_coef': 1.45,       # 銷售係數（1.3-1.6）
            # 新增：原建築容積率推估參數
            'num_floors': 5,          # 建物樓層數
            'building_year': 1990     # 建築年份
        }

    def create_sidebar_inputs(self) -> Dict[str, Any]:
        """創建側邊欄輸入介面（修正版）"""
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
            help="現有建物的樓地板面積（權狀登記坪數）"
        )
        
        legal_far = st.sidebar.number_input(
            "法定容積率（%）",
            min_value=100,  # 確保最小值合理
            max_value=800,
            value=max(225, int(self.defaults['legal_far'] * 100)), 
            step=25,
            help="依都市計畫規定的容積率"
        ) / 100  # 轉換為小數
        
        st.sidebar.markdown("---")
        
        # 新增：原建築容積率推估參數
        st.sidebar.subheader("🏗️ 原建築資訊（用於容積率推估）")
        
        num_floors = st.sidebar.number_input(
            "建物樓層數",
            min_value=1,
            max_value=20,
            value=self.defaults['num_floors'],
            step=1,
            help="現有建物的地上樓層數"
        )
        
        building_year = st.sidebar.number_input(
            "建築年份",
            min_value=1950,
            max_value=2025,
            value=self.defaults['building_year'],
            step=1,
            help="建物建造或核發建照年份"
        )
        
        # 原建築容積率多重推估展示
        far_from_title = personal_building_area / personal_land_area if personal_land_area > 0 else 0
        far_from_floors = num_floors * 0.6  # 預設建蔽率60%
        estimated_original_far = (far_from_title + far_from_floors) / 2  # 取平均值
        
        st.sidebar.info(f"💡 推估原建築容積率：{estimated_original_far:.1%}")
        st.sidebar.caption(f"　權狀面積法：{far_from_title:.1%}")
        st.sidebar.caption(f"　樓層估算法：{far_from_floors:.1%}")
        
        # 自動計算並顯示相關資訊
        ownership_ratio = personal_land_area / total_land_area
        st.sidebar.info(f"💡 土地持分比例：{ownership_ratio:.2%}")
        
        st.sidebar.markdown("---")
        
        # 修正：容積與面積轉換參數
        st.sidebar.subheader("📐 容積轉換參數")
        
        efficiency_coef = st.sidebar.slider(
            "容積效率係數η", 
            min_value=0.85, 
            max_value=0.95, 
            value=self.defaults['efficiency_coef'], 
            step=0.01,
            help="容積樓地板面積轉換為總樓地板面積的效率係數"
        )
        
        sales_coef = st.sidebar.slider(
            "銷售係數σ", 
            min_value=1.30, 
            max_value=1.70, 
            value=self.defaults['sales_coef'], 
            step=0.01,
            help="總樓地板面積轉換為可售建坪的係數（1.3-1.6為常見範圍）"
        )
        
        # 顯示轉換說明
        st.sidebar.caption("📋 計算說明：")
        st.sidebar.caption("容積樓地板 ÷ η = 總樓地板")
        st.sidebar.caption("總樓地板 × σ = 可售建坪")
        
        st.sidebar.markdown("---")
        
        # 修正：共同負擔費用參數（依附件建議）
        st.sidebar.subheader("💰 共同負擔費用設定")
        
        # 工程費用（原營建費用，約65%）
        unit_cost = st.sidebar.number_input(
            "工程費用單價（元/坪）", 
            min_value=100000, 
            max_value=300000,
            value=self.defaults['unit_cost'], 
            step=5000,
            help="建築工程費用單價，約佔總成本65%"
        )
        
        # 拆遷補償安置費用（原拆除費用，約4%）
        relocation_cost = st.sidebar.number_input(
            "拆遷補償安置費用（元/坪）", 
            min_value=2000, 
            max_value=20000,
            value=self.defaults['relocation_cost'], 
            step=500,
            help="拆遷補償安置費用，約佔總成本4%"
        )
        
        # 設計及其他規劃費（約4%）
        design_rate = st.sidebar.slider(
            "設計及其他規劃費率（%）", 
            min_value=2.0, 
            max_value=8.0,
            value=self.defaults['design_rate'] * 100, 
            step=0.5,
            help="設計及其他規劃費用占工程費用比例，約4%"
        ) / 100
        
        # 融資利息（約3%）
        finance_rate = st.sidebar.slider(
            "融資利息率（%）", 
            min_value=1.0, 
            max_value=8.0,
            value=self.defaults['finance_rate'] * 100, 
            step=0.1,
            help="建設期間融資利息，約佔總成本3%"
        ) / 100
        
        # 管理費（約22%）
        management_rate = st.sidebar.slider(
            "管理費率（%）", 
            min_value=15.0, 
            max_value=30.0,
            value=self.defaults['management_rate'] * 100, 
            step=1.0,
            help="管理費用，約佔總成本22%"
        ) / 100
        
        # 稅捐及其他費用（約1%+1%=2%）
        tax_rate = st.sidebar.slider(
            "稅捐及其他費率（%）", 
            min_value=1.0, 
            max_value=5.0,
            value=self.defaults['tax_rate'] * 100 * 2,  # 稅捐1% + 其他1%
            step=0.1,
            help="稅捐及其他費用，約佔總成本2%"
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
        
        st.sidebar.markdown("---")
        
        # 顯示成本結構預覽
        st.sidebar.subheader("📊 成本結構預覽")
        total_rate = (0.65 + design_rate + finance_rate + management_rate + tax_rate)
        st.sidebar.caption(f"工程費用：65%")
        st.sidebar.caption(f"拆遷補償：4%")
        st.sidebar.caption(f"設計規劃：{design_rate:.1%}")
        st.sidebar.caption(f"融資利息：{finance_rate:.1%}")
        st.sidebar.caption(f"管理費用：{management_rate:.1%}")
        st.sidebar.caption(f"稅捐其他：{tax_rate:.1%}")
        st.sidebar.caption(f"**總計：{total_rate:.1%}**")
        
        # 整合所有參數
        params = {
            'total_land_area': total_land_area,
            'personal_land_area': personal_land_area,
            'personal_building_area': personal_building_area,
            'legal_far': legal_far,
            'estimated_original_far': estimated_original_far,
            'ownership_ratio': ownership_ratio,
            'num_floors': num_floors,
            'building_year': building_year,
            # 修正後的面積轉換參數
            'efficiency_coef': efficiency_coef,
            'sales_coef': sales_coef,
            # 修正後的成本參數
            'unit_cost': unit_cost,
            'relocation_cost': relocation_cost,
            'design_rate': design_rate,
            'finance_rate': finance_rate,
            'management_rate': management_rate,
            'tax_rate': tax_rate,
            'market_price': market_price,
            'scenario_factor': scenario_factor,
            # 容積率推估方法資訊
            'far_from_title': far_from_title,
            'far_from_floors': far_from_floors
        }
        
        return params
    
    def validate_inputs(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證輸入參數（擴充版）"""
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
            return False, "工程費用單價必須大於0"
            
        if params['market_price'] <= 0:
            return False, "市場單價必須大於0"
        
        # 新增：容積轉換參數檢查
        if not 0.8 <= params['efficiency_coef'] <= 1.0:
            return False, "容積效率係數應在0.8-1.0之間"
            
        if not 1.2 <= params['sales_coef'] <= 1.8:
            return False, "銷售係數應在1.2-1.8之間"
        
        # 新增：成本結構合理性檢查
        total_cost_ratio = (0.65 + params['design_rate'] + params['finance_rate'] + 
                           params['management_rate'] + params['tax_rate'])
        if total_cost_ratio > 1.2:  # 總成本率不應超過120%
            return False, f"成本結構不合理，總比例為{total_cost_ratio:.1%}，建議調整各項費率"
        
        return True, "參數驗證通過"
    
    def get_parameter_summary(self, params: Dict[str, Any]) -> Dict[str, str]:
        """生成參數摘要（新增方法）"""
        return {
            "基地資訊": f"總面積{params['total_land_area']:.1f}坪，個人{params['personal_land_area']:.1f}坪（{params['ownership_ratio']:.1%}持分）",
            "容積設定": f"法定{params['legal_far']:.1%}，推估原容{params['estimated_original_far']:.1%}",
            "面積轉換": f"效率係數{params['efficiency_coef']:.2f}，銷售係數{params['sales_coef']:.2f}",
            "主要成本": f"工程{params['unit_cost']:,}元/坪，管理費{params['management_rate']:.1%}",
            "市場條件": f"單價{params['market_price']/10000:.1f}萬/坪，{params['scenario_factor']:.1f}倍情境"
        }
