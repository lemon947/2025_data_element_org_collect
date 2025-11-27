# province_extractor.py
class ProvinceExtractor:
    """省份名称提取器，用于从用户输入中识别省份"""
    
    def __init__(self):
        # 完整的省份列表
        self.province_list = [
            "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
            "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
            "浙江省", "安徽省", "福建省", "江西省", "山东省",
            "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
            "海南省", "重庆市", "四川省", "贵州省", "云南省",
            "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
            "新疆维吾尔自治区"
        ]
        
        # 省份简称到全称的映射
        self.province_shortnames = {
            "北京": "北京市", "天津": "天津市", "河北": "河北省", "山西": "山西省", 
            "内蒙古": "内蒙古自治区", "辽宁": "辽宁省", "吉林": "吉林省", 
            "黑龙江": "黑龙江省", "上海": "上海市", "江苏": "江苏省",
            "浙江": "浙江省", "安徽": "安徽省", "福建": "福建省", "江西": "江西省",
            "山东": "山东省", "河南": "河南省", "湖北": "湖北省", "湖南": "湖南省",
            "广东": "广东省", "广西": "广西壮族自治区", "海南": "海南省",
            "重庆": "重庆市", "四川": "四川省", "贵州": "贵州省", "云南": "云南省",
            "西藏": "西藏自治区", "陕西": "陕西省", "甘肃": "甘肃省", 
            "青海": "青海省", "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区"
        }
    
    def extract_provinces(self, text: str) -> list:
        """从用户输入文本中提取省份名称
        
        Args:
            text: 用户输入的文本
            
        Returns:
            list: 提取到的省份名称列表
        """
        found_provinces = []
        
        # 首先查找完整省份名称
        for province in self.province_list:
            if province in text:
                found_provinces.append(province)
        
        # 如果没有找到完整名称，查找省份简称
        if not found_provinces:
            for short, full in self.province_shortnames.items():
                if short in text:
                    found_provinces.append(full)
        
        # 去重后返回
        return list(set(found_provinces))