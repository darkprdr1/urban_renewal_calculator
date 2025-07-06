"""
視覺化模組
生成各種 Plotly 圖表
"""

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List

class Visualizer:
    """視覺化類別"""
    
    def kpi_data(self, vol: Dict[str, Any], cost: Dict[str, Any], alloc: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {'title':'總可建坪', 'value':vol['max_volume_ping'], 'unit':'坪'},
            {'title':'可售建坪', 'value':vol['saleable_volume_ping'], 'unit':'坪'},
            {'title':'總開發成本', 'value':cost['total_cost']/1e8, 'unit':'億元'},
            {'title':'地主分配價值', 'value':alloc['personal_allocated_value']/1e6, 'unit':'百萬元'},
            {'title':'換回坪數', 'value':alloc['return_area_ping'], 'unit':'坪'},
            {'title':'需補差額', 'value':alloc['shortfall']/1e6, 'unit':'百萬元'}
        ]
    
    def cost_pie(self, cost_results: Dict[str, Any]) -> go.Figure:
        from modules.cost_calculator import CostCalculator
        return CostCalculator().create_pie_chart(cost_results)
    
    def allocation_bar(self, alloc_results: Dict[str, Any]) -> go.Figure:
        labels = ['地主','實施者']
        values = [alloc_results['personal_allocated_value'], alloc_results['developer_share']]
        fig = go.Figure(data=[go.Bar(x=labels, y=values)])
        fig.update_layout(title_text="價值分配", yaxis_title="元")
        return fig
    
    def sensitivity_radar(self, radar_data: List[Dict[str, Any]]) -> go.Figure:
        fig = go.Figure()
        theta = ['-10%','0%','+10%']
        for item in radar_data:
            fig.add_trace(go.Scatterpolar(
                r=item['values'], theta=theta, fill='toself', name=item['param']
            ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
        return fig
