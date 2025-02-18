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
                    "{nickname}，注册成功，你的cow昵称{cowname}，现在有{length} cm",
                    "{nickname}，cow初始化完成，昵称{cowname}，初始长度：{length} cm"
                ],
                'exists': [
                    "{nickname}，你已经注册过cow啦！",
                    "{nickname}，不要重复注册哦，cow只有一个！"
                ]
            },
            'dajiao': {
                "cooldown_messages": [
                    "{nickname}，你的cow还在疲惫状态呢，至少再歇 {dajiao_cd} 分钟呀！",
                    "{nickname}，cow刚刚折腾完，还没缓过来，{dajiao_cd} 分钟内别再搞啦！",
                    "{nickname}，cow累得直喘气，{dajiao_cd} 分钟内可经不起再折腾咯！",
                    "{nickname}，cow正虚弱着呢，等 {dajiao_cd} 分钟让它恢复恢复吧！"
                ],
                "diff_increase_messages": [
                    "{nickname}，你的cow还没完全恢复呢，但它潜力惊人，增长了{change}cm",
                    "{nickname}，你冒险打胶，没想到cow小宇宙爆发，增长了{change}cm",
                    "{nickname}，cow还软绵绵的，你却大胆尝试，结果增长了{change}cm"
                ],
                "diff_decrease_messages": [
                    "{nickname}，你的cow还没恢复，你就急于打胶，导致它缩短了{change}cm",
                    "{nickname}，你不顾cow疲惫，强行打胶，让它缩短了{change}cm",
                    "{nickname}，cow还在虚弱期，你却折腾它，缩短了{change}cm"
                ],
                "diff_no_effect_messages": [
                    "{nickname}，你的cow还没恢复，你打胶也没啥效果哦",
                    "{nickname}，cow没缓过来，你这次打胶白费劲啦",
                    "{nickname}，cow还没力气呢，打胶没作用"
                ],
                "increase_messages": [
                    "{nickname}，你嘿咻嘿咻一下，cow如同雨后春笋般茁壮成长，增长了{change}cm呢",
                    "{nickname}，这一波操作猛如虎，cow蹭蹭地长了{change}cm，厉害啦！",
                    "{nickname}，打胶效果显著，cow一下子就长了{change}cm，前途无量啊！"
                ],
                "decrease_messages": [
                    "{nickname}，哎呀，打胶过度，cow像被霜打的茄子，缩短了{change}cm呢",
                    "{nickname}，用力过猛，cow惨遭重创，缩短了{change}cm，心疼它三秒钟",
                    "{nickname}，这波操作不太妙，cow缩水了{change}cm，下次悠着点啊！"
                ],
                "no_effect_messages": [
                    "{nickname}，这次打胶好像没什么效果哦，再接再厉吧",
                    "{nickname}，打了个寂寞，cow没啥变化，再试试呗",
                    "{nickname}，这波打胶无功而返，cow依旧岿然不动"
                ],
                'cooldown': [
                    "{nickname}，你的cow还在疲惫状态呢，至少再歇 10 分钟呀！",
                    "{nickname}，cow刚刚折腾完，还没缓过来，10 分钟内别再搞啦！"
                ],
                'success': [
                    "{nickname}，这一波操作猛如虎，cow蹭蹭地长了{change}cm！\n当前战绩：{stats}",
                    "{nickname}，打胶效果显著，cow增长{change}cm！\n{stats}"
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
                "cooldown_messages": [
                    "{nickname}，至少再歇 {dajiao_cd} 分钟呀！",
                    "{nickname}，{dajiao_cd} 分钟内别再搞啦！",
                    "{nickname}，{dajiao_cd} 分钟内可经不起再折腾咯！",
                ],
                'success_both_inc': [
                    "{helper} 助力 {target} 打胶成功！双方cow增长{change}cm！\n"
                    "├─ 助攻者战绩：👐 {helper_assists:+d} 🎁 {helper_assisted:+d}\n"
                    "└─ 被助者战绩：💦 {helper_assists:+d} 🎁 {target_assisted:+d}",
                    "{helper} 的神助攻让 {target} cow涨{change}cm！\n"
                    "● 助攻方：助力+{helper_assists} 被助+{helper_assisted}\n"
                    "● 受益方：打胶+{target_solo} 被助+{target_assisted}"
                ],
                'fail_both_dec': [
                    "{nickname} 和 {target} 用力过猛，cow都缩短了{change}cm！",
                    "{nickname} 和 {target} 操作失误，cow各损失了{change}cm！"
                ],
                'fail_self_dec': [
                    "{nickname} 的cow因操作不当缩短了{change}cm，而{target}的cow安然无恙",
                    "{nickname} 的cow意外受损缩短{change}cm，{target}侥幸逃过一劫"
                ],
                'fail_target_dec': [
                    "{target} 的cow被{nickname}误伤，缩短了{change}cm！",
                    "{nickname} 的操作导致{target}的cow损失了{change}cm！"
                ],
                'no_effect': [
                    "{nickname} 和 {target} 的cow互相看了看，什么都没发生...",
                    "{nickname} 和 {target} 的cow产生排斥反应，毫无效果"
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
