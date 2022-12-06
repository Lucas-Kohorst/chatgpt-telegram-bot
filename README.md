# chatgpt-telegram-bot

This is a Telegram bot that lets you chat with the [chatGPT](https://github.com/openai/gpt-3) over telegram. You can deploy and run the bot locally or via docker on a remote server. Prior implementations required running locally, in order to have the bot continuously online it is now able to be run anywhere.

## Features
You can view all features by sending `/help` to the bot
- `/ask`, ask chatGPT anything receive a response
- `/draw`, draw pictures using stablediffusion
- `/browse`, give chatGPT access to Google
- `/reload`, force reload your session

## Install
### Locally
Install miniconda and setup your environment
```
# install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh

# setup environment
conda env create -f environment.yml
playwright install 
playwright install-deps
```

### Docker 
Build and run your Dockerfile
```
docker build . --tag chatgpt-telegram-bot
```

## Telegram Bot Setup
Copy `.env.example` and fill it in with the relevant API keys
```
cp .env.example .env
```

The `.env` file is layed out with the following keys
```
TELEGRAM_API_KEY=# (required) used to identify and control your bot
#TELEGRAM_USER_ID=# (optional) used to authenticate access to your bot to just a given account

OPENAI_EMAIL=# (required) email to access the openai account that is being used for chatgpt
OPENAI_PASSWORD=#(required) password to access the openai account that is being used for chatgpt

STABILITY_API_KEY=# (required) API key for stablediffusion to generate drawings
SERP_API_KEY=# (required) API key for google searches
```

You can obtain the required API Keys below
- [Telegram](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)
- [Dream Studio StableDiffusion](https://beta.dreamstudio.ai/membership?tab=home)
- [SERP API Google Searches](https://serpapi.com/)

## Running 
### Locally 
```
# if your environment is installed correct
python server.py
```

### Systemd
```
# if your environment is installed correct
mv telegram.service /etc/systemd/system/telegram.service
systemctl enable /etc/systemd/system/telegram.service
systemctl start telegram.service
```

### Docker
```
docker run -d --name chatgpt-telegram-bot chatgpt-telegram-bot
```

You will also need to go the bot that you created via `@Botfather`, start a chat with it, and click start. 

## Credits
- Original Creator [@Altryne](https://twitter.com/altryne/status/1598902799625961472) on Twitter
- Based on [Daniel Gross's whatsapp gpt](https://github.com/danielgross/whatsapp-gpt) package.