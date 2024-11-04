import configparser
import logging


class SingletonMeta(type):
    """Використання патерну Singleton для конфігураційного файлу"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Перевіряє чи існує вже екземпляр класу, якщо так, то повертає його, якщо ні, то створює новий
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    def __init__(self):
        self.__ok = False

        try:
            self._config = configparser.ConfigParser()
            if not self._config.read("config.ini"):
                raise FileNotFoundError("Файл конфігурацій не знайдено")

            self.TOKEN = self._config.get("TOKEN", "BOT")
            self.SKIPUPDATES = self._config.getboolean("SETTINGS", "SKIPUPDATES")
            self.ADMIN = [int(u_id.strip()) for u_id in self._config.get("ID", "ADMIN").split(",")]
            self.SUPPORT = [int(u_id.strip()) for u_id in self._config.get("ID", "SUPPORT").split(",")]
            self.TEST = self._config.getboolean("SETTINGS", "TEST")
            self.DBFILE = self._config.get("SETTINGS", "DBFILE")
            self.VERSION = self._config.get("SETTINGS", "VERSION")
            self.DELETE = self._config.getint("SETTINGS", "DELETE")
            self.BAN = self._config.getint("SPAM", "BAN")
            self.SPEED = self._config.getint("SPAM", "SPEED")
            self.MESSAGES = self._config.getint("SPAM", "MESSAGES")
            self.RANDOMGAMES = self._config.getfloat("SETTINGS", "RANDOMGAMES")
            self.ALIASES = {k: int(v) for k, v in self._config["ALIASES"].items()}
            self.DONATE = self._config.get("SETTINGS", "DONATE")

        except configparser.NoSectionError as e:
            logging.error(
                f'Помилка завантаження конфігураційного файлу в sofia.py: Секцію "{e.section.upper()}" не знайдено'
            )

        except configparser.NoOptionError as e:
            logging.error(
                f'Помилка завантаження конфігураційного файлу в sofia.py: Опцію "{e.option.upper()}" не знайдено'
            )

        except KeyError as e:
            logging.error(
                f'Помилка завантаження конфігураційного файлу в sofia.py: Опцію "{e}" не знайдено'
            )

        except FileNotFoundError as e:
            logging.error(
                f"Помилка завантаження конфігураційного файлу в sofia.py: {e}"
            )

        else:
            self.__ok = True

        finally:
            if not self.__ok:
                exit()


config = Config()
