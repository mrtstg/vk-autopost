# -*- coding: utf-8 -*-
# Импорт библиотек
import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll
import datetime
import time
import pytz
import random
import os
from threading import Thread


class AutoPostThread:
    def __init__(self, param_array, index):
        type = "chat"
        id = 0
        if 'user_id' in param_array:
            type = "user"
            id = param_array['user_id']
        else:
            id = param_array['chat_id']
        self.timeout = param_array['timeout']
        self.id = id
        self.type = type
        self.delete = param_array['delete']
        self.text = param_array['text']
        self.alive = True
        self.index = index
        self.start_task()

    def start_task(self):
        Thread(target=self.recognize, args=()).start()

    def recognize(self):
        while self.alive:
            try:
                msg_id = 0
                if self.type == "chat":
                    msg_id = vk.messages.send(
                        random_id=random.randint(-2147483648, 2147483647),
                        chat_id=self.id,
                        message=self.text,
                    )
                else:
                    msg_id = vk.messages.send(
                        random_id=random.randint(-2147483648, 2147483647),
                        user_id=self.id,
                        message=self.text,
                    )
                time.sleep(int(self.timeout) + random.randint(delay_min, delay_max))
                if self.delete:
                    vk.messages.delete(message_ids=msg_id, delete_for_all=True)
            except Exception as e:
                send_msg(user_id=int(account_id),
                         message="Ошибка при выполнении задачи #" + str(self.index) + ": " + str(e))


def reboot(is_trd_python):
    # функция перезагрузки бота
    # аругмент функции влияет на выбор команды для перезагрузки
    way = os.path.abspath(__file__)
    if is_trd_python != "-1":
        os.system("python " + way)
    else:
        os.system("python3 " + way)


def console_log(text, sym_amount=50):
    print('[' + get_time() + '] ' + text, end="\n\n")
    print("-" * sym_amount)


def get_time():
    # возвращает время формата ДД.ММ.ГГ ЧЧ:ММ:СС (по МСК)
    # например, 01.01.01 13:37:00
    return datetime.datetime.strftime(datetime.datetime.now(pytz.timezone('Europe/Moscow')), "%d.%m.%Y %H:%M:%S")


def give_words(text, min=1, max=-1):
    if max == -1:
        return ' '.join(text.split(" ")[min:])
    else:
        return ' '.join(text.split(" ")[min:max])


def send_msg(peer_id=None, domain=None, user_id=None, chat_id=None, message=None,
             sticker=None):
    vk.messages.send(
        user_id=user_id,
        random_id=random.randint(-2147483648, 2147483647),
        peer_id=peer_id,
        domain=domain,
        chat_id=chat_id,
        message=message,
        sticker_id=sticker,
    )


def resolve_task_to_text(task_list):
    tasks = []
    for task in task_list:
        task_text = str(task.index) + ") Отправка сообщения "
        if task.type != "chat":
            if task.id > 0:
                task_text += "пользователю *id" + str(task.id)
            else:
                task_text += "группе *club" + str(task.id).replace("-", "")
        else:
            task_text += "в чат #" + str(task.id)
        task_text += " с текстом '" + str(task.text)
        task_text += ". Интервал равен " + str(task.timeout)
        task_text += ". Сообщения {} удаляются за собой".format('не' if not task.delete else '')
        tasks.append(task_text)
    return "\n".join(tasks)


# получаем путь к скрипту
folder_path = os.path.abspath(__file__).replace("main.py", "")
console_log("Получен путь скрипта: " + folder_path)
# считываем параметры
config_lines = [line[line.find("=") + 1:].replace("\n", "") for line in open(folder_path + 'config.txt',
                encoding='utf-8').readlines()]
delay_min, delay_max, code_word, is_3_python, allowed_ids, account_id, task_limit, is_accessed = \
    1, 10, "kolbasa", "0", [0], 0, 10, False
try:
    console_log("Получаю параметры запуска...")
    is_3_python = config_lines[3]
    allowed_ids = [int(num) for num in config_lines[5].split(",")]
    account_id = int(config_lines[4])
    delay_min = int(config_lines[1])
    delay_max = int(config_lines[2])
    code_word = config_lines[6]
    task_limit = int(config_lines[7])
    vk_session = vk_api.VkApi(token=config_lines[0])
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
except Exception as e:
    console_log("Ошибка: " + str(e) + ". Перезапуск через 10 секунд.")
    time.sleep(10)
    reboot(is_trd_python=is_3_python)
finally:
    console_log("Запуск...")


