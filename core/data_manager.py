from pathlib import Path
import yaml
import threading
from typing import Dict, Any

class DataManager:
    """cow数据管理类"""
    
    def __init__(self, plugin_dir: str):
        self.data_dir = Path(plugin_dir) / 'data'
        self.niuniu_file = self.data_dir / 'niuniu_lengths.yml'
        self._ensure_directory_exists()
        self.lock = threading.Lock()  # 添加线程锁保证数据安全
        
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

    def increment_stat(self, group_id: str, user_id: str, field: str, amount: int = 1):
        """通用统计字段更新方法"""
        with self.lock:
            data = self.load_niuniu_data()
            group_data = data.get(group_id, {})
            user_data = group_data.get("__users__", {}).get(user_id, {})
            
            # 初始化字段并更新数值
            current_value = user_data.get(field, 0)
            user_data[field] = max(0, current_value + amount)
            
            # 更新数据结构
            data.setdefault(group_id, {}).setdefault("__users__", {})[user_id] = user_data
            self.save_niuniu_data(data)

    def update_niuniu_length(self, user_id: str, user_data: dict):
        """更新全局用户牛牛数据"""
        with self.lock:
            data = self.load_niuniu_data()
            user_id = str(user_id)
            
            # 初始化默认数据结构
            default_data = {
                'length': 10.0,
                'nickname': '',
                'compare_attempts': 0,
                'compared_times': 0,
                'solo_actions': 0,
                'assist_others': 0,
                'assisted_times': 0,
                'compare_wins': 0,
                'compare_losses': 0
            }
            
            # 合并现有数据
            global_users = data.setdefault('__global__', {}).setdefault('__users__', {})
            if user_id in global_users:
                default_data.update(global_users[user_id])
            
            # 更新新数据
            default_data.update(user_data)
            default_data['length'] = max(1.0, default_data['length'])
            
            # 保存更新
            global_users[user_id] = default_data
            self.save_niuniu_data(data)

    def update_niuniu_length(self, user_id: str, user_data: dict):
        """更新用户牛牛数据"""
        with self.lock:
            data = self.load_niuniu_data()
            user_id = str(user_id)
            
            # 初始化默认数据结构
            default_data = {
                'length': 10.0,
                'nickname': '',
                'compare_attempts': 0,
                'compared_times': 0,
                'solo_actions': 0,
                'assist_others': 0,
                'assisted_times': 0,
                'compare_wins': 0,
                'compare_losses': 0
            }
            
            # 合并现有数据
            if user_id in data.get('__global__', {}).get('__users__', {}):
                default_data.update(data['__global__']['__users__'][user_id])
            
            # 更新新数据
            default_data.update(user_data)
            default_data['length'] = max(1.0, default_data['length'])
            
            # 保存更新后的数据
            data.setdefault('__global__', {}).setdefault('__users__', {})[user_id] = default_data
            self.save_niuniu_data(data)

    def update_group_data(self, group_id: str, new_data: Dict[str, Any]):
        """更新群组数据并维护昵称索引"""
        data = self.load_niuniu_data()
        # 初始化用户统计字段
        for user_id, user_data in new_data.items():
            user_data.setdefault('compare_attempts', 0)  # 主动比划
            user_data.setdefault('compared_times', 0)    # 被比划
            user_data.setdefault('solo_actions', 0)      # 打胶
            user_data.setdefault('assist_others', 0)     # 助力他人
            user_data.setdefault('assisted_times', 0)    # 被助力
            user_data.setdefault('compare_wins', 0)      # 比划成功
            user_data.setdefault('compare_losses', 0)    # 比划失败

        # 初始化统计字段
        for user_id, user_data in new_data.items():
            user_data.setdefault('compare_attempts', 0)
            user_data.setdefault('compared_times', 0)
            user_data.setdefault('solo_actions', 0)
            user_data.setdefault('assist_others', 0)
            user_data.setdefault('assisted_times', 0)
            user_data.setdefault('compare_wins', 0)
            user_data.setdefault('compare_losses', 0)

        # 创建昵称索引（统一小写）
        nickname_index = {
            user_data["nickname"].lower(): user_id
            for user_id, user_data in new_data.items()
        }
        # 存储结构改为包含索引和用户数据
        # 初始化用户统计字段
        for user_id, user_data in new_data.items():
            user_data.setdefault('compare_attempts', 0)
            user_data.setdefault('compared_times', 0)
            user_data.setdefault('solo_actions', 0)
            user_data.setdefault('assist_others', 0)
            user_data.setdefault('assisted_times', 0)
            user_data.setdefault('compare_wins', 0)
            user_data.setdefault('compare_losses', 0)

        data[group_id] = {
            "__nickname_index__": nickname_index,
            "__users__": new_data
        }
        self.save_niuniu_data(data)

    def get_group_data(self, group_id: str) -> Dict[str, Any]:
        """获取群组用户数据"""
        data = self.load_niuniu_data()
        return data.get(group_id, {}).get("__users__", {})
