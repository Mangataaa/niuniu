import random
import yaml
import os
import re
import time
from astrbot.api.all import *

from pathlib import Path
from .core.data_manager import DataManager
from .core.cool_down import CoolDownManager, group_cooldown, user_cooldown
from .core.message_gen import MessageGenerator

@register("niuniu_plugin", "长安某", "cow插件，包含注册cow、打胶、我的cow、比划比划、cow排行等功能", "2.2.0")
class NiuniuPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        from collections import defaultdict
        self.config = config or {}
        self.data_manager = DataManager(str(Path(__file__).parent))
        self.cool_down_manager = CoolDownManager()
        self.msg_gen = MessageGenerator(self.config)
        # 初始化冷却时间记录器
        self.last_dajiao_time = defaultdict(dict)    # 群组打胶时间 {group_id: {user_id: timestamp}}
        self.invite_count = defaultdict(dict)        # 邀请计数 {group_id: {user_id: (timestamp, count)}}
        self.last_compare_time = defaultdict(
            lambda: defaultdict(dict))               # 比划时间 {group_id: {user_id: {target_id: timestamp}}}

    def _create_niuniu_lengths_file(self):
        """创建 niuniu_lengths.yml 文件"""
        niuniu_lengths_file = self.data_manager.niuniu_file
        niuniu_lengths_file.parent.mkdir(parents=True, exist_ok=True)
        if not niuniu_lengths_file.exists():
            with open(niuniu_lengths_file, 'w', encoding='utf-8') as file:
                yaml.dump({}, file, allow_unicode=True)

    # 移除独立的数据存储方法，统一使用data_manager

    def get_niuniu_config(self):
        """获取cow相关配置"""
        return self.config.get('niuniu_config', {})

    def check_probability(self, probability):
        """检查是否满足给定概率条件"""
        return random.random() < probability

    def format_niuniu_message(self, message, length):
        """格式化cow相关消息"""
        if length >= 100:
            length_str = f"{length / 100:.2f}m"
        else:
            length_str = f"{length}cm"
        return f"{message}，当前cow长度为{length_str}"

    @event_message_type(EventMessageType.ALL)
    async def on_all_messages(self, event: AstrMessageEvent):
        """全局事件监听，处理所有消息"""
        group_id = event.message_obj.group_id if hasattr(event.message_obj, "group_id") else None
        if not group_id:
            return

        message_str = event.message_str.strip()

        if message_str == "注册cow":
            async for result in self.register_niuniu(event):
                yield result
        elif message_str == "打胶":
            async for result in self.dajiao(event):
                yield result
        elif message_str == "我的cow":
            async for result in self.my_niuniu(event):
                yield result
        elif message_str.startswith("比划比划"):
            parts = message_str.split(maxsplit=1)
            target_name = parts[1].strip() if len(parts) > 1 else None
            async for result in self.compare_niuniu(event, target_name):
                yield result
        elif message_str == "cow排行":
            async for result in self.niuniu_rank(event):
                yield result
        elif message_str == "cow菜单":
            async for result in self.niuniu_menu(event):
                yield result
        elif message_str.startswith("修改昵称"):
            async for result in self.change_nickname(event):
                yield result

        yield event

    def parse_at_users(self, event: AstrMessageEvent):
        """解析消息中的 @ 用户"""
        chain = event.message_obj.message
        return [str(comp.qq) for comp in chain if isinstance(comp, At)]

    async def register_niuniu(self, event: AstrMessageEvent):
        """注册cow指令处理函数"""
        user_id = str(event.get_sender_id())
        sender_nickname = event.get_sender_name()
        group_id = str(event.message_obj.group_id)
        
        if not group_id:
            yield event.plain_result("该指令仅限群聊中使用。")
            return

        group_data = self.data_manager.get_group_data(group_id)
        
        if user_id in group_data:
            template = self.msg_gen.get_template('register', 'exists')
            yield event.plain_result(template.format(nickname=sender_nickname))
            return

        config = self.config.get('niuniu_config', {})
        length = random.randint(config.get('min_length', 1),
                               config.get('max_length', 10))
        
        # 生成1-4个随机中文字符的昵称
        def generate_random_nickname():
            chinese_chars = ['孤', '傲', '狂', '战', '天', '霸', '帝', '王', '龙', '虎']
            return ''.join(random.choices(chinese_chars, k=random.randint(1,4)))
        
        # 确保立即保存到文件
        new_user_data = {
            "nickname": generate_random_nickname(),
            "length": length
        }
        group_data = self.data_manager.get_group_data(group_id) or {}
        group_data[user_id] = new_user_data
        self.data_manager.update_group_data(group_id, group_data)
        
        template = self.msg_gen.get_template('register', 'success')
        yield event.plain_result(template.format(
            nickname=sender_nickname,
            length=length
        ))

    async def dajiao(self, event: AstrMessageEvent):
        """打胶指令处理函数"""
        user_id = str(event.get_sender_id())
        sender_nickname = event.get_sender_name()
        group_id = event.message_obj.group_id
        group_data = self.data_manager.get_group_data(str(group_id))
        if group_id and user_id in group_data:
            user_info = group_data[user_id]
            # 检查冷却期
            current_time = time.time()

            group_dajiao_time = self.last_dajiao_time.setdefault(group_id, {})
            last_time = group_dajiao_time.get(user_id, 0)
            time_diff = current_time - last_time

            # 十分钟内不允许打胶
            MIN_COOLDOWN = 10 * 60
            if time_diff < MIN_COOLDOWN:
                cooldown_messages = [
                    f"{sender_nickname}，你的cow还在疲惫状态呢，至少再歇 10 分钟呀！",
                    f"{sender_nickname}，cow刚刚折腾完，还没缓过来，10 分钟内别再搞啦！",
                    f"{sender_nickname}，cow累得直喘气，10 分钟内可经不起再折腾咯！",
                    f"{sender_nickname}，cow正虚弱着呢，等 10 分钟让它恢复恢复吧！"
                ]
                yield event.plain_result(random.choice(cooldown_messages))
                return

            # 超过十分钟但低于三十分钟，越接近十分钟越容易失败
            THIRTY_MINUTES = 30 * 60
            if time_diff < THIRTY_MINUTES:
                failure_probability = (THIRTY_MINUTES - time_diff) / (THIRTY_MINUTES - MIN_COOLDOWN)
                config = self.get_niuniu_config()
                min_change = config.get('min_change', -5)
                max_change = config.get('max_change', 5)

                increase_messages = [
                    "{nickname}，你的cow还没完全恢复呢，但它潜力惊人，增长了{change}cm",
                    "{nickname}，你冒险打胶，没想到cow小宇宙爆发，增长了{change}cm",
                    "{nickname}，cow还软绵绵的，你却大胆尝试，结果增长了{change}cm"
                ]
                decrease_messages = [
                    "{nickname}，你的cow还没恢复，你就急于打胶，导致它缩短了{change}cm",
                    "{nickname}，你不顾cow疲惫，强行打胶，让它缩短了{change}cm",
                    "{nickname}，cow还在虚弱期，你却折腾它，缩短了{change}cm"
                ]
                no_effect_messages = [
                    "{nickname}，你的cow还没恢复，你打胶也没啥效果哦",
                    "{nickname}，cow没缓过来，你这次打胶白费劲啦",
                    "{nickname}，cow还没力气呢，打胶没作用"
                ]

                if self.check_probability(failure_probability):
                    change = random.randint(min_change, 0)
                    positive_change = -change
                    message = random.choice(decrease_messages).format(nickname=sender_nickname, change=positive_change)
                else:
                    change = random.randint(0, max_change)
                    if change > 0:
                        message = random.choice(increase_messages).format(nickname=sender_nickname, change=change)
                    else:
                        message = random.choice(no_effect_messages).format(nickname=sender_nickname)

                user_info["length"] = max(1, user_info["length"] + change)
                self._save_niuniu_lengths()
                # 更新上次打胶时间
                # self.last_dajiao_time[user_id] = current_time
                self.data_manager.update_group_data(str(group_id), group_data)
                self.last_dajiao_time[group_id][user_id] = current_time
                yield event.plain_result(self.format_niuniu_message(message, user_info["length"]))
                return

            # 三十分钟后正常判定
            config = self.get_niuniu_config()
            min_change = config.get('min_change', -5)
            max_change = config.get('max_change', 5)

            increase_messages = [
                "{nickname}，你嘿咻嘿咻一下，cow如同雨后春笋般茁壮成长，增长了{change}cm呢",
                "{nickname}，这一波操作猛如虎，cow蹭蹭地长了{change}cm，厉害啦！",
                "{nickname}，打胶效果显著，cow一下子就长了{change}cm，前途无量啊！"
            ]
            decrease_messages = [
                "{nickname}，哎呀，打胶过度，cow像被霜打的茄子，缩短了{change}cm呢",
                "{nickname}，用力过猛，cow惨遭重创，缩短了{change}cm，心疼它三秒钟",
                "{nickname}，这波操作不太妙，cow缩水了{change}cm，下次悠着点啊！"
            ]
            no_effect_messages = [
                "{nickname}，这次打胶好像没什么效果哦，再接再厉吧",
                "{nickname}，打了个寂寞，cow没啥变化，再试试呗",
                "{nickname}，这波打胶无功而返，cow依旧岿然不动"
            ]

            change = random.randint(min_change, max_change)
            if change > 0:
                message = random.choice(increase_messages).format(nickname=sender_nickname, change=change)
            elif change < 0:
                positive_change = -change
                message = random.choice(decrease_messages).format(nickname=sender_nickname, change=positive_change)
            else:
                message = random.choice(no_effect_messages).format(nickname=sender_nickname)

            user_info["length"] = max(1, user_info["length"] + change)
            self.data_manager.update_group_data(str(group_id), group_data)
            # 更新上次打胶时间
            # self.last_dajiao_time[user_id] = current_time
            self.last_dajiao_time[group_id][user_id] = current_time
            yield event.plain_result(self.format_niuniu_message(message, user_info["length"]))
        else:
            yield event.plain_result(f"{sender_nickname}，你还没有注册cow，请先发送“注册cow”进行注册。")

    async def my_niuniu(self, event: AstrMessageEvent):
        """我的cow指令处理函数"""
        user_id = str(event.get_sender_id())
        sender_nickname = event.get_sender_name()
        group_id = str(event.message_obj.group_id)
        group_data = self.data_manager.get_group_data(group_id)
        if group_data and user_id in group_data:
            user_info = group_data[user_id]
            length = user_info["length"]

            # 根据长度给出评价（修改）
            if length <= 5:
                evaluations = ["还处于萌芽阶段呢", "小小的也很可爱"]
            elif length <= 12:
                evaluations = ["像一只蚕宝宝", "小趴菜", "行不行阿，小老弟", "也是到平均水平了呢"]
            elif length <= 24:
                evaluations = ["中规中矩，有提升空间", "一般阿", "哥哥好厉害我好爱❤️"]
            elif length <= 24:
                evaluations = ["表现还不错，继续加油", "算是有点小实力啦", "看看爸爸的大cow"]
            elif length <= 36:
                evaluations = ["简直就是巨无霸", "太猛了，令人惊叹", "无敌的存在呀"]
            else:
                evaluations = ["突破天际的超级巨物", "神话般的存在，无人能及", "已经超越常理的长度啦", "你比黑哥哥厉害",
                               "已经要到捅穿的程度"]

            evaluation = random.choice(evaluations)
            if length >= 100:
                length_str = f"{length / 100:.2f}m"
            else:
                length_str = f"{length}cm"
            yield event.plain_result(f"{sender_nickname}，你的cow长度为{length_str}，{evaluation}")
        else:
            yield event.plain_result(f"{sender_nickname}，你还没有注册cow，请先发送“注册cow”进行注册。")

    async def compare_niuniu(self, event: AstrMessageEvent, target_name: str = None):
        """比划比划指令处理函数"""
        user_id = str(event.get_sender_id())
        sender_nickname = event.get_sender_name()
        group_id = str(event.message_obj.group_id)

        if group_id:
            # 获取以昵称为key的数据结构
            group_data = self.data_manager.get_group_data(group_id) or {}
            nickname_data = {info["nickname"]: info for info in group_data.values()}
            
            # 获取当前用户昵称
            current_user_nickname = next((info["nickname"] for uid, info in group_data.items() if uid == user_id), None)
            if not current_user_nickname:
                yield event.plain_result(f"{sender_nickname}，你还没有注册cow，请先发送“注册cow”进行注册。")
                return
            at_users = self.parse_at_users(event)
            target_user_id = None

            # 直接使用昵称匹配
            if target_name:
                from difflib import get_close_matches
                # 获取所有已注册昵称（排除自己）
                current_nickname = group_data[user_id]["nickname"]
                all_nicknames = [info["nickname"] for uid, info in group_data.items() if uid != user_id]
                
                if not all_nicknames:
                    yield event.plain_result(f"{sender_nickname}，当前群组没有其他已注册cow的用户。")
                    return
                    
                matches = get_close_matches(target_name, all_nicknames, n=1, cutoff=0.6)
                
                if not matches:
                    yield event.plain_result(f"{sender_nickname}，未找到包含 '{target_name}' 的已注册cow用户。")
                    return
                
                target_nickname = matches[0]
                
                # 检查是否是自己
                if target_nickname == current_nickname:
                    yield event.plain_result(f"{sender_nickname}，你不能和自己比划。")
                    return
            else:
                yield event.plain_result(f"{sender_nickname}，请 @ 一名已注册cow的用户或输入用户名关键词进行比划。")
                return

            if not target_user_id:
                yield event.plain_result(f"{sender_nickname}，请 @ 一名已注册cow的用户或输入用户名关键词进行比划。")
                return

            if target_user_id not in group_data:
                yield event.plain_result(f"{sender_nickname}，对方还没有注册cow呢！,{target_user_id}")
                return

            # 检查 3分钟内邀请人数限制
            current_time = time.time()
            group_invite_count = self.invite_count.setdefault(group_id, {})
            last_time, count = group_invite_count.get(user_id, (0, 0))
            compare_cd = 3   # 3 分钟冷却时间
            if current_time - last_time < 3 * 60:
                if count >= 5:
                    limit_messages = [
                        f"{sender_nickname}，你的cow刚比划了好几回，这会儿累得直喘气，得缓缓啦！",
                        f"{sender_nickname}，cow经过几次比划，已经累得软绵绵的，让它歇会儿吧！",
                        f"{sender_nickname}，你的cow连续比划，现在都有点颤颤巍巍了，快让它休息下！",
                        f"{sender_nickname}，cow比划了这么多次，已经疲惫不堪，没力气再比啦，先休息会儿！"
                    ]
                    yield event.plain_result(random.choice(limit_messages))
                    return
            else:
                count = 0
            group_invite_count[user_id] = (current_time, count + 1)

            # 检查冷却
            group_compare_time = self.last_compare_time.setdefault(group_id, {})
            user_compare_time = group_compare_time.setdefault(user_id, {})
            last_compare = user_compare_time.get(target_user_id, 0)
            MIN_COMPARE_COOLDOWN = compare_cd  * 60

            if current_time - last_compare < MIN_COMPARE_COOLDOWN:
                yield event.plain_result(f"{sender_nickname}，你在 {compare_cd} 分钟内已邀请过该用户比划，稍等一下吧。")
                return

            # 统一使用data_manager获取最新数据
            user_info = group_data[user_id]
            target_info = group_data[target_user_id]
            # 更新最后发起比划时间
            user_compare_time[target_user_id] = current_time

            user_length = user_info["length"]
            target_length = target_info["length"]
            diff = user_length - target_length

            # 增加随机事件：两败俱伤，长度减半
            double_loss_probability = 0.05  # 5% 的概率两败俱伤或者双方胜利
            if self.check_probability(double_loss_probability):
                if self.check_probability(0.5):
                    user_info["length"] = max(1, user_length // 2)
                    target_info["length"] = max(1, target_length // 2)
                    self.data_manager.update_group_data(group_id, group_data)
                    yield event.plain_result(f"{sender_nickname} 和 {target_info['nickname']}，你们俩的cow刚一碰撞，就像两颗脆弱的玻璃珠，“啪嗒”一下都折断啦！双方的cow长度都减半咯！")
                    return
                else:
                    user_info["length"] = user_length * 2
                    target_info["length"] = target_length * 2
                    self.data_manager.update_group_data(group_id, group_data)
                    yield event.plain_result(
                        f"{sender_nickname} 和 {target_info['nickname']}，你们俩的cow刚一碰撞，就发生奇妙反应！双方的cow长度都加倍！")
                    return

            hardness_win_messages = [
                "{nickname}，虽然你们的cow长度相近，但你的cow如同钢铁般坚硬，碾压了对方，太厉害了！",
                "{nickname}，关键时刻，你的cow硬度爆棚，像一把利刃刺穿了对方的防线！",
                "{nickname}，长度差不多又怎样，你的cow凭借着惊人的硬度脱颖而出，霸气侧漏！"
            ]

            if abs(diff) <= 10:
                if self.check_probability(0.35):
                    config = self.get_niuniu_config()
                    min_bonus = config.get('min_bonus', 1)
                    max_bonus = config.get('max_bonus', 3)
                    bonus = random.randint(min_bonus, max_bonus)
                    user_info["length"] = max(1, user_info["length"] + bonus)
                    self._save_niuniu_lengths()
                    message = random.choice(hardness_win_messages).format(nickname=sender_nickname)
                    yield event.plain_result(self.format_niuniu_message(f"{message} 你的长度增加{bonus}cm",
                                                                        user_info["length"]))
                    return
                else:
                    yield event.plain_result(f"{sender_nickname} 和 {target_info['nickname']}，你们的cow长度差距不大，就像两位旗鼓相当的对手，继续加油哦！")
                    return

            elif diff > 10 and diff <= 30:
                if self.check_probability(0.6):
                    config = self.get_niuniu_config()
                    min_bonus = config.get('min_bonus', 1)
                    max_bonus = config.get('max_bonus', 3)
                    bonus = random.randint(min_bonus, max_bonus)
                    user_info["length"] += bonus
                    self._save_niuniu_lengths()
                    message = random.choice(hardness_win_messages).format(nickname=sender_nickname)
                    yield event.plain_result(self.format_niuniu_message(f"{message} 你的长度增加{bonus}cm",
                                                                        user_info["length"]))
                    return
                elif self.check_probability(0.1):
                    yield event.plain_result(f"{sender_nickname} 你的cow掏出来就把对方吓跑，但是你得意忘形，导致cow长度不变")
                    return

                else:
                    config = self.get_niuniu_config()
                    min_bonus = config.get('min_bonus', 1)
                    max_bonus = config.get('max_bonus', 3)
                    bonus = random.randint(min_bonus, max_bonus)
                    user_info["length"] -= bonus
                    self._save_niuniu_lengths()
                    av_name_messages =["水卜樱","樱由萝","永濑唯","樱空桃","桃乃木香奈"]
                    av_name = random.choice(av_name_messages)
                    yield event.plain_result(self.format_niuniu_message(
                        f"{sender_nickname} 你的cow气度不凡，但是你的意志不够坚定，被{av_name}诱惑，性起鹿管导致cow缩短{bonus}cm",user_info["length"]))
                    return

            elif diff > 30:
                if self.check_probability(0.05):
                    config = self.get_niuniu_config()
                    min_bonus = config.get('min_bonus', 1)
                    max_bonus = config.get('max_bonus', 3)
                    bonus = random.randint(min_bonus, max_bonus)
                    user_info["length"] += bonus
                    self._save_niuniu_lengths()
                    win_messages = [
                        "{nickname}，你的cow就像一条威风凛凛的巨龙，以绝对的长度优势把 {target_nickname} 的cow打得节节败退，太威武啦！",
                        "{nickname}，你的cow如同一个勇猛的战士，用长长的身躯轻松碾压了 {target_nickname} 的cow，厉害极了！",
                        "{nickname}，你家cow简直就是王者降临，长度上把 {target_nickname} 远远甩在身后，让对方毫无还手之力！"
                    ]
                    message = random.choice(win_messages).format(nickname=sender_nickname, target_nickname=target_info["nickname"])
                    yield event.plain_result(self.format_niuniu_message(
                        f"{message} 你的长度增加{bonus}cm",
                        user_info["length"]))
                    return
                else:
                    yield event.plain_result(
                        f"以大欺小，懦弱之举我绝不姑息！！！" )
                    return

            elif abs(diff) <= 30:
                if self.check_probability(0.7):
                    if self.check_probability(0.4):
                        config = self.get_niuniu_config()
                        min_bonus = config.get('min_bonus', 1)
                        max_bonus = config.get('max_bonus', 3)
                        bonus = random.randint(min_bonus, max_bonus)
                        target_info["length"] += bonus
                        self._save_niuniu_lengths()
                        lose_messages = [
                            "{nickname}，你的cow在长度上完全比不过 {target_nickname} 的大火腿"
                        ]
                        message = random.choice(lose_messages).format(nickname=sender_nickname,
                                                                      target_nickname=target_info["nickname"])
                        yield event.plain_result(self.format_niuniu_message(
                            f"{message} {target_info['nickname']}的长度增加{bonus}cm 你的长度不变",
                            user_info["length"]))
                        return
                    else:
                        config = self.get_niuniu_config()
                        min_bonus = config.get('min_bonus', 1)
                        max_bonus = config.get('max_bonus', 3)
                        bonus = random.randint(min_bonus, max_bonus)
                        user_info["length"] -= bonus
                        self._save_niuniu_lengths()
                        lose_messages = [
                            "{nickname}，你的cow受到过度惊吓！"
                        ]
                        message = random.choice(lose_messages).format(nickname=sender_nickname)
                        yield event.plain_result(self.format_niuniu_message(
                            f"{message} 你的长度缩短{bonus}cm",
                            user_info["length"]))
                        return

                else:
                    config = self.get_niuniu_config()
                    min_bonus = config.get('min_bonus', 1)
                    max_bonus = config.get('max_bonus', 3)
                    bonus = random.randint(min_bonus, max_bonus)
                    user_info["length"] += bonus
                    self._save_niuniu_lengths()
                    av_name_messages = ["水卜樱", "樱由萝", "永濑唯", "樱空桃", "桃乃木香奈"]
                    av_name = random.choice(av_name_messages)
                    win_messages = [
                        "{nickname}，你的cow以小胜大！",
                        "{nickname}，你厚颜无耻，播放{av_name}的成名之作，让对方迅速缴械",
                    ]
                    message = random.choice(win_messages).format(nickname=sender_nickname, av_name=av_name)
                    yield event.plain_result(self.format_niuniu_message(
                        f"{message} 你的长度增加{bonus}cm",
                        user_info["length"]))
                    return

            else:
                if self.check_probability(0.05):
                    config = self.get_niuniu_config()
                    min_bonus = config.get('min_bonus', 1)
                    max_bonus = config.get('max_bonus', 3)
                    bonus = random.randint(min_bonus, max_bonus)
                    user_info["length"] += bonus
                    self._save_niuniu_lengths()
                    lose_messages = [
                        "{nickname}，虽然你的cow就像一只小虾米，在长度上完全比不过 {target_nickname} 的大鲸鱼，但是你爆发出了异常坚定的意志，对方被你吓跑",
                        "{nickname}，虽然你的长度远远不及 {target_nickname} 的参天大树，但是对方突然阳痿"
                    ]
                    message = random.choice(lose_messages).format(nickname=sender_nickname,
                                                                  target_nickname=target_info["nickname"])
                    yield event.plain_result(self.format_niuniu_message(
                        f"{message} 你的长度增加{bonus}cm",
                        user_info["length"]))
                    return

                else:
                    lose_messages = [
                        "{nickname}，很可惜呀，这次你的cow就像一只小虾米，在长度上完全比不过 {target_nickname} 的大鲸鱼，下次加油呀！",
                        "{nickname}，{target_nickname} 的cow如同一个巨人，在长度上把你的cow秒成了渣渣，你别气馁，还有机会！",
                        "{nickname}，这一回你的cow就像一颗小豆芽，长度远远不及 {target_nickname} 的参天大树，再接再厉，争取下次赢回来！"
                    ]
                    message = random.choice(lose_messages).format(nickname=sender_nickname, target_nickname=target_info["nickname"])
                    yield event.plain_result(f"{message}")
                    return

        else:
            yield event.plain_result(f"{sender_nickname}，你还没有注册cow，请先发送“注册cow”进行注册。")

    async def niuniu_rank(self, event: AstrMessageEvent):
        """cow排行指令处理函数"""
        group_id = str(event.message_obj.group_id)
        group_data = self.data_manager.get_group_data(group_id)
        if group_data:
            sorted_niuniu = sorted(group_data.items(), key=lambda x: x[1]["length"], reverse=True)
            rank_message = "cow排行榜：\n"
            for i, (_, user_info) in enumerate(sorted_niuniu, start=1):
                nickname = user_info["nickname"]
                length = user_info["length"]
                if length >= 100:
                    length_str = f"{length / 100:.2f}m"
                else:
                    length_str = f"{length}cm"
                rank_message += f"{i}. {nickname}：{length_str}\n"
            yield event.plain_result(rank_message)
        else:
            yield event.plain_result("当前群里还没有人注册cow呢！")

    async def niuniu_menu(self, event: AstrMessageEvent):
        """cow菜单指令处理函数"""
        menu = """
cow游戏菜单：
1. 注册cow：开启你的cow之旅，随机获得初始长度的cow。
2. 打胶：通过此操作有机会让你的cow长度增加或减少，注意要等cow恢复好哦。
3. 我的cow：查看你当前cow的长度，并获得相应评价。
4. 比划比划：@ 一名已注册cow的用户，或输入用户名关键词，进行cow长度的较量。
5. cow排行：查看当前群内cow长度的排行榜。
6. 修改昵称 新昵称：更改你的显示昵称（30分钟冷却）
        """
        yield event.plain_result(menu)

    @user_cooldown(1800, "昵称修改冷却中，请30分钟后再试")
    async def change_nickname(self, event: AstrMessageEvent):
        """修改昵称处理函数"""
        user_id = str(event.get_sender_id())
        group_id = str(event.message_obj.group_id)
        sender_nickname = event.get_sender_name()

        # 解析新昵称
        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            template = self.msg_gen.get_template('nickname', 'format_error')
            yield event.plain_result(template.format(nickname=sender_nickname))
            return

        new_nickname = parts[1].strip()
        if not (1 <= len(new_nickname) <= 20):
            yield event.plain_result("昵称长度需在1-20个字符之间")
            return

        group_data = self.data_manager.get_group_data(group_id)
        # 检查昵称唯一性
        if any(info["nickname"] == new_nickname for uid, info in group_data.items() if uid != user_id):
            yield event.plain_result(f"昵称 {new_nickname} 已被使用，请换一个")
            return

        if user_id not in group_data:
            yield event.plain_result(f"{sender_nickname}，请先注册cow再修改昵称")
            return

        # 更新昵称
        group_data[user_id]["nickname"] = new_nickname
        self.data_manager.update_group_data(group_id, group_data)

        template = self.msg_gen.get_template('nickname', 'success')
        yield event.plain_result(template.format(
            nickname=sender_nickname,
            new_nickname=new_nickname
        ))
