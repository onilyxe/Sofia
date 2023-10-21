# Sofia for Telegram
Entertainment bot

[Try the my bot](https://t.me/sofiarolbot)

Installation
------------
```shell
# Clone the repository
$ git clone https://github.com/onilyxe/Sofia.git

# Change the working directory to Sofia
$ cd Sofia
```

Configuring
------------
**Open the `config.json` configuration file in a text editor and change the values to your own:**
```ini
[TOKEN]
SOFIA = 0000000000:0000000000000000000000000000000000
TEST = 0000000000:0000000000000000000000000000000000

[ID]
ADMIN = 000000000

[ALIASES]
chatname1= -1000000000000
chatname1 = -1000000000001

[SETTINGS]
DELETE = 3600
```
* `TOKEN` is token for your Telegram bot. You can get it here: [BotFather](https://t.me/BotFather)
* `ADMIN` is your ID
* `ALIASES` Aliases for the chat ID so you don't have to type it in
* `DELETE` Auto-delete message timer in seconds

Running
------------
Using Python
```shell
# Install requirements
$ python3 -m pip install -r requirements.txt

# Run script
$ python3 sofia.py
```