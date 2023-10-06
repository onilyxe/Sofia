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
{
    "TOKEN": "0000000000:0000000000000000000000000000000000",
    "ADMIN_ID": 000000000
}
```
* `TOKEN` is token for your Telegram bot. You can get it here: [BotFather](https://t.me/BotFather)
* `ADMIN_ID` is your ID

Running
------------
Using Python
```shell
# Install requirements
$ python3 -m pip install -r requirements.txt

# Run script
$ python3 sofia.py
```