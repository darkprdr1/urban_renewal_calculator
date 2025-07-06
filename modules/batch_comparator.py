"""
多案例比對模組
批次驗證多筆案例誤差
"""

import pandas as pd
from typing import Dict, Any

class BatchComparator:
    """批次比對類別"""
    
    def validate(self, df: pd.DataFrame) -> (bool, str):
        required = {'case_name','total_land_area','personal_land_area','personal_building_area','actual_return_area'}
        if not required.issubset(df.columns):
            return False, f"缺少欄位: {required - set(df.columns)}"
        return True, ""
    
    def compare(self, df: pd.DataFrame, calculators: Dict[str, Any]) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            p = row.to_dict()
            # 轉型
            p['total_land_area'] = float(p['total_land_area'])
            p['personal_land_area'] = float(p['personal_land_area'])
            p['personal_building_area'] = float(p['personal_building_area'])
            # 執行
            vol  = calculators['volume'].calculate_volume(p)
            cost = calculators['cost'].calculate_total_costs(p, vol)
            alloc= calculators['alloc'].calculate_allocation(p, vol, cost)
            pred = alloc['return_area_ping']
            act  = float(p['actual_return_area'])
            abs_e = pred - act
            rel_e = abs_e / act * 100 if act>0 else 0
            level = '優' if abs(rel_e)<=10 else '良' if abs(rel_e)<=20 else '待'
            records.append({
                '案例': p['case_name'],
                '實際坪數': act,
                '預測坪數': pred,
                '絕對誤差': abs_e,
                '相對誤差(%)': rel_e,
                '精度': level
            })
        return pd.DataFrame(records)
