import re
import random
from typing import Any

from aiogram.enums import ParseMode as PMode
from aiogram.utils.formatting import Text


class TextBuilder:
    def __init__(self, text: str = None, **kwargs: Text|Any):
        self.kwargs = self._str_to_text_obj(kwargs)
        self._temp_substrings = {}
        self.text = self._wrap_string(text) if text else ""

    @staticmethod
    def _str_to_text_obj(kwargs: dict):
        for k, v in kwargs.items():
            if isinstance(v, str):
                kwargs[k] = Text(v)
        return kwargs

    def _wrap_string(self, text: str):
        a = re.findall(r"(\{.*?})", text)
        for i in set(a):
            t_string = f"sub{random.randint(1, 100 ** 10)}string"
            self._temp_substrings[t_string] = i
            text = text.replace(i, t_string)
        return text

    def _unwrap_string(self, text: str, items: dict = None):
        items = items or self.kwargs
        for k, w in self._temp_substrings.items():
            text = text.replace(k, w)
        return text.format(**items)

    def add(self, text: str = None, new_line: bool = False, **kwargs: Text|Any):
        text = self._wrap_string(text)
        self.text += "\n" + text if new_line else text
        self.kwargs.update(self._str_to_text_obj(kwargs))

    def render(self, parse_mode: PMode):
        if not self.text:
            return self.text
        is_md = parse_mode in (PMode.MARKDOWN_V2, PMode.MARKDOWN)
        items = {
            k: (v.as_markdown() if is_md else v.as_html())
            if isinstance(v, Text) else v for k, v in self.kwargs.items()
        }
        text = Text(self.text)
        text = text.as_markdown() if is_md else text.as_html()
        return self._unwrap_string(text, items)
