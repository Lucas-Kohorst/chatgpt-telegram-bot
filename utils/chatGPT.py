"""Make some requests to OpenAI's chatbot"""
import json
import time
import os

from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import logging

import dotenv
import nest_asyncio

from functools import wraps

from telegram.helpers import escape, escape_markdown
from telegram import Update
from telegram.ext import ContextTypes

nest_asyncio.apply()
dotenv.load_dotenv()

OPENAI_EMAIL = ''
if os.environ.get('OPENAI_EMAIL'):
    OPENAI_EMAIL = os.environ.get('OPENAI_EMAIL')

OPENAI_PASSWORD = ''
if os.environ.get('OPENAI_PASSWORD'):
    OPENAI_PASSWORD = os.environ.get('OPENAI_PASSWORD')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# check if /tmp/playwright exists prior to running  
prompt_bypass = False
if not os.path.exists('/tmp/playwright'):
    prompt_bypass = True

# TODO: create a new headless browser for each unique session of the bot
# see comment in the `telegram.py` file
PLAY = sync_playwright().start()
BROWSER = PLAY.chromium.launch_persistent_context(
    user_data_dir="/tmp/playwright",
    headless=False,
)
PAGE = BROWSER.new_page()

def get_input_box():
    """Get the child textarea of `PromptTextarea__TextareaWrapper`"""
    textarea = PAGE.query_selector(r'//*[@id="__next"]/div/div[1]/main/div[2]/form/div/div[2]/textarea')
    return textarea

def is_logged_in():
    # See if we have a textarea with data-id="root"
    return get_input_box() is not None

def send_message(message):
    # Send the message
    box = get_input_box()
    box.click()
    box.fill(message)
    box.press("Enter")
    logger.info("Sent message: " + message)

class AtrributeError:
    pass

#@auth()
async def reload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info(f"Got a reload command from user {update.effective_user.id}")
    PAGE.reload()
    await update.message.reply_text("Reloaded the browser!")

def get_last_message():
    """Get the latest message"""
    page_elements = PAGE.query_selector_all("div[class*='request-']")
    last_element = page_elements[-1]
    prose = last_element
    try:
        code_blocks = prose.query_selector_all("pre")
    except Exception as e:
        response = 'Server probably disconnected, try running /reload'
        return response
    if len(code_blocks) > 0:
        # get all children of prose and add them one by one to respons
        response = ""
        for child in prose.query_selector_all('p,pre'):
            if str(child.get_property('tagName')) == "PRE":
                code_container = child.query_selector("code")
                response += f"\n```\n{escape_markdown(code_container.inner_text(), version=2)}\n```"
            else:
                #replace all <code>x</code> things with `x`
                text = child.inner_html()
                response += escape_markdown(text, version=2)
        response = response.replace("<code\>", "`")
        response = response.replace("</code\>", "`")
    else:
        response = escape_markdown(prose.inner_text(), version=2)
    
    logger.info('Received Response\n ' + response)
    return response

async def check_loading(update, application):
    #button has an svg of submit, if it's not there, it's likely that the three dots are showing an animation
    submit_button = PAGE.query_selector_all("textarea+button")[0]
    # with a timeout of 90 seconds, created a while loop that checks if loading is done
    loading = submit_button.query_selector_all(".text-2xl")
    #keep checking len(loading) until it's empty or 45 seconds have passed
    await application.bot.send_chat_action(update.effective_chat.id, "typing")
    start_time = time.time()
    while len(loading) > 0:
        if time.time() - start_time > 90:
            break
        time.sleep(0.5)
        loading = submit_button.query_selector_all(".text-2xl")
        await application.bot.send_chat_action(update.effective_chat.id, "typing")

def start_browser():
    PAGE.goto("https://chat.openai.com/")
    if not is_logged_in():
        logger.info("Logging into ChatGPT")
        PAGE.goto('https://chat.openai.com/auth/login')
        PAGE.locator('button:has-text(\"Log in\")').click()
        PAGE.get_by_label("Email address").fill(OPENAI_EMAIL)
        PAGE.locator('button[name=\"action\"]').click()
        PAGE.get_by_label("Password").fill(OPENAI_PASSWORD)
        PAGE.locator('button[name=\"action\"]').click()

        # check if /tmp/playwright is empty
        if prompt_bypass:
            PAGE.locator('button:has-text(\"Next\")').click()
            PAGE.locator('button:has-text(\"Next\")').click()
            PAGE.locator('button:has-text(\"Done\")').click()
            logger.info("Passed intro messages on first start")
        
        logger.info("ChatGPT Logged in and Ready for Queries")
    else:
        logger.info("ChatGPT Ready for Queries")
