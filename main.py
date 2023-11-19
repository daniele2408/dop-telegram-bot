#!/usr/bin/env python
# pylint: disable=unused-argument

import logging
import traceback
from typing import List, Set
import configparser

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from logic.callers import generate_lemma, generate_lemma_multi
from logic.exceptions import RetrieveException, NoResultException
from model.records import Lemma

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Ciao {user.mention_html()}! Sono un bot Telegram costruito per aiutarti nella consultazione del Dizionario italiano multimediale e multilingue d’ortografia e di pronunzia.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Inviami una parola per ottenere il link alla voce del DOP, con pronuncia in forma scritta e audio.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""

    word = update.message.text

    if len(word.split(" ")) != 1:
        await update.message.reply_text("Inserire un'unica parola, senza spazi.")
    else:
        try:
            # lemma: Lemma = generate_lemma(word)
            lemmas: Set[Lemma] = generate_lemma_multi(word)
            if len(lemmas) > 1:
                await update.message.reply_text(f"Ho trovato {len(lemmas)} risultati:")
            for lemma in lemmas:
                await update.message.reply_text(lemma.info())

                if lemma.is_there_audio():
                    with open(lemma.download_audio(), 'rb') as audio:
                        await context.bot.send_audio(chat_id=context._chat_id, audio=audio, title=lemma.lemma_decoded)
                else:
                    await update.message.reply_text("Non sono riuscito a trovare un file audio per questa parola.")
        except NoResultException as nre:
            await update.message.reply_text(str(nre))
        except RetrieveException as ret_exc:
            traceback.print_exc()
            await update.message.reply_text(f"Ho riscontrato un errore nella ricerca della parola immessa, riprovare più tardi oppure controllare che la parola sia stata digitata correttamente.")


def main() -> None:

    config = configparser.ConfigParser()
    config.read('./resources/config.ini')
    application = Application.builder().token(config.get('BOT_SETTINGS', 'TOKEN')).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e. message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
