FROM python:bullseye

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

COPY  * /app/
RUN python3 -m pip install -r /app/requirements.txt

ENTRYPOINT [ "python3", "/app/main.py" ]