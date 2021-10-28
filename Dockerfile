FROM python:3.6-bullseye

ENV DISCORD_BOT_TOKEN ""

ENV DISCORD_SERVER_ID ""
ENV DISCORD_INVITE_LINK ""

# DB Config
ENV DB_HOST ""
ENV DB_PORT 3306
ENV DB_USER ""
ENV DB_PASS ""
ENV DB_NAME ""

# Email Config
ENV SMTP_HOST ""
ENV SMTP_USER ""
ENV SMTP_PASSWD ""
ENV SMTP_PORT 465

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
COPY  * /app/

ENTRYPOINT [ "python3", "main.py" ]
