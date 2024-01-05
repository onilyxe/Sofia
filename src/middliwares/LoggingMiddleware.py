import logging
from typing import Dict, Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram import types


# Логування кожного повідомлення
class LoggingMiddleware(BaseMiddleware):
    CONTENT_TYPES = {
        "text": lambda m: m.text,
        "sticker": lambda m: f"sticker, f_id={m.sticker.file_id}",
        "audio": lambda m: f"audio, f_id={m.audio.file_id}",
        "photo": lambda m: f"photo, f_id={m.photo.file_id}",
        "video": lambda m: f"video, f_id={m.video.file_id}"}

    async def __call__(self, handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], event: types.Message,
                       data: Dict[str, Any]
                       ):
        user = getattr(event.from_user, "username", None) or getattr(event.from_user, "first_name", "Unknown")
        chat = getattr(event.chat, "title", None) or f"ID {event.chat.id}"
        content_type = next((self.CONTENT_TYPES[event_type](event) for event_type in self.CONTENT_TYPES if
                             getattr(event, event_type, None)), "other_content")
        logging.info(f"{chat=}: {user=} - {content_type}")
        return await handler(event, data)