def main():
    tasks = []
    task_dict = []
    if open(folder_path + 'tasks.txt', 'r', encoding='utf-8').read() == "":
        task_dict = []
    else:
        task_dict = eval(open(folder_path + 'tasks.txt', 'r', encoding='utf-8').read())
        if len(task_dict) > task_limit:
            raise Exception("Превышен лимит задач.")
        else:
            for task in task_dict:
                tasks.append(AutoPostThread(task, task_dict.index(task) + 1))
    print("Начинаю прием сообщений!")
    while True:
        try:
            for task in tasks:
                if not task.alive:
                    tasks.pop(tasks.index(task))
                    task_dict.pop(tasks.index(task))
                    if len(task_dict) == 0:
                        task_dict = []
                    open(folder_path + 'tasks.txt', 'w', encoding='utf-8').write(str(task_dict))
            for event in longpoll.check():
                global is_3_python, allowed_ids, account_id, delay_max, delay_min, code_word
                if event.type == VkEventType.MESSAGE_NEW and not event.from_group:
                    is_allowed = True
                    if event.user_id not in allowed_ids and event.user_id != account_id:
                        is_allowed = False
                    if is_allowed:
                        message_text = event.text
                        message_length = len(message_text.split())
                        lower_text = event.text.lower()
                        command = lower_text.split(" ")[0]
                        words = lower_text.split(" ")
                        peer_id = event.peer_id
                        if command == "задачи":
                            if not task_dict:
                                send_msg(peer_id=peer_id, message="Задач нет.")
                            else:
                                text = "Действующие задачи: \n" + resolve_task_to_text(tasks)
                                send_msg(peer_id=peer_id, message=text)

                        if command == code_word:
                            if event.from_chat:
                                send_msg(peer_id=int(account_id), message="Айди чата: " + str(event.chat_id))

                        if message_length > 5:
                            if words[0] == "новая" and words[1] == "задача":
                                if words[2] == "чат" or words[2] == "пользователь":
                                    if len(tasks) < task_limit:
                                        task = give_words(message_text, 5)
                                        if len(task) < 300:
                                            id = int(words[3])
                                            interval = int(words[4])
                                            post = {"text": task, "timeout": interval, 'delete': False}
                                            if words[2] == "чат":
                                                post['chat_id'] = id
                                            else:
                                                post['user_id'] = id
                                            task_dict.append(post)
                                            open(folder_path + 'tasks.txt', 'w', encoding='utf-8').write(str(task_dict))
                                            tasks.append(AutoPostThread(post, len(task_dict)))
                                            send_msg(peer_id=peer_id, message="Задача создана и начата!")
                                        else:
                                            send_msg(peer_id=peer_id, message="Текст должен быть короче 300 символов!")
                                    else:
                                        send_msg(peer_id=peer_id, message="Достигнут лимит задач")

                        if message_length > 2:
                            if words[0] == "удалить" and words[1] == "задачу":
                                if words[2].isdigit():
                                    tasks[int(words[2]) - 1].alive = False
                                    tasks.pop(int(words[2]) - 1)
                                    task_dict.pop(int(words[2]) - 1)
                                    for task_index in range(len(tasks)):
                                        tasks[task_index].index = task_index + 1
                                    open(folder_path + 'tasks.txt', 'w', encoding='utf-8').write(str(task_dict))
                                    send_msg(peer_id=peer_id, message="Задача удалена!")

                            if words[0] == "удалять" and words[1] == "сообщения":
                                if words[2].isdigit():
                                    tasks[int(words[2]) - 1].delete = True if not tasks[int(words[2]) - 1].delete else False
                                    task_dict[int(words[2]) - 1]['delete'] = tasks[int(words[2]) - 1].delete
                                    send_msg(peer_id=peer_id, message="Режим удаления изменен!")
                                    open(folder_path + 'tasks.txt', 'w', encoding='utf-8').write(str(task_dict))


                        if command == "чатайди":
                            if event.from_chat:
                                send_msg(peer_id=peer_id, message="Айди чата: " + str(event.chat_id))

                        if command == "какойайди" and message_length > 1:
                            screen_name = words[1]
                            if screen_name[0] == "[" and screen_name.find("|") != -1 and screen_name.find("]") != -1:
                                screen_name = screen_name[screen_name.find("|") + 1:screen_name.find("]")]\
                                    .replace("@", "").replace("*", "")
                            if screen_name.find("vk.com/") != -1:
                                screen_name = screen_name[screen_name.find(".com/") + 5::1]
                            object = vk.utils.resolveScreenName(screen_name=screen_name)
                            if not object:
                                send_msg(peer_id=peer_id, message="Данная ссылка не занята")
                            else:
                                send_msg(peer_id=peer_id,
                                         message="Тип: " + object['type'].replace("user", "пользователь") \
                                         .replace("group", "группа").replace("application", "приложение").replace(
                                             "vk_app", "приложение ВК") + "\nАйди: " + \
                                                 str(object['object_id']))

        except Exception as e:
            console_log("Ошибка: " + str(e))



if __name__ == "__main__":
    params = "Бот запущен! Параметры: \n"
    if allowed_ids == [0]:
        console_log("Разрешенные айди не настроены. Прекращаю запуск.")
        exit(0)
    else:
        params += "Люди, имеющие доступ к редактированию задач: " + str(allowed_ids) + "\n"
    if account_id == 0:
        console_log("Не настроен айди аккаунта, на котором будет автопост. Прекращаю запуск")
        exit(0)
    else:
        params += "Айди аккаунта, на котором будет автопост: " + str(
            account_id) + " . Внимательно проверьте корректность этого параметра\n"
    params += "Команда для проверки и логирования айди чата: " + code_word
    params += "\nЛимит задач: " + str(task_limit)
    console_log(params)
    main()
