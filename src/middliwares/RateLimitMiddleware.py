import time

from aiogram import BaseMiddleware
from aiogram.types import Message, FSInputFile

from src.utils import reply_voice_and_delete


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, speed: float, messages: int, ban: float):
        self.speed = speed
        self.messages_limit = messages
        self.ban_time = ban
        self.users_message_data = {}
        self.banned_users = {}
        super().__init__()

    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        current_time = time.time()

        if user_id in self.banned_users:
            ban_end_time = self.banned_users[user_id]
            if current_time < ban_end_time:
                return
            else:
                del self.banned_users[user_id]

        if user_id not in self.users_message_data:
            self.users_message_data[user_id] = []

        # Видаляємо повідомлення, що старші за SPEED
        self.users_message_data[user_id] = [
            timestamp for timestamp in self.users_message_data[user_id]
            if current_time - timestamp <= self.speed
        ]

        self.users_message_data[user_id].append(current_time)

        # Якщо кількість повідомлень перевищила ліміт, блокуємо користувача
        if len(self.users_message_data[user_id]) > self.messages_limit:
            self.banned_users[user_id] = current_time + self.ban_time
            file = FSInputFile("src/spam.ogg")
            await reply_voice_and_delete(event, file)
            return

        return await handler(event, data)
