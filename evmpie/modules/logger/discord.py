from multiprocessing.dummy import Process
import discord
import coloredlogs, logging
from multiprocessing import Process
from discord_webhook import DiscordWebhook
import requests


class DiscordBot(discord.Client):
    def __init__(self, discord_token, discord_webhook_url):
        super().__init__(intents=discord.Intents.all())
        self.logger = logging.getLogger("discord_bot")
        coloredlogs.install(logger=self.logger)

        self.__discord_token = discord_token
        self.__discord_webhook_url = discord_webhook_url
        self.__webhook = DiscordWebhook(url=self.__discord_webhook_url)
        self.__bot_process = None

    def __del__(self):
        if self.__bot_process is not None:
            self.__bot_process.join()

    async def on_ready(self):
        self.logger.info("Discord Client successfully connected.")

    async def on_message(self, message):
        if message.author == self.user:
            return

        # if message.content == "!help":
        #     msg = (
        #         "Asked for help?\n"
        #         "------------------------------------------------------\n"
        #         "**!spot-holdings** -> returns wallet current holdings\n"
        #         "------------------------------------------------------\n"
        #         "**!dca-orderbook** -> returns current dca running orders\n"
        #         "------------------------------------------------------\n"
        #         "**!running-time** -> returns how long the bot has been running\n"
        #         "------------------------------------------------------\n"
        #         "**!pnl** -> returns the unrealized cumulative PNL\n"
        #         "------------------------------------------------------\n"
        #         "**!day-pnl** -> returns the unrealized PNL of the day\n"
        #         "------------------------------------------------------\n"
        #         "**!realized-pnl** -> returns the realized cumulative PNL\n"
        #         "------------------------------------------------------\n"
        #         "**!realized-day-pnl** -> returns the realized PNL of the day\n"
        #         "------------------------------------------------------\n"
        #         "**!open-order** -> SIKE!\n"
        #         "------------------------------------------------------\n"
        #     )
        #     await message.channel.send(msg)

        # elif message.content == "!random":
        #     await message.channel.send(
        #         "\u001b[0;40m\u001b[1;32mThat's some cool formatted text right?"
        #     )

        # elif message.content == "!spot-holdings":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!dca-orderbook":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!running-time":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!pnl":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!day-pnl":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!realized-pnl":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!realized-day-pnl":
        #     await message.channel.send("I can't do that yet!")

        # elif message.content == "!open-order":
        #     await message.channel.send("SIKE! Fuck outta here.")

    def send_message(self, msg):
        self.__webhook.content = msg
        response = self.__webhook.execute()
        if response.status_code != requests.codes.ok:
            return False
        return True

    def run_bot(self):
        self.__bot_process = Process(target=self.run, args=(self.__discord_token,))
        self.__bot_process.start()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from time import sleep

    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    webhook = os.getenv("DISCORD_UPDATES_WEBHOOK")

    bot = DiscordBot(token, webhook)

    bot.run_bot()

    bot.send_message("Hello World")
