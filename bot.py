import logging
import re
from optparse import OptionParser

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import paramiko, os
from dotenv import load_dotenv

import psycopg2
from psycopg2 import Error

#load_dotenv(".env")

host = os.getenv('HOST')
port = os.getenv('PORT')
username = os.getenv('USER')
password = os.getenv('PASSWORD')

host_db = os.getenv('HOST_DB')
port_db = os.getenv('PORT_DB')
username_db = os.getenv('USER_DB')
password_db = os.getenv('PASSWORD_DB')
database_db = os.getenv('DATABASE_DB')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

TOKEN = os.getenv('TOKEN')


# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

logger.info("Запуск бота")
def connectAndCommand(command):
    try:
        client.connect(hostname=host, username=username, password=password, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        return data
    except Exception as err:
        logger.warning('Возникло исключение: ' + str(err))
        return "Ошибка при кодключении или выполнении команды"
    

def connectToDB(command=None, emails=None, phones=None):
    connection = None
    try:
        connection = psycopg2.connect(user=username_db,
                                password=password_db,
                                host=host_db,
                                port=port_db, 
                                database=database_db)
        
        cursor = connection.cursor()
        if emails:
            for email in emails:
                cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email,))
            connection.commit()
            return True
        if phones:
            for phone in phones:
                cursor.execute("INSERT INTO phones (phone) VALUES (%s)", (phone,))
            connection.commit()
            return True
        
        if command:
            cursor.execute(command)
            data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
        return data  
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        return False
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def start(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду start")
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду help")
    update.message.reply_text('Help!')

def getRelease(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_release")
    data = connectAndCommand('cat /etc/os-release')
    update.message.reply_text(data)

def getUname(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_uname")
    data = connectAndCommand('uname -a')
    update.message.reply_text(data)

def getUptime(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_uptime")
    data = connectAndCommand('uptime')
    update.message.reply_text(data)

def getDf(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_df")
    data = connectAndCommand('df -h')
    update.message.reply_text(data)

def getFree(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_free")
    data = connectAndCommand('free -h')
    update.message.reply_text(data)

def getMpstat(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_mpstat")
    data = connectAndCommand('mpstat')
    update.message.reply_text(data)

def getW(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_w")
    data = connectAndCommand('w -h')
    update.message.reply_text(data)

def getAuth(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_auths")
    data = connectAndCommand('last -10')
    update.message.reply_text(data)

def getCritical(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_critical")
    data = connectAndCommand('journalctl -p crit -n 5')
    update.message.reply_text(data)

def getPs(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_ps")
    data = connectAndCommand('ps')
    update.message.reply_text(data)

def getSs(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_ss")
    data = connectAndCommand('ss -tlnp')
    update.message.reply_text(data)


def getService(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_services")
    data = connectAndCommand('service --status-all | grep +')
    update.message.reply_text(data)

def getReplLogs(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_repl_logs")
    data = connectToDB("SELECT pg_read_file(pg_current_logfile());")
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    data = filter_replication_logs(data)
    msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for text in msgs:
        update.message.reply_text(text)

def filter_replication_logs(log_data):
    keywords = ['repl', 'checkpoint']
    replication_logs = []
    for line in log_data.split('\n'):
        if any(keyword.lower() in line.lower() for keyword in keywords):
            replication_logs.append(line)
    return '\n'.join(replication_logs)

def getEmails(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_emails")
    data = connectToDB("SELECT * FROM emails;")
    emails = ''
    for i, row in enumerate(data, start=1):
        emails += f'{i}. {row[1]}\n'
    update.message.reply_text(emails)

def getPhones(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_emails")
    data = connectToDB("SELECT * FROM phones;")
    phones = ''
    for i, row in enumerate(data, start=1):
        phones += f'{i}. {row[1]}\n'
    update.message.reply_text(phones)


def getAptListCommand(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду get_apt_list")
    update.message.reply_text('Введите название пакета (для вывода всех пакетов отправьте "все"):')
    return 'get_apt_list'

def findPhoneNumbersCommand(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду find_phone_number")
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_number'

def findEmailsCommand(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду find_email")
    update.message.reply_text('Введите текст для поиска Emails: ')
    return 'find_email'

def verifyPassCommand(update: Update, context):
    user = update.effective_user
    logger.info('Пользователь ' + str(user.username) + " запустил команду verify_password")
    update.message.reply_text('Введите пароль для проверки: ')
    return 'verify_password'


def getAptList(update: Update, context):
    
    user_input = update.message.text 
    
    data = ""
    if(user_input == "все"):
        data = connectAndCommand('apt list --installed')
        msgs = [data[i:i + 4096] for i in range(0, len(data), 4096)]
        for text in msgs:
            update.message.reply_text(text)
            return ConversationHandler.END
    else:
         data = connectAndCommand('apt list --installed | grep ' + user_input)
    if(not data):
        data = "Данный пакет не установлен"
    update.message.reply_text(data)
    return ConversationHandler.END 

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text 

    phoneNumRegex = re.compile(r"(\+7|8)([\( -]\d{3}[\) -]\d{3}[ -]?\d{2}[ -]?\d{2})|(\+7|8)(\d{3}\d{3}[ -]?\d{2}[ -]?\d{2})")

    phoneNumberList = phoneNumRegex.findall(user_input)

    if not phoneNumberList: 
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END 
    
    joined_numbers = [''.join(filter(None, num)) for num in phoneNumberList]

    phoneNumbers = '' 
    for i in range(len(joined_numbers)):
        phoneNumbers += f'{i+1}. {joined_numbers[i]}\n' 

    context.user_data['found_phones'] = joined_numbers

    update.message.reply_text('Найдены следующие номера телефонов:\n\n' + phoneNumbers + '\nХотите записать их в базу данных? (Да/Нет)')
    return 'wait_confirm_to_write_phone'


def confPhone(update: Update, context):
    user_response = update.message.text.lower()
    
    if user_response == 'да':
        phones = context.user_data['found_phones']
        res = connectToDB(phones=phones)
        print(res)
        if(res):
            update.message.reply_text('Номера телефонов успешно записаны в базу данных.')
        else:
            update.message.reply_text('При записи в БД произошла ошибка')
    
    context.user_data.pop('found_phones', None)

    return ConversationHandler.END

def findEmails (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'[A-Za-z0-9_-]+?\.?[A-Za-z0-9_-]+@[A-Za-z0-9-_]+\.[A-Za-z]{2,}') 

    emailList = emailRegex.findall(user_input) 
    if not emailList: 
        update.message.reply_text('Email адреса не найдены')
        return ConversationHandler.END 
    
    emails = '' 
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' 
    context.user_data['found_emails'] = emailList
    update.message.reply_text('Найдены следующие email адреса:\n\n' + emails + '\nХотите записать их в базу данных? (Да/Нет)')
    return 'wait_confirm_to_write_email'

def confEmail(update: Update, context):
    user_response = update.message.text.lower()
    
    if user_response == 'да':
        emails = context.user_data['found_emails']
        res = connectToDB(emails=emails)
        print(res)
        if(res):
            update.message.reply_text('Email адреса успешно записаны в базу данных.')
        else:
            update.message.reply_text('При записи в БД произошла ошибка')
    
    context.user_data.pop('found_emails', None)

    return ConversationHandler.END

def verifyPass (update: Update, context):
    user_input = update.message.text

    passRegex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$') 

    checkPass = passRegex.search(user_input) 
    if (checkPass != None): 
        update.message.reply_text('Пароль сложный')
    else:
         update.message.reply_text('Пароль простой')
    return ConversationHandler.END 

def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'wait_confirm_to_write_phone': [MessageHandler(Filters.text & ~Filters.command, confPhone)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'wait_confirm_to_write_email': [MessageHandler(Filters.text & ~Filters.command, confEmail)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPassCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPass)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
        },
        fallbacks=[]
    )
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDf))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpstat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuth))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ps", getPs))
    dp.add_handler(CommandHandler("get_ss", getSs))
    dp.add_handler(CommandHandler("get_services", getService))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLogs))
    dp.add_handler(CommandHandler("get_emails", getEmails))
    dp.add_handler(CommandHandler("get_phones", getPhones))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetAptList)
		
	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, helpCommand))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
