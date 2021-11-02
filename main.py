#!/usr/bin/python

import discord
from discord.ext import commands
import logging

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import random
import pymysql
import re
import string
import sys

# Bot Config
import bot_config

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='.', description='''Backers Verification Bot''', intents=intents)


def main():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s: %(levelname)s: %(message)s',
                        datefmt='%Y/%m/%d-%H:%M:%S')

    bot.remove_command('help')
    bot.run(bot_config.discord_token)

def sendEmail(toAddr, verifyCode):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Mythic Table Kickstarter Discord Verification Code"
    message["From"] = bot_config.smtp_user
    message["To"] = toAddr

    message.attach(
        MIMEText(
            "Hello Backer!"
            "This is a confirmation email to verify you as one of our "
            "backers. In order to confirm you as a backer, please go to Discord "
            "and send the following message to BackersBot:"
            ".backer_verify {0} {1}".format(toAddr, verifyCode),
            "plain"
        )
    )

    message.attach(
        MIMEText(
            "Hello Backer! <br/><br/>"
            "This is a confirmation email to verify you as one of our "
            "backers. In order to confirm you as a backer, please go to Discord "
            "and send the following message to BackersBot: <br/><br/>"
            ".backer_verify {0} {1}".format(toAddr, verifyCode),
            "html"
        ),
    )

    ssl_context = ssl.create_default_context()

    with smtplib.SMTP_SSL(bot_config.smtp_host, bot_config.smtp_port, context=ssl_context) as server:
        server.login(bot_config.smtp_user, bot_config.smtp_passwd)
        server.sendmail(
            bot_config.smtp_user, toAddr, message.as_string()
        )

@bot.event
async def on_ready():
    logging.info("Logged in as {0}-{1}".format(bot.user.name, bot.user.id))

    if bot_config.is_test:
        await bot.change_presence(status=discord.Status.invisible)


# region Backer Roles
@bot.command(pass_context=True)
async def backer_help(ctx: commands.Context):
    log_command(ctx.author, "backer_help")

    msg = "This bot will help you identify yourself as a backer and obtain access to Discord's private channels.\r\r" \
          "In order to start the process, you'll need to know the email you've used to back our project. That would be " \
          "your Kickstarter email, PayPal email or your Facebook email if you have your Kickstarter and Facebook " \
          "accounts linked.\r\r" \
          "Send me the following command: \r\r" \
          ".backer_mail email@example.com"

    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(msg)
    else:
        try:
            await ctx.author.send(msg)
        except discord.errors.Forbidden:
            await ctx.send("{0} you have disabled direct messages "
                                                        "from this server members. "
                                                        "Please, allow them temporarily so we can start the process."
                                   .format(ctx.message.author.mention))


@bot.command(pass_context=True)
async def backer_mail(ctx: commands.Context, email: str):
    log_command(ctx.author, "backer_mail", email)

    # Only works if we're on a private message
    if isinstance(ctx.channel, discord.DMChannel):
        # Check if email is valid
        if valid_email(email):
            # Check the Database and see if we have the email.
            # Also check it we already sent a verification code and send the same one
            mariadb = db_connect()

            try:
                with mariadb.cursor() as cursor:
                    cursor.execute("SELECT `verification_code` FROM `backers` WHERE `email`=%s", email)
                    result = cursor.fetchone()

                    token = None

                    if result is None:
                        # User doesn't exists in the database. Throw an error.
                        await ctx.send("The email address is not registered as a valid backer. "
                                      "Please, make sure you've entered the right email.\r\r")
                    elif result["verification_code"] is None:
                        # User hasn't started the verified proccess previously. Generate a new verifiy token.
                        token = generate_random_string(40)

                        # Save the token on the database.
                        cursor.execute("UPDATE `backers` SET `verification_code`=%s"
                                       " WHERE `email`=%s", (token, email))
                        mariadb.commit()
                    else:
                        # Get previous token and reuse it.
                        token = result["verification_code"]

                    if token is not None:
                        # Send an email with the token and say the instructions to verify it.
                        sendEmail(email, token)

                        await ctx.send("Welcome backer! Just one more step to access the backer-exclusive channels. "
                                      "Please, check your email for the verification code we just sent you (please "
                                      "check your spam folder too just in case) and send "
                                      "me back the following command:\r\r"
                                      ".backer_verify {0} verification_code_here"
                                      .format(email))
            finally:
                cursor.close()
                mariadb.close()
        else:
            await ctx.send("The email address looks like it's invalid. "
                          "Please, make sure you enter a valid email address.")
    else:
        await ctx.message.delete()
        await ctx.send("{0} That command only works on private message. "
                        "Please DM the command to me.".format(ctx.author.mention))


