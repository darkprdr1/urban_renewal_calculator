"""
敏感度分析模組
評估關鍵參數變動對試算結果的影響
"""

import pandas as pd
from typing import Dict, Any, List
import numpy as np

class SensitivityAnalyzer:
    """敏感度分析類別"""
    
    def __init__(self):
        self.factors = [
            ('unit_cost', '營建單價'),
            ('market_price', '市場單價'),
            ('saleable_ratio', '可售係數'),
            ('design_rate', '設計監造率'),
            ('finance_rate', '融資利率'),
            ('estimated_original_far', '原建築容積率')
        ]
        self.levels = [-0.1, 0.0, 0.1]  # ±10%
    
    def analyze(self, params: Dict[str, Any], calculators: Dict[str, Any]) -> Dict[str, Any]:
        base_alloc = self._run_once(params, calculators)['return_area_ping']
        radar = []
        summary = []
        
        for key, name in self.factors:
            impacts = []
            for lvl in self.levels:
                p = params.copy()
                p[key] = params[key] * (1 + lvl)
                ret = self._run_once(p, calculators)['return_area_ping']
                impacts.append(ret)
            max_imp = max(impacts) - min(impacts)
            radar.append({'param': name, 'values': impacts})
            lvl_str = f"±10%"
            impact_pct = max_imp / base_alloc * 100 if base_alloc>0 else 0
            summary.append({
                '參數': name,
                '影響範圍(坪)': f"{max_imp:.2f}",
                '影響率(%)': f"{impact_pct:.1f}%",
                '等級': '高' if impact_pct>15 else '中' if impact_pct>10 else '低'
            })
        
        return {
            'radar_data': radar,
            'summary_df': pd.DataFrame(summary)
        }
    
    def _run_once(self, p: Dict[str, Any], calc: Dict[str, Any]) -> Dict[str, Any]:
        vol = calc['volume'].calculate_volume(p)
        cost = calc['cost'].calculate_total_costs(p, vol)
        alloc = calc['alloc'].calculate_allocation(p, vol, cost)
        return alloc
