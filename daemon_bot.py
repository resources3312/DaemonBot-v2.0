from telebot import TeleBot, util
from platform import platform, processor
import time
import sys
import os
import socket
from psutil import sensors_battery
from subprocess import getoutput
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from keyboard import press_and_release
from dotenv import load_dotenv

driver = None

load_dotenv()

bot = TeleBot(os.getenv("TOKEN"))

def get_info_ipv4() -> str:
    """
    Returning local or global ipv4
    
    no argument - Local ipv4
    
    -w, --wan - Global ipv4 
    
    Not connection - 127.0.0.1
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except socket.error: return "127.0.0.1"


def definedistr() -> str:
    """
    Returning your linux distribtion from os-release
    file
    
    """
    try:
        with open('/etc/os-release', 'r', encoding="utf-8") as f:
            return f.read().split()[9].split('=')[1].lower()
    except EOFError: return 

def conf_write_option(file: str, param: str, option: str) -> None:
    """
    Changing option in config file
    
    """
    try:
        with open(file, "r", encoding="utf-8") as f:
            raw = f.read().split()
            index = raw.index(param)
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()
                data = text.replace(raw[index], option)
                with open(file, "w", encoding="utf-8") as f:
                    f.write(data)
    except (EOFError, IndexError): pass

def conf_write_value(file: str, param: str, option: str) -> None:
    """
    Changing value of option in config file
    
    """
    try:
        with open(file, "r", encoding="utf-8") as f:
            raw = f.read().split()
            index = raw.index(param) + 1
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()
                data = text.replace(raw[index], option)
                with open(file, "w", encoding="utf-8") as f:
                    f.write(data)
    except (EOFError, IndexError): pass


def init_ssh() -> str:
    """
    Installi if not installed, and running SSH-server

    """
    if "nt" in os.name: return get_info_ipv4()
        # In development stage
    else:
        if "not found" in getoutput("which sshd"):
            match definedistr():
                case "debian":
                    os.system('apt update -y')
                    os.system('apt install openssh-server -y')
                case "ubuntu":
                    os.system('apt update -y')
                    os.system('apt install openssh-server -y')
                case "centos":
                    pass
                case "fedora":
                    os.system("dnf update")
                    os.system('dnf install openssh-server -y')
                case "arch":
                    os.system('pacman -Sy')
                    os.system('pacman -S openssh')
                case "gentoo":
                    os.system('emerge --sync')
                    os.system('emerge openssh')
            conf_write_option("/etc/ssh/sshd_config", "#ListenAddress", "ListenAddress")
            conf_write_option("/etc/ssh/sshd_config", "#Port", "Port")
        conf_write_value("/etc/ssh/sshd_config", "ListenAddress", get_info_ipv4())
        os.system("systemctl restart ssh")
        return get_info_ipv4()

def parse_argumnt(option: str) -> str:
    try: return sys.argv[sys.argv.index(option) + 1]
    except: return

@bot.message_handler(func=lambda message: "https://" in message.text and "youtu" in message.text, content_types=["text"])
def open_url(message):
    try: 
        global driver
        driver = webdriver.Firefox()
        driver.get(message.text)
        driver.maximize_window()
        driver.find_element(By.XPATH,'//*[@id="movie_player"]').click()
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f"<b>{driver.title}</b>\n\n<b>Предупреждение</b>\nСоблюдайте правило <b>одно меню - одно видео</b>, и не забывайте закрывать видео с помощью кнопки закрыть", reply_markup=util.quick_markup(
            {"Закрыть": {"callback_data": "player_kill"} ,
             "Запустить/Приостановить": {"callback_data": "player_switch"}, 
             "Полноэкранный режим": {"callback_data": "player_fullscreen"},
             "Увеличить громкость": {"callback_data": "player_volume_up"}, 
             "Уменьшить громкость": {"callback_data": "player_volume_down"}, 
             "Включить/Отключить звук": {"callback_data": "player_volume_mute"},
             "Воспроизвести заново": {"callback_data": "player_replay"},
             "Перемотка назад": {"callback_data": "player_back"},
             "Перемотка вперед": {"callback_data": "player_front"}
             }, row_width=1), parse_mode="html")
    except: driver.quit(), bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, f"Не удалось открыть <code>{message.text}</code>\nПроверьте ссылку и попробуйте еще раз", reply_markup=util.quick_markup({"В главное меню": {"callback_data": "main"}}), parse_mode="html")

@bot.message_handler(func=lambda message: message.text not in ["/start", "/help"] and "/" in message.text, content_types=["text"])
def send_document(message):
    try:
        with open(message.text, "rb") as file:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_document(message.chat.id, file)
    except: bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Файл не найден на диске, попробуйте еще раз")

@bot.message_handler(func=lambda message: message.from_user.id == int(parse_argumnt("--id")), content_types=["document"])
def get_document(message):
    try:
        with open(str(message.document.file_name), "wb") as f:
            f.write(bot.download_file(bot.get_file(message.document.file_id).file_path))
            bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Ваш файл был сохранен на диске", reply_markup=util.quick_markup({"В главное иеню": {"callback_data": "main"}})) 
    except: bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Ваш файл не был сохранен на диске, проверьте файл и попробуйте еще раз", reply_markup=util.quick_markup({"В главное иеню": {"callback_data": "main"}})) 


@bot.message_handler(func=lambda message: message.from_user.id == int(parse_argumnt("--id")), content_types=["photo"])
def get_photo(message):
    try:
        with open("file.png", "wb") as f:
            f.write(bot.download_file(bot.get_file(message.photo[-1].file_id).file_path))
            bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Ваш файл был сохранен на диске", reply_markup=util.quick_markup({"В главное иеню": {"callback_data": "main"}})) 


    except: bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Ваш файл не был сохранен на диске, проверьте файл и попробуйте еще раз", reply_markup=util.quick_markup({"В главное меню": {"callback_data": "main"}})) 


@bot.message_handler(func=lambda message: message.from_user.id == int(parse_argumnt("--id")), content_types=["video"])
def get_video(message):
    try:
        with open(message.video.file_name, "wb") as f:
            f.write(bot.download_file(bot.get_file(message.video.file_id).file_path))
            bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Ваш файл был сохранен на диске", reply_markup=util.quick_markup({"В главное иеню": {"callback_data": "main"}}))
    
    except: bot.delete_message(message.chat.id, message.message_id), bot.send_message(message.chat.id, "Ваш файл не был сохранен на диске, проверьте файл и попробуйте еще раз", reply_markup=util.quick_markup({"В главное иеню": {"callback_data": "main"}})) 

@bot.message_handler(commands=["help"])
def get_help(message):
    bot.delete_message(message.chat.id, message.message_id), bot.send_message(int(parse_argumnt("--id")), "<b>DaemonBot v2.0</b>\nПредставяет собой вторую версию легендарного в очень узких кругах DaemonBot v1.0, существует для удобного доступа к ресурсам вашего компьютера средствами TelegramAPI", parse_mode="html")

@bot.message_handler(commands=["start"])
def get_start(message):
    if message.chat.id != int(parse_argumnt("--id")): bot.send_message(int(parse_argumnt("--id")), f"<b>Замечена попытка доступа к панели управления</b>\n\n<b>ID</b> - {message.from_user.id}\n\n<b>First name</b> - {message.from_user.first_name}\n\n<b>Last name</b> - {message.from_user.last_name}\n\n<b>Username</b> - {message.from_user.username}", parse_mode="html"), bot.send_message(message.chat.id, "Была зафиксирована попытка доступа к панели управления, ваши данные были направлены владельцу")
    else: bot.send_message(message.from_user.id, f"<b>Панель управления</b>\n\n<b>Имя устройства</b> - <code>{socket.gethostname()}</code>\n\n<b>Питание</b> - <code>{sensors_battery().percent if sensors_battery() else 'Подключено'}</code>\n\n<b>OC</b> - <code>{platform()}</code>\n\n<b>Процессор</b> - <code>{processor()}</code>\n\n<b>Локальный адрес</b> - <code>{get_info_ipv4()}</code>\n\n<b>Uptime</b> - uptime\n", reply_markup=util.quick_markup(
        {"Отключить машину": {"callback_data": "shutdown"},
         "Поднять ssh": {"callback_data": "ssh_up"}, 
        "Увеличить громкость": {"callback_data": "system_volume_up"},
         "Уменьшить громкость": {"callback_data": "system_volume_down"},
         "Включить/Отключить звук": {"callback_data": "system_volume_mute"}},
        row_width=1), parse_mode="html") 


#@bot.callback_query_handler(func=lambda call: True)
@bot.callback_query_handler(func=lambda call: True)
def start_handler(call):
    match call.data:
        case "main": bot.delete_message(call.message.chat.id, call.message.message_id), bot.send_message(call.message.chat.id, f"<b>Панель управления</b>\n\n<b>Имя устройства</b> - <code>{socket.gethostname()}</code>\n\n<b>Питание</b> - <code>{sensors_battery().percent if sensors_battery() else 'Подключено'}</code>\n\n<b>OC</b> - <code>{platform()}</code>\n\n<b>Процессор</b> - <code>{processor()}</code>\n\n<b>Локальный адрес</b> - <code>{get_info_ipv4()}</code>\n\n<b>Uptime</b> - uptime\n", reply_markup=util.quick_markup(
        {"Отключить машину": {"callback_data": "shutdown"},
         "Поднять ssh": {"callback_data": "ssh_up"}, 
        "Увеличить громкость": {"callback_data": "system_volume_up"},
         "Уменьшить громкость": {"callback_data": "system_volume_down"},
         "Включить/Отключить звук": {"callback_data": "system_volume_mute"}},
        row_width=1), parse_mode="html")
        case "ssh_up": bot.delete_message(call.message.chat.id, call.message.message_id), bot.send_message(call.message.chat.id, f"<b>SSH сервер был запущен</b>\nЛокальный адрес - <code>{init_ssh()}</code>", reply_markup=util.quick_markup({"В главное меню": {"callback_data": "main"}}), parse_mode="html")
        case "system_volume_up": press_and_release("volume up")
        case "system_volume_down": press_and_release("volume down")
        case "system_volume_mute": press_and_release("volume mute")
        case "player_kill": driver.quit(), bot.delete_message(call.message.chat.id, call.message.message_id), bot.send_message(call.message.chat.id, "Плеер был закрыт, чтобы вернуться в главное меню нажмите кнопку ниже", reply_markup=util.quick_markup({"В главное меню": {"callback_data": "main"}}))  
        case "player_switch": driver.find_element(By.XPATH,'//*[@id="movie_player"]').click() 
        case "player_volume_mute": driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys("m")
        case "player_volume_up": [driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys(Keys.ARROW_UP) for i in range(0, 2)]
        case "player_volume_down": [driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys(Keys.ARROW_DOWN) for i in range(0, 2)]
        case "player_front": driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys(Keys.ARROW_RIGHT)
        case "player_back": driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys(Keys.ARROW_LEFT)
        case "player_fullscreen": driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys("f")
        case "player_replay": driver.find_element(By.XPATH,'//*[@id="movie_player"]').send_keys("0")

def main() -> None:
    bot.infinity_polling()

if __name__ == '__main__':
    main()
