"""
容積計算模組
計算法定容積、原建築容積與防災2.0獎勵容積
"""

from typing import Dict, Any

class VolumeCalculator:
    """容積計算類別"""
    
    def __init__(self):
        self.ping_to_sqm = 3.3058  # 坪轉平方公尺係數
        
    def calculate_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算各種容積方案
        
        Args:
            params: 輸入參數字典
            
        Returns:
            Dict: 容積計算結果
        """
        # 基本參數
        total_land_area = params['total_land_area']
        legal_far = params['legal_far']
        estimated_original_far = params['estimated_original_far']
        saleable_ratio = params['saleable_ratio']
        
        # 法定容積計算
        legal_volume_ping = total_land_area * legal_far
        
        # 原建築容積計算
        original_volume_ping = total_land_area * estimated_original_far
        
        # 防災2.0獎勵容積（1.5倍原容）
        disaster_bonus_volume_ping = original_volume_ping * 1.5
        
        # 選擇最優容積方案
        max_volume_ping = max(legal_volume_ping, disaster_bonus_volume_ping)
        
        # 可售建坪計算
        saleable_volume_ping = max_volume_ping * saleable_ratio
        
        # 判斷採用方案
        if max_volume_ping == legal_volume_ping:
            adopted_scheme = "法定容積"
        else:
            adopted_scheme = "防災2.0獎勵容積"
        
        # 容積獎勵比例
        if legal_volume_ping > 0:
            bonus_ratio = (max_volume_ping - legal_volume_ping) / legal_volume_ping
        else:
            bonus_ratio = 0
        
        return {
            'legal_volume_ping': legal_volume_ping,
            'original_volume_ping': original_volume_ping,
            'disaster_bonus_volume_ping': disaster_bonus_volume_ping,
            'max_volume_ping': max_volume_ping,
            'saleable_volume_ping': saleable_volume_ping,
            'saleable_ratio': saleable_ratio,
            'adopted_scheme': adopted_scheme,
            'bonus_ratio': bonus_ratio,
            'legal_far': legal_far,
            'estimated_original_far': estimated_original_far
        }
