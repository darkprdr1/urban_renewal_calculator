"""
容積計算模組（修正版）
計算法定容積、原建築容積與防災2.0獎勵容積
整合容積效率係數與銷售係數的正確計算邏輯
"""

from typing import Dict, Any
import math

class VolumeCalculator:
    """容積計算類別（修正版）"""
    
    def __init__(self):
        self.ping_to_sqm = 3.3058  # 坪轉平方公尺係數
        
        # 標準參數設定
        self.standard_floor_height = 3.0  # 標準層高(公尺)
        self.standard_coverage_ratio = 0.6  # 標準建蔽率
        
    def calculate_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算各種容積方案（修正版）
        
        Args:
            params: 輸入參數字典，需包含：
                - total_land_area: 整塊基地面積(坪)
                - legal_far: 法定容積率(小數)
                - personal_land_area: 個人土地面積(坪)
                - personal_building_area: 個人建物面積(坪)
                - efficiency_coef: 容積效率係數(0.85-0.95)
                - sales_coef: 銷售係數(1.3-1.6)
                - num_floors: 樓層數(選填)
                
        Returns:
            Dict: 容積計算結果
        """
        # 基本參數提取
        total_land_area = params['total_land_area']
        legal_far = params['legal_far']
        personal_land_area = params.get('personal_land_area', total_land_area * 0.25)
        personal_building_area = params.get('personal_building_area', 80.0)
        
        # 新增：容積效率係數與銷售係數
        efficiency_coef = params.get('efficiency_coef', 0.90)  # 容積效率係數
        sales_coef = params.get('sales_coef', 1.45)  # 銷售係數
        
        # 1. 法定容積計算
        legal_volume_ping = total_land_area * legal_far
        
        # 2. 原建築容積率多重推估
        estimated_original_far = self._estimate_original_far(
            personal_land_area, 
            personal_building_area,
            params.get('num_floors', None),
            params.get('building_year', None)
        )
        
        # 3. 原建築容積計算
        original_volume_ping = total_land_area * estimated_original_far
        
        # 4. 防災2.0獎勵容積（1.5倍原容）
        disaster_bonus_volume_ping = original_volume_ping * 1.5
        
        # 5. 選擇最優容積方案
        max_volume_ping = max(legal_volume_ping, disaster_bonus_volume_ping)
        
        # 6. 修正版可售建坪計算
        # 階段一：容積樓地板 → 總樓地板
        total_floor_area = max_volume_ping / efficiency_coef
        
        # 階段二：總樓地板 → 可售建坪
        saleable_volume_ping = total_floor_area * sales_coef
        
        # 7. 判斷採用方案
        if max_volume_ping == legal_volume_ping:
            adopted_scheme = "法定容積"
            scheme_basis = f"法定容積率{legal_far:.1%}"
        else:
            adopted_scheme = "防災2.0獎勵容積"
            scheme_basis = f"原容{estimated_original_far:.1%} × 1.5倍獎勵"
        
        # 8. 容積獎勵比例
        if legal_volume_ping > 0:
            bonus_ratio = (max_volume_ping - legal_volume_ping) / legal_volume_ping
        else:
            bonus_ratio = 0
            
        # 9. 坪效計算
        ping_efficiency = saleable_volume_ping / total_land_area
        
        # 10. 分階段面積計算詳情
        volume_breakdown = self._calculate_volume_breakdown(
            max_volume_ping, efficiency_coef, sales_coef
        )
        
        return {
            # 基本容積數據
            'legal_volume_ping': legal_volume_ping,
            'original_volume_ping': original_volume_ping,
            'disaster_bonus_volume_ping': disaster_bonus_volume_ping,
            'max_volume_ping': max_volume_ping,
            
            # 修正版面積計算
            'total_floor_area': total_floor_area,  # 總樓地板面積
            'saleable_volume_ping': saleable_volume_ping,  # 可售建坪
            
            # 係數參數
            'efficiency_coef': efficiency_coef,
            'sales_coef': sales_coef,
            'ping_efficiency': ping_efficiency,  # 坪效
            
            # 方案資訊
            'adopted_scheme': adopted_scheme,
            'scheme_basis': scheme_basis,
            'bonus_ratio': bonus_ratio,
            
            # 推估資訊
            'legal_far': legal_far,
            'estimated_original_far': estimated_original_far,
            'original_far_method': self.original_far_method,
            
            # 詳細分解
            'volume_breakdown': volume_breakdown
        }
    
    def _estimate_original_far(self, personal_land_area: float, 
                              personal_building_area: float,
                              num_floors: int = None,
                              building_year: int = None) -> float:
        """
        多重方法推估原建築容積率
        
        Args:
            personal_land_area: 個人土地面積(坪)
            personal_building_area: 個人建物面積(坪)
            num_floors: 樓層數(選填)
            building_year: 建築年份(選填)
            
        Returns:
            float: 推估的原建築容積率(小數)
        """
        estimates = []
        methods = []
        
        # 方法1：權狀建物面積法
        if personal_land_area > 0 and personal_building_area > 0:
            far_from_title = personal_building_area / personal_land_area
            estimates.append(far_from_title)
            methods.append(f"權狀面積法({far_from_title:.1%})")
        
        # 方法2：樓層×建蔽率估算法  
        if num_floors and num_floors > 0:
            # 依建築年代調整建蔽率
            coverage_ratio = self._get_coverage_by_year(building_year)
            far_from_floors = num_floors * coverage_ratio
            estimates.append(far_from_floors)
            methods.append(f"樓層估算法({num_floors}層×{coverage_ratio:.0%}={far_from_floors:.1%})")
        else:
            # 預設5層估算
            default_floors = 5
            far_from_default = default_floors * self.standard_coverage_ratio
            estimates.append(far_from_default)
            methods.append(f"預設估算法({default_floors}層×{self.standard_coverage_ratio:.0%}={far_from_default:.1%})")
        
        # 方法3：建築年代修正法
        if building_year:
            far_from_year = self._get_far_by_building_year(building_year)
            estimates.append(far_from_year)
            methods.append(f"年代修正法({building_year}年約{far_from_year:.1%})")
        
        # 選擇最合理的估算值
        if len(estimates) >= 2:
            # 取中位數，避免極端值
            estimates.sort()
            median_estimate = estimates[len(estimates)//2]
            self.original_far_method = f"多重驗證法(中位數): {', '.join(methods)}"
        else:
            median_estimate = estimates[0] if estimates else 3.0  # 預設300%
            self.original_far_method = methods[0] if methods else "預設值300%"
        
        # 合理性檢查：容積率應在100%-800%之間
        return max(1.0, min(8.0, median_estimate))
    
    def _get_coverage_by_year(self, building_year: int = None) -> float:
        """依建築年代推估建蔽率"""
        if not building_year:
            return self.standard_coverage_ratio
        
        if building_year < 1980:
            return 0.7  # 早期建築建蔽率較高
        elif building_year < 2000:
            return 0.6  # 中期建築
        else:
            return 0.5  # 現代建築建蔽率較低
    
    def _get_far_by_building_year(self, building_year: int) -> float:
        """依建築年代推估典型容積率"""
        if building_year < 1970:
            return 2.5  # 250%，早期低層建築
        elif building_year < 1990:
            return 3.0  # 300%，中期發展
        elif building_year < 2010:
            return 3.5  # 350%，都市化高峰
        else:
            return 4.0  # 400%，現代高密度
    
    def _calculate_volume_breakdown(self, base_volume: float, 
                                   efficiency: float, sales: float) -> Dict[str, Any]:
        """
        計算容積分解詳情
        
        Args:
            base_volume: 基礎容積(坪)
            efficiency: 容積效率係數
            sales: 銷售係數
            
        Returns:
            Dict: 詳細分解資訊
        """
        # 階段性計算
        stage1_volume = base_volume  # 容積樓地板面積
        stage2_volume = stage1_volume / efficiency  # 總樓地板面積
        stage3_volume = stage2_volume * sales  # 可售建坪
        
        # 各階段增加的面積
        efficiency_add = stage2_volume - stage1_volume  # 容積效率增加
        sales_add = stage3_volume - stage2_volume  # 銷售增加
        
        return {
            'stage1_volume_ping': stage1_volume,
            'stage2_total_floor_ping': stage2_volume,
            'stage3_saleable_ping': stage3_volume,
            'efficiency_addition': efficiency_add,
            'sales_addition': sales_add,
            'total_multiplier': stage3_volume / stage1_volume,
            'explanation': {
                '階段1': f"容積樓地板面積 {stage1_volume:.1f}坪",
                '階段2': f"÷ 效率係數{efficiency:.2f} = 總樓地板{stage2_volume:.1f}坪",
                '階段3': f"× 銷售係數{sales:.2f} = 可售建坪{stage3_volume:.1f}坪"
            }
        }
    
    def get_volume_comparison_table(self, volume_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成容積比較表（修正版）"""
        comparison_data = {
            '容積方案': [
                '法定容積', 
                '原建築容積', 
                '防災2.0獎勵', 
                '最終採用',
                '總樓地板面積',
                '可售建坪'
            ],
            '容積坪數': [
                f"{volume_results['legal_volume_ping']:.1f}",
                f"{volume_results['original_volume_ping']:.1f}",
                f"{volume_results['disaster_bonus_volume_ping']:.1f}",
                f"{volume_results['max_volume_ping']:.1f}",
                f"{volume_results['total_floor_area']:.1f}",
                f"{volume_results['saleable_volume_ping']:.1f}"
            ],
            '計算說明': [
                f"基地×{volume_results['legal_far']:.1%}",
                f"基地×{volume_results['estimated_original_far']:.1%}",
                f"原容積×1.5倍",
                volume_results['adopted_scheme'],
                f"÷效率係數{volume_results['efficiency_coef']:.2f}",
                f"×銷售係數{volume_results['sales_coef']:.2f}"
            ],
            '是否採用': [
                '✓' if volume_results['adopted_scheme'] == '法定容積' else '○',
                '○',
                '✓' if volume_results['adopted_scheme'] == '防災2.0獎勵容積' else '○',
                '✓',
                '→',
                '→'
            ]
        }
        
        return comparison_data
