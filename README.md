# Sofia for Telegram
Розважальний бот

[Спробуй мого бота](https://t.me/sofiarolbot)

Встановлення
------------
```shell
# Клонуй репозиторій
$ git clone https://github.com/onilyxe/Sofia.git

# Змініть робочу директорію на Sofia
$ cd Sofia
```

Налаштування
------------
**Відкрийте файл конфігурації `config.ini` у текстовому редакторі та змініть значення на свої:**.
```ini
[TOKEN]
BOT = 0000000000:0000000000000000000000000000000000

[ID]
ADMIN = 000000000
CHANNEL = -1000000000000
SUPPORT = 000000000, 000000001

[ALIASES]
chatname = -1000000000000
chatnametwo = -1000000000001

[SPAM]
BAN = 10
SPEED = 5
MESSAGES = 4

[SETTINGS]; True/False
SKIPUPDATES = False
TEST = False
STATUS = False
DELETE = 3600
RANDOMGAMES = 0.35
VERSION = v2
```
* `TOKEN` це токен для вашого Telegram-бота. Отримати його можна тут: [BotFather](https://t.me/BotFather)
* `ADMIN` це твій ID, для адмін команд
* `CHANNEL` ID каналу куди бот надсилає повідомлення про запуск/зупинку
* `SUPPORT` ID юзерів, для доступу до команди /add
* `ALIASES` Псевдоніми для ID чату, щоб не вводити його вручну
* `BAN` Захист від спаму. Час муту у хвилинах за флуд
* `SPEED` Час у секундах, за який потрібно надіслати повідомлення для отримання муту
* `MESSAGES` Кількість повідомлень для отримання муту

* `SKIPUPDATES` Пропускає нові повідомлення. True або False
* `TEST` Пропускає кулдауни. True або False
* `STATUS` Надсилає повідомлення про запуск/зупинку. True або False
* `DELETE` Таймер автоматичного видалення повідомлень у секундах
* `RANDOMGAMES` Шанс виграшу в /game. 1 - завжди вигравати. 0 - ніколи. 0.5 - шанс 50/50
* `VERSION` Версія

Запуск
------------
Використовуй Python
```shell
# Встанови залежності
$ python3 -m pip install -r requirements.txt

# Запустити бота
$ python3 sofia.py
```