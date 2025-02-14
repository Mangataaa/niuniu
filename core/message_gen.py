import random
from typing import Dict

class MessageGenerator:
    """消息模板管理类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self._load_templates()
        
    def generate_niuniu_message(self, user_data: dict) -> str:
        """生成牛牛统计消息"""
        stats = [
            ("🤜 主动出击", user_data.get('compare_attempts', 0)),
            ("🛡️ 被挑战", user_data.get('compared_times', 0)),
            ("💦 专注手艺", user_data.get('solo_actions', 0)),
            ("👐 助人为乐", user_data.get('assist_others', 0)),
            ("🎁 获助攻", user_data.get('assisted_times', 0)),
            ("🏆 胜利次数", user_data.get('compare_wins', 0)),
            ("😢 败北次数", user_data.get('compare_losses', 0))
        ]
        # 确保所有统计字段都有默认值
        user_data.setdefault('length', 0.0)
        
        stat_lines = []
        for icon, value in stats:
            stat_lines.append(f"{icon}: {value:^3}")
        
        return (
            f"┌──────── 牛牛战绩 ────────┐\n"
            f"│ 当前长度：{user_data['length']:>6.1f}cm │\n"
            f"├──────────────────────────┤\n"
            f"│ {' '.join(stat_lines[:3])} │\n"
            f"│ {' '.join(stat_lines[3:6])} │\n"
            f"│ {stat_lines[6]:<24} │\n"
            f"└──────────────────────────┘"
        )

    def _load_templates(self):
        """加载消息模板"""
        self.templates = {
            'register': {
                'success': [
                    "{nickname}，注册成功，你的牛牛现在有{length} cm",
                    "{nickname}，牛牛初始化完成，初始长度：{length} cm"
                ],
                'exists': [
                    "{nickname}，你已经注册过牛牛啦！",
                    "{nickname}，不要重复注册哦，牛牛只有一个！"
                ]
            },
            'dajiao': {
                'cooldown': [
                    "{nickname}，你的牛牛还在疲惫状态呢，至少再歇 10 分钟呀！",
                    "{nickname}，牛牛刚刚折腾完，还没缓过来，10 分钟内别再搞啦！"
                ],
                'success': [
                    "{nickname}，这一波操作猛如虎，牛牛蹭蹭地长了{change}cm！\n当前战绩：{stats}",
                    "{nickname}，打胶效果显著，牛牛增长{change}cm！\n{stats}"
                ],
                'stats_format': [
                    "┌────────┬────────┬────────┐\n"
                    "│🤜 {compare_attempts:3} │🛡️ {compared_times:3} │💦 {solo_actions:3}│\n"
                    "├────────┼────────┼────────┤\n"
                    "│👐 {assist_others:3} │🎁 {assisted_times:3} │🏆 {compare_wins:3}│\n"
                    "└────────┴────────┴────────┘"
                ]
            },
            'zhuli_dajiao': {
                'success_both_inc': [
                    "{helper} 助力 {target} 打胶成功！双方牛牛增长{change}cm！\n"
                    "├─ 助攻者战绩：👐 {helper_assists:+d} 🎁 {helper_assisted:+d}\n"
                    "└─ 被助者战绩：💦 {target_solo:+d} 🎁 {target_assisted:+d}",
                    "{helper} 的神助攻让 {target} 牛牛涨{change}cm！\n"
                    "● 助攻方：助力+{helper_assists} 被助+{helper_assisted}\n"
                    "● 受益方：打胶+{target_solo} 被助+{target_assisted}"
                ],
                'fail_both_dec': [
                    "{nickname} 和 {target} 用力过猛，牛牛都缩短了{change}cm！",
                    "{nickname} 和 {target} 操作失误，牛牛各损失了{change}cm！"
                ],
                'fail_self_dec': [
                    "{nickname} 的牛牛因操作不当缩短了{change}cm，而{target}的牛牛安然无恙",
                    "{nickname} 的牛牛意外受损缩短{change}cm，{target}侥幸逃过一劫"
                ],
                'fail_target_dec': [
                    "{target} 的牛牛被{nickname}误伤，缩短了{change}cm！",
                    "{nickname} 的操作导致{target}的牛牛损失了{change}cm！"
                ],
                'no_effect': [
                    "{nickname} 和 {target} 的牛牛互相看了看，什么都没发生...",
                    "{nickname} 和 {target} 的牛牛产生排斥反应，毫无效果"
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

    def format_牛牛_length(self, length: int) -> str:
        """格式化牛牛长度"""
        if length >= 100:
            return f"{length / 100:.2f}m"
        return f"{length}cm"
