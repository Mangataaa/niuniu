import time
from typing import Callable, Any
from functools import wraps


class CoolDownManager:
    """cow操作冷却时间管理"""

    def __init__(self):
        self._records = {}

    def check_cooldown(self, group_id: str, user_id: str, key: str, cooldown: int) -> bool:
        """检查冷却时间"""
        group_ = self._records.setdefault(group_id, {})
        user_ = group_.setdefault(user_id, {})
        last_time = user_.get(key, 0)
        return time.time() - last_time >= cooldown * 60

    def update_cooldown(self, group_id: str, user_id: str, key: str):
        """更新冷却时间记录"""
        self._records[group_id][user_id][key] = time.time()


def group_cooldown(cooldown: int, message: str):
    """群组冷却时间装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, event: Any, *args, **kwargs):
            group_id = str(event.message_obj.group_id)
            manager = self.cool_down_manager

            if not manager.check_cooldown(group_id, cooldown):
                yield event.plain_result(message)
                return

            manager.update_cooldown(group_id)
            async for result in func(self, event, *args, **kwargs):
                yield result

        return wrapper

    return decorator


def user_cooldown(cooldown: int, type: str, message: str):
    """用户冷却时间装饰器, 传入cooldown冷去时间，按分钟计算，以及类型"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, event: Any, *args, **kwargs):
            user_id = str(event.get_sender_id())
            sender_nickname = event.get_sender_name()
            group_id = str(event.message_obj.group_id)
            key = f"{group_id}_{user_id}_{func.__name__}"
            manager = self.cool_down_manager
            template = self.message_gen.get_template(type, message)

            if not manager.check_cooldown(group_id, user_id, key, cooldown):
                yield event.plain_result(template.format(
                    nickname=sender_nickname
                ))
                return

            manager.update_cooldown(key)
            async for result in func(self, event, *args, **kwargs):
                yield result

        return wrapper

    return decorator