@bot.command(pass_context=True)
async def backer_verify(ctx, email: str, token: str):
    log_command(ctx.message.author, "backer_verify", email, token)

    # Only works if we're on a private message
    if ctx.message.channel.is_private:
        # Connect to the database and check if the email-token is correct
        mariadb = db_connect()

        try:
            with mariadb.cursor() as cursor:
                cursor.execute("SELECT `discord_user_id`, `role_id` FROM `backers` WHERE `email`=%s"
                               " AND `verification_code`=%s",
                               (email, token))
                result = cursor.fetchone()

                if result is None:
                    # User doesn't exists in the database. Throw an error.
                    await bot.say("The combination of user and verification code doesn't exist. "
                                  "Please, make sure you've entered the right email and code.\r\r")
                elif result["discord_user_id"] == ctx.message.author.id:
                    # The user is already registered
                    server = bot.get_server(id=bot_config.server_id)
                    server_member = discord.utils.get(server.members, id=ctx.message.author.id)
                    if server_member is not None:
                        server_role = discord.utils.get(server.roles, id=result["role_id"])
                        await bot.add_roles(server_member, server_role)

                    await bot.say("You've already been confirmed as a backer.")
                elif result["discord_user_id"] is not None:
                    # Someone already registered this email.
                    await bot.say("It looks like this email has already been registered by another user.")
                else:
                    # Check if the user has joined server
                    server = bot.get_server(id=bot_config.server_id)
                    server_member = discord.utils.get(server.members, id=ctx.message.author.id)
                    if server_member is not None:
                        # Update the database to register this user as taken
                        cursor.execute("UPDATE `backers` SET `discord_user_id`=%s"
                                       " WHERE `email`=%s AND `verification_code`=%s",
                                       (ctx.message.author.id, email, token))
                        mariadb.commit()

                        server_role = discord.utils.get(server.roles, id=result["role_id"])

                        await bot.add_roles(server_member, server_role)
                        await bot.say(
                            "Congratulations! You just completed the process and you've been confirmed as "
                            "a **{0}** tier backer. Now you have access to the private channels."
                            .format(server_role.name))
                    else:
                        await bot.say(
                            "You haven't joined our Discord server! You should join it first and then come "
                            "back and run the command again.\r\r"
                            "Please, join the server here: {0}".format(bot_config.server_invite_link))
        finally:
            cursor.close()
            mariadb.close()
    else:
        await bot.delete_message(ctx.message)
        await bot.send_message(ctx.message.author, "That command only works on private message. "
                                                   "Please send me the command again.")
# endregion


# region Util
def log_command(author: discord.Member, command_name: str, *args):
    args_str = ' '.join(str(arg) for arg in args)
    if len(args_str) > 0: args_str = ' '+args_str
    logging.info("Processed command: {0}{1} by {2}".format(command_name, args_str, author.id))


def check_user_role(author: discord.Member, rolecheck):
    if type(rolecheck) is list and len(set(rolecheck).intersection(set([role.id for role in author.roles]))) > 0:
        return True

    if type(rolecheck) is str and rolecheck in [role.id for role in author.roles]:
        return True

    return False

def valid_email(email):
    return re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)


def db_connect():
    # Connect to the database
    mariadb = pymysql.connect(host=bot_config.db_host,
                              port=bot_config.db_port,
                              user=bot_config.db_user,
                              password=bot_config.db_pass,
                              db=bot_config.db_name,
                              cursorclass=pymysql.cursors.DictCursor)
    return mariadb


def generate_random_string(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
# endregion


if __name__ == '__main__':
    main()
