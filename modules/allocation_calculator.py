"""
分配計算模組
計算地主與實施者的權利分配
"""

import pandas as pd
from typing import Dict, Any

class AllocationCalculator:
    """分配計算類別"""
    
    def __init__(self):
        pass
        
    def calculate_allocation(self, params: Dict[str, Any],
                           volume_results: Dict[str, Any],
                           cost_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算權利分配結果
        
        Args:
            params: 輸入參數
            volume_results: 容積計算結果
            cost_results: 成本計算結果
            
        Returns:
            Dict: 分配計算結果
        """
        # 基本參數
        ownership_ratio = params['ownership_ratio']
        market_price = params['market_price']
        scenario_factor = params['scenario_factor']
        
        # 更新後總價值
        total_revenue = (volume_results['saleable_volume_ping'] * 
                        market_price * scenario_factor)
        
        # 扣除共同負擔後的淨價值
        net_value = total_revenue - cost_results['total_cost']
        
        # 地主總分配價值（依土地持分比例）
        owner_total_share = net_value * ownership_ratio
        
        # 實施者分配價值
        developer_share = net_value * (1 - ownership_ratio)
        
        # 個人可分配價值（考慮實際持分）
        personal_allocated_value = owner_total_share
        
        # 換回面積計算
        effective_price = market_price * scenario_factor
        return_area_ping = personal_allocated_value / effective_price if effective_price > 0 else 0
        
        # 計算是否需要補差額
        personal_building_value = params['personal_building_area'] * effective_price
        if personal_allocated_value >= personal_building_value:
            surplus = personal_allocated_value - personal_building_value
            shortfall = 0
        else:
            surplus = 0
            shortfall = personal_building_value - personal_allocated_value
        
        # 投資報酬分析
        roi_analysis = self._calculate_roi_analysis(params, personal_allocated_value, cost_results)
        
        return {
            'total_revenue': total_revenue,
            'net_value': net_value,
            'owner_total_share': owner_total_share,
            'developer_share': developer_share,
            'personal_allocated_value': personal_allocated_value,
            'return_area_ping': return_area_ping,
            'surplus': surplus,
            'shortfall': shortfall,
            'effective_price': effective_price,
            'roi_analysis': roi_analysis,
            'personal_cost_burden': cost_results['total_cost'] * ownership_ratio
        }
    
    def _calculate_roi_analysis(self, params: Dict[str, Any],
                               allocated_value: float,
                               cost_results: Dict[str, Any]) -> Dict[str, Any]:
        """計算投資報酬分析"""
        # 估算原建物價值（簡化估算）
        estimated_original_value = params['personal_building_area'] * params['market_price'] * 0.5
        
        # 個人承擔成本
        personal_cost = cost_results['total_cost'] * params['ownership_ratio']
        
        # 淨收益
        net_benefit = allocated_value - estimated_original_value - personal_cost
        
        # ROI
        if estimated_original_value > 0:
            roi = net_benefit / estimated_original_value
        else:
            roi = 0
        
        return {
            'estimated_original_value': estimated_original_value,
            'personal_cost': personal_cost,
            'net_benefit': net_benefit,
            'roi': roi
        }
    
    def get_allocation_summary_table(self, allocation_results: Dict[str, Any]) -> pd.DataFrame:
        """生成分配摘要表"""
        summary_data = {
            '分配項目': [
                '更新後總價值',
                '總共同負擔',
                '扣負擔後淨價值',
                '地主總分配價值',
                '實施者分配價值',
                '個人可分配價值',
                '換回面積',
                '盈餘/需補差額'
            ],
            '金額/數量': [
                f"{allocation_results['total_revenue']/10000:.0f} 萬元",
                f"{allocation_results['personal_cost_burden']/10000:.0f} 萬元",
                f"{allocation_results['net_value']/10000:.0f} 萬元",
                f"{allocation_results['owner_total_share']/10000:.0f} 萬元",
                f"{allocation_results['developer_share']/10000:.0f} 萬元",
                f"{allocation_results['personal_allocated_value']/10000:.0f} 萬元",
                f"{allocation_results['return_area_ping']:.1f} 坪",
                f"{'盈餘' if allocation_results['surplus'] > 0 else '需補'} {max(allocation_results['surplus'], allocation_results['shortfall'])/10000:.0f} 萬元"
            ]
        }
        
        return pd.DataFrame(summary_data)
    
    def generate_allocation_recommendation(self, allocation_results: Dict[str, Any]) -> Dict[str, str]:
        """生成分配建議"""
        roi = allocation_results['roi_analysis']['roi']
        shortfall = allocation_results['shortfall']
        surplus = allocation_results['surplus']
        
        # 主要建議
        if roi > 0.3:
            primary_recommendation = "投資報酬率良好，建議積極參與都更"
        elif roi > 0.1:
            primary_recommendation = "投資報酬率尚可，可考慮參與都更"
        elif roi > 0:
            primary_recommendation = "投資報酬率偏低，需審慎評估"
        else:
            primary_recommendation = "投資報酬率為負，不建議參與"
        
        # 財務建議
        if surplus > 0:
            financial_advice = f"預估可獲得 {surplus/10000:.0f} 萬元額外收益，財務狀況良好"
        elif shortfall > 0:
            financial_advice = f"需額外補繳 {shortfall/10000:.0f} 萬元，需準備充足資金"
        else:
            financial_advice = "收支平衡，財務風險較低"
        
        # 風險控制
        if allocation_results['personal_cost_burden'] > allocation_results['personal_allocated_value']:
            risk_mitigation = "成本負擔較重，建議爭取更好的分配條件"
        else:
            risk_mitigation = "成本負擔合理，風險可控"
        
        # 談判要點
        return_area = allocation_results['return_area_ping']
        if return_area < 20:
            negotiation_points = "換回面積較小，建議爭取現金補償或調整分配比例"
        elif return_area > 50:
            negotiation_points = "換回面積較大，可考慮部分出售以回收資金"
        else:
            negotiation_points = "換回面積適中，符合一般家庭需求"
        
        return {
            'primary_recommendation': primary_recommendation,
            'financial_advice': financial_advice,
            'risk_mitigation': risk_mitigation,
            'negotiation_points': negotiation_points
        }
