"""
都市更新權利變換試算模型
以新北市防災型都更為例
"""

import streamlit as st
import pandas as pd
import numpy as np

# 導入模組
from modules.input_handler import InputHandler
from modules.volume_calculator import VolumeCalculator
from modules.cost_calculator import CostCalculator
from modules.allocation_calculator import AllocationCalculator
from modules.sensitivity_analyzer import SensitivityAnalyzer
from modules.visualizer import Visualizer
from modules.batch_comparator import BatchComparator

# 頁面配置
st.set_page_config(
    page_title="都市更新權利變換試算模型",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class UrbanRenewalApp:
    """都市更新權利變換試算應用程式主類別"""
    
    def __init__(self):
        self.input_handler = InputHandler()
        self.volume_calculator = VolumeCalculator()
        self.cost_calculator = CostCalculator()
        self.allocation_calculator = AllocationCalculator()
        self.sensitivity_analyzer = SensitivityAnalyzer()
        self.visualizer = Visualizer()
        self.batch_comparator = BatchComparator()
        
    def run(self):
        """運行主應用程式"""
        # 標題
        st.markdown("""
        <div style="text-align: center;">
            <h1>🏙️ 都市更新權利變換試算模型</h1>
            <h3>以新北市防災型都更2.0為例</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 輸入參數
        params = self.input_handler.create_sidebar_inputs()
        
        # 驗證輸入
        is_valid, message = self.input_handler.validate_inputs(params)
        if not is_valid:
            st.error(f"⚠️ 輸入參數錯誤：{message}")
            return
        
        # 執行計算
        try:
            volume_results = self.volume_calculator.calculate_volume(params)
            cost_results = self.cost_calculator.calculate_total_costs(params, volume_results)
            allocation_results = self.allocation_calculator.calculate_allocation(
                params, volume_results, cost_results
            )
            
            # 顯示結果
            self.show_main_results(volume_results, cost_results, allocation_results)
            
        except Exception as e:
            st.error(f"❌ 計算過程發生錯誤：{str(e)}")
            st.info("請檢查輸入參數是否正確，或聯繫系統管理員")
    
    def show_main_results(self, volume_results, cost_results, allocation_results):
        """顯示主要計算結果"""
        st.subheader("📊 權利變換試算結果")
        
        # KPI 指標卡
        kpi_cols = st.columns(3)
        
        with kpi_cols[0]:
            st.metric(
                "總可建坪", 
                f"{volume_results['max_volume_ping']:.1f} 坪",
                delta=f"採用{volume_results['adopted_scheme']}"
            )
        
        with kpi_cols[1]:
            st.metric(
                "可售建坪", 
                f"{volume_results['saleable_volume_ping']:.1f} 坪",
                delta=f"可售率{volume_results['saleable_ratio']:.1%}"
            )
        
        with kpi_cols[2]:
            st.metric(
                "總開發成本", 
                f"{cost_results['total_cost']/1e8:.2f} 億元",
                delta=f"共負比{cost_results['burden_ratio']:.1%}"
            )
        
        kpi_cols2 = st.columns(3)
        
        with kpi_cols2[0]:
            st.metric(
                "個人分配價值", 
                f"{allocation_results['personal_allocated_value']/1e6:.1f} 百萬元"
            )
        
        with kpi_cols2[1]:
            st.metric(
                "換回面積", 
                f"{allocation_results['return_area_ping']:.1f} 坪"
            )
        
        with kpi_cols2[2]:
            if allocation_results['shortfall'] > 0:
                st.metric(
                    "需補差額", 
                    f"{allocation_results['shortfall']/1e6:.1f} 百萬元",
                    delta="需要額外資金",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    "財務狀況", 
                    "收支平衡",
                    delta="✅ 良好",
                    delta_color="normal"
                )
        
        # 圖表展示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 共同負擔費用結構")
            pie_chart = self.visualizer.cost_pie(cost_results)
            st.plotly_chart(pie_chart, use_container_width=True)
            
        with col2:
            st.subheader("📈 價值分配結構")
            bar_chart = self.visualizer.allocation_bar(allocation_results)
            st.plotly_chart(bar_chart, use_container_width=True)

# 主程式入口
if __name__ == "__main__":
    app = UrbanRenewalApp()
    app.run()
