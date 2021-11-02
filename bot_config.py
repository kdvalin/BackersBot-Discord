#!/usr/bin/python

import os

# Discord Bot token
discord_token = os.environ.get("DISCORD_BOT_TOKEN")

# Logging
log_folder = ""

# Server ID (you can get this right-clicking your server and selecting Copy ID)
server_id = os.environ.get("DISCORD_SERVER_ID")
# Your Server invite link, make sure this doesn't expire!
server_invite_link = os.environ.get("DISCORD_INVITE_LINK")

# DB Config
db_host = os.environ.get("DB_HOST")
db_port = int(os.environ.get("DB_PORT"))
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")

smtp_host = os.environ.get("SMTP_HOST")
smtp_user = os.environ.get("SMTP_USER")
smtp_passwd = os.environ.get("SMTP_PASSWD")
smtp_port = int(os.environ.get("SMTP_PORT"))

is_test = bool(os.environ.get('TEST_MODE'))