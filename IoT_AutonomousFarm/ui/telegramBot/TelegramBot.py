import json
import requests
import random
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# function to write in a log file the message passed as argument
def write_log(message):
    with open("./logs/TelegramBot.log", "a") as log_file:
        log_file.write(f"{message}\n")

os.makedirs("./logs", exist_ok=True)   # create the logs directory if it doesn't exist

# each time that the device starts, we clear the log file
with open("./logs/TelegramBot.log", "w") as log_file:
    pass

try:
    # read the greenhouse_id and mqtt information of the broker from the json file
    with open("./TelegramBot_config.json", "r") as config_fd:
        config = json.load(config_fd)   # read the configuration from the json file
        catalog_url = config["catalog_url"] # read the url of the Catalog
        mqtt_broker = config["mqtt_connection"]["mqtt_broker"]  # read the mqtt broker address
        mqtt_port = config["mqtt_connection"]["mqtt_port"]  # read the mqtt broker port
        keep_alive = config["mqtt_connection"]["keep_alive"]    # read the keep alive time of the mqtt connection
        telegram_token = config["telegram_token"]

except FileNotFoundError:
    write_log("DeviceConnector_config.json file not found")
    exit(1)   # exit the program if the file is not found
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # send a welcome message to the user
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the IoT Autonomous Farm Bot!\nUse /login connect telegram to your Smart Greehouse.")
    except Exception as e:
        write_log(f"Error sending start message: {e}")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Generating OTP code...\nInsert it into your web application to connect telegram to your account.")
    user_id = update.effective_user.id
    # generate a random OTP code
    otp_code = str(random.randint(100000, 999999))  # generate a 6-digit OTP code
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your OTP code is: {otp_code}")
    # send the OTP to the Catalog service
    try:
        response = requests.post(
            f"{catalog_url}/otp",
            json={"user_id": user_id, "otp_code": otp_code}
        )
        if response.status_code == 200:
            write_log(f"OTP sent successfully for user {user_id}")

        else:
            write_log(f"Failed to send OTP for user {user_id}: {response.text}")

    except requests.RequestException as e:
        write_log(f"Error sending OTP: {e}")

# try:
#     # get the user id associated with this Telegram chat from the Catalog
#     response = requests.get(f'{catalog_url}/get_telegram_user', params={'telegram_user_id': update.effective_user.id})
#     if response.status_code == 200:  # if the request is successful
#         response = response.json()    # get the response in json format
#         user_id = response.get("user_id")
#         username = response.get("username")
#         await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Welcome {username}!\nYour user id is: {user_id}")

#     elif response.status_code == 404:  # if the user is not found
#         await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not registered. Please, genereate an otp with /otp and insert it into your web application to log in.")
        
#     else:
#         error_msg = response.json().get("error", "Unknown error")
#         write_log(f"Failed to get user id from the Catalog\nResponse: {error_msg}")

# except Exception as e:
#     write_log(f"Error getting user id from the Catalog: {e}")

def main():
    application = ApplicationBuilder().token(telegram_token).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('login', login))

    application.run_polling()

if __name__ == '__main__':
    main()