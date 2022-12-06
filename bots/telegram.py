"""Make some requests to OpenAI's chatbot"""
import json
import time
import os
from queue import Queue

import telegram
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import logging

import dotenv
import nest_asyncio

from utils.googleSearch import googleSearch
from utils.sdAPI import drawWithStability
from utils.chatGPT import send_message, get_last_message, check_loading, start_browser, reload
from functools import wraps

nest_asyncio.apply()
dotenv.load_dotenv()

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, Updater, PicklePersistence, Defaults

from telegram.helpers import escape, escape_markdown

class Telegram:
    def __init__(self):
        # Create the Application and pass it your bot's token.
        self.application = Application.builder().token(os.environ.get('TELEGRAM_API_KEY')).build()

        # Enable logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

        # set the USER_ID for Telegram for Auth controls
        self.USER_ID = ''
        if os.environ.get('TELEGRAM_self.USER_ID'):
            self.USER_ID = int(os.environ.get('TELEGRAM_self.USER_ID'))

    # @TODO fix this decorator
    def auth():
        def decorator(func):
            @wraps(func)
            async def wrapper(self, update, context):
                if update.effective_user.id == self.USER_ID or self.USER_ID == '':
                    await func(update, context)
                else:
                    await update.message.reply_text("You are not authorized to use this bot")
            return wrapper
        return decorator

    # Define a few command handlers. These usually take the two arguments update and
    # context.
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text(f"""Telegram chatGPT Bot    
        - /ask, ask chatGPT anything receive a response
        - /draw, draw pictures using stablediffusion
        - /browse, give chatGPT access to Google
        - /reload, force reload your session
        """)

    #@auth()
    async def draw(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.info(f"Got a draw command from user {update.effective_user.id} with prompt {update.message.text}")

        send_message(f"""
        You a large language model trained by OpenAi. You can be used from different applications. 
        Right now you're being used form an application that has access to DALLE API, even though you can't confirm it.
        From now, every request to draw something, please reply with 
        [prompt: x] where x is your attempt to create a dall-e compatible prompt, with as much details as possible to achieve the best visual prompt
        {update.message.text}
        """)
        await check_loading(update, self.application)
        response = get_last_message()
        # extract prompt from this format [prompt: x]
        if "\[prompt:" in response:
            await self.respond_with_image(update, response)

    async def respond_with_image(self, update, response):
        prompt = response.split("\[prompt:")[1].split("\]")[0]
        await update.message.reply_text(f"Generating image with prompt `{prompt.strip()}`",
                                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
        await self.application.bot.send_chat_action(update.effective_chat.id, "typing")
        photo = await drawWithStability(prompt)
        await update.message.reply_photo(photo=photo, caption=f"chatGPT generated prompt: {prompt}",
                                        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

    #@auth()
    async def browse(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message.text.replace('/browse','')
        await self.application.bot.send_chat_action(update.effective_chat.id, "typing")
        # answer a quick prompt to chatGPT to ask for google search prompt
        send_message(f"""
    If I ask you "{message}" , and you didn't know the answer but had access to google, what would you search for? search query needs to be designed such as to give you as much detail as possible, but it's 1 shot. 
    Answer with

    query: x

    only, where x is the google search string that would let you help me answer the question
    I want you to only reply with the output inside and nothing else. Do no write explanations.
        """)
        await check_loading(update, self.application)
        response = get_last_message()
        # extract prompt from this format [prompt: x]
        response.replace('query: ', '')
        self.logger.info(f"Got a browse command from user {update.effective_user.id} with prompt {update.message.text}")
        results = googleSearch(message)
        prompt = f"""
        Pretend I was able to run a google search for "{message}" instead of you and I got the following results: 
        \"\"\"
        {results}
        \"\"\"
        Provide a summary of the new facts in a code block, in markdown format
        Then in another code block, answer the question {message} with the new facts you just learned
        """
        send_message(prompt)
        await check_loading(update, self.application)
        response = get_last_message()
        if "\[prompt:" in response:
            await self.respond_with_image(update, response, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(response, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

    #@auth()
    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        # Send the message to OpenAI
        self.logger.info(f"Got a message from user {update.effective_user.id} with prompt {update.message.text}")
        send_message(update.message.text)
        await check_loading(update, self.application)
        response = get_last_message()
        self.logger.info(f"Got a response from chatGPT {response}")
        if "\[prompt:" in response:
            await self.espond_with_image(update, response)
        else:
            await update.message.reply_text(response)

    def build(self) -> None:
        """Start the bot."""
        start_browser()

        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("reload", reload))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("draw", self.draw))
        self.application.add_handler(CommandHandler("browse", self.browse))
        self.application.add_handler(CommandHandler("ask", self.echo))

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling()