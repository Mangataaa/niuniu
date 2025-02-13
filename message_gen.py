import random
from typing import Dict

class MessageGenerator:
    """消息模板管理类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self._load_templates()
        
    def _load_templates(self):
        """加载消息模板"""
        self.templates = {
            'register': {
                'success': [
                    "{nickname}，注册成功，你的cow现在有{length} cm",
                    "{nickname}，cow初始化完成，初始长度：{length} cm"
                ],
                'exists': [
                    "{nickname}，你已经注册过cow啦！",
                    "{nickname}，不要重复注册哦，cow只有一个！"
                ]
            },
            'dajiao': {
                'cooldown': [
                    "{nickname}，你的cow还在疲惫状态呢，至少再歇 10 分钟呀！",
                    "{nickname}，cow刚刚折腾完，还没缓过来，10 分钟内别再搞啦！"
                ],
                'success': [
                    "{nickname}，这一波操作猛如虎，cow蹭蹭地长了{change}cm，厉害啦！",
                    "{nickname}，打胶效果显著，cow一下子就长了{change}cm，前途无量啊！"
                ]
            },
            'nickname': {
                'success': [
                    "{nickname}，昵称已成功修改为：{new_nickname}",
                    "{nickname}，新的昵称 {new_nickname} 已生效！"
                ],
                'format_error': [
                    "指令格式错误，正确格式：修改昵称 新昵称",
                    "请使用「修改昵称 新昵称」的格式进行操作"
                ],
                'cooldown': [
                    "{nickname}，昵称修改太频繁啦，请{remaining_time}分钟后再试"
                ]
            }
        }

    def get_template(self, category: str, sub_type: str) -> str:
        """获取随机模板"""
        return random.choice(self.templates[category][sub_type])

    def format_cow_length(self, length: int) -> str:
        """格式化cow长度"""
        if length >= 100:
            return f"{length / 100:.2f}m"
        return f"{length}cm"