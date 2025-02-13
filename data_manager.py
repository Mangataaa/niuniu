from pathlib import Path
import yaml
from typing import Dict, Any

class DataManager:
    """cow数据管理类"""
    
    def __init__(self, plugin_dir: str):
        self.data_dir = Path(plugin_dir) / 'data'
        self.niuniu_file = self.data_dir / 'niuniu_lengths.yml'
        self._ensure_directory_exists()
        
    def _ensure_directory_exists(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.niuniu_file.exists():
            self.niuniu_file.touch()
    
    def load_niuniu_data(self) -> Dict[str, Dict[str, Any]]:
        """加载牛牛长度数据"""
        try:
            with open(self.niuniu_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"加载数据失败: {e}")
            return {}

    def save_niuniu_data(self, data: Dict[str, Dict[str, Any]]):
        """保存牛牛长度数据"""
        try:
            with open(self.niuniu_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            print(f"保存数据失败: {e}")

    def get_group_data(self, group_id: str) -> Dict[str, Any]:
        """获取群组数据"""
        data = self.load_niuniu_data()
        return data.get(group_id, {})

    def update_group_data(self, group_id: str, new_data: Dict[str, Any]):
        """更新群组数据"""
        data = self.load_niuniu_data()
        data[group_id] = new_data
        self.save_niuniu_data(data)