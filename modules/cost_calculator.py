"""
成本計算模組
計算都市更新共同負擔各項費用
"""

import plotly.graph_objects as go
from typing import Dict, Any

class CostCalculator:
    """成本計算類別"""
    
    def __init__(self):
        self.cost_categories = [
            ('construction', '營建費用'),
            ('demolition', '拆除費用'),
            ('design', '設計監造費用'),
            ('finance', '融資利息'),
            ('management', '管理費用'),
            ('tax_other', '稅捐及其他費用')
        ]
        
    def calculate_total_costs(self, params: Dict[str, Any], 
                              volume_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算總開發成本
        Args:
            params: 輸入參數
            volume_results: 容積計算結果
        Returns:
            Dict: 成本計算結果
        """
        max_vol = volume_results['max_volume_ping']
        # 基地規模係數
        scale = self._scale_factor(params['total_land_area'])
        unit_cost = params['unit_cost'] * scale
        # 各項費用
        construction = max_vol * unit_cost
        demolition = max_vol * 0.3 * params['demo_unit_cost']
        design     = construction * params['design_rate']
        finance    = (construction + demolition + design) * params['finance_rate']
        management = construction * params['management_rate']
        tax_other  = construction * params['tax_rate']
        total = construction + demolition + design + finance + management + tax_other
        # 負擔比率
        revenue = volume_results['saleable_volume_ping'] * params['market_price'] * params['scenario_factor']
        burden_ratio = total / revenue if revenue > 0 else 0
        
        return {
            'construction_cost': construction,
            'demolition_cost': demolition,
            'design_cost': design,
            'finance_cost': finance,
            'management_cost': management,
            'tax_other_cost': tax_other,
            'total_cost': total,
            'burden_ratio': burden_ratio,
            'unit_cost_used': unit_cost
        }
    
    def _scale_factor(self, area: float) -> float:
        if area < 50:    return 1.15
        if area < 100:   return 1.05
        return 1.0
    
    def create_pie_chart(self, cost_results: Dict[str, Any]) -> go.Figure:
        labels = [name for _, name in self.cost_categories]
        values = [
            cost_results['construction_cost'],
            cost_results['demolition_cost'],
            cost_results['design_cost'],
            cost_results['finance_cost'],
            cost_results['management_cost'],
            cost_results['tax_other_cost']
        ]
        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.45,
            textinfo='label+percent'
        )])
        fig.update_layout(title_text="共同負擔費用結構")
        return fig
