# Sofia for Telegram
Розважальний бот

[Спробуй мого бота](https://t.me/sofiarolbot)

Встановлення
------------
```shell
# Клонуй репозиторій
$ git clone https://github.com/onilyxe/sofia.git

# Змініть робочу директорію на sofia
$ cd sofia
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
SUPPORT = 000000000, 000000000, 000000000

[ALIASES]
chatname = -1000000000000

[SPAM]
BAN = 10
SPEED = 5
MESSAGES = 4

[SETTINGS]; True/False
; Пропускає нові повідомлення
SKIPUPDATES = False

; Пропускає кулдауни
TEST = False

; Файл бази даних
DBFILE = src/database.db

; Надсилає повідомлення про старт/стоп
STATUS = True

; Таймер видалення повідомлень у секундах
DELETE = 120

; Шанс виграшу в /game
RANDOMGAMES = 0.45

; Версія
VERSION = v3_final

; Посилання на картку
DONATE = https://send.monobank.ua/0000000000
```
* `TOKEN` це токен для вашого Telegram-бота. Отримати його можна тут: [BotFather](https://t.me/BotFather)
* `ADMIN` це твій ID, для адмін команд
* `CHANNEL` ID каналу куди бот надсилає повідомлення про запуск/зупинку
* `SUPPORT` ID юзерів, для доступу до команди /add
* `ALIASES` Псевдоніми для ID чату, щоб не вводити його вручну
* `BAN` Захист від спаму. Час муту у хвилинах за флуд
* `SPEED` Час у секундах, за який потрібно надіслати повідомлення для отримання муту
* `MESSAGES` Кількість повідомлень для отримання муту

Запуск
------------
Використовуй Python
```shell
# Встанови залежності
$ python3 -m pip install -r requirements.txt

# Запустити бота
$ python3 sofia.py
```
