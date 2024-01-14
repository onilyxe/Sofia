from typing import Any

from aiogram.enums import ParseMode as PMode
from aiogram.utils.formatting import Text


class TextBuilder:
    def __init__(self, text: str = None, **kwargs: Text|Any):
        self.text = text or ""
        self.kwargs = kwargs

    def add(self, text: str = None, **kwargs: Text|Any):
        self.text += text
        self.kwargs.update(kwargs)

    def render(self, parse_mode: PMode):
        if not self.text:
            return self.text
        items = {
            k: (v.as_markdown() if parse_mode in (PMode.MARKDOWN_V2, PMode.MARKDOWN) else v.as_html())
            if isinstance(v, Text) else v for k, v in self.kwargs.items()
        }
        return self.text.format(**items)
