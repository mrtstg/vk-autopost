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
    def __init__(self, task, index):
        self.task = task
        self.alive = True
        self.index = index
        self.start_thread()

    def start_thread(self):
        Thread(target=self.recognize_task).start()

    def recognize_task(self):
        task = self.task
        id = task[0:task.find("|")]
        text = task[task.find("|") + 1: task.find("[")]
        interval = task[task.find("[") + 1: task.find("]")]
        add_codes = task[task.find("[") + 1:]
        while self.alive:
            try:
                if "c" in add_codes:
                    send_msg(chat_id=int(id), message=text)
                elif "u" in add_codes:
                    send_msg(user_id=int(id), message=text)
            except Exception as e:
                send_msg(user_id=int(account_id),
                         message="Ошибка при выполнении задачи #" + str(self.index) + ": " + str(e))
            time.sleep(int(interval) + random.randint(r_del_min, r_del_max))


def console_log(text, sym_amount=50):
    print(text, end="\n\n")
    print("-" * sym_amount)


def reboot(is_third_python):
    cmd = os.path.abspath(__file__)
    if is_third_python is not "1":
        cmd = "python " + cmd
    else:
        cmd = "python3 " + cmd
    os.system(cmd)


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


def resolve_task_to_text(tasks_list):
    tasks = []
    for task_str in tasks_list:
        id = task_str[0:task_str.find("|")]
        text = task_str[task_str.find("|") + 1:task_str.find("[")]
        interval = task_str[task_str.find("[") + 1: task_str.find("]")]
        additional_codes = task_str[task_str.find("[") + 1:]
        task_text = str(tasks_list.index(task_str) + 1) + ") Отправка сообщения "
        if "c" in additional_codes:
            task_text += "в чат #"
        elif "u" in additional_codes:
            if id[0] != "-":
                task_text += "пользователю *id"
            else:
                task_text += "группе *club"
        task_text += id.replace("-", "")
        task_text += " с текстом '" + text + "'"
        task_text += ". Интервал равен " + interval + " секунд"
        tasks.append(task_text)
    return "\n".join(tasks)


# Получаем путь к скрипту
path = os.path.abspath(__file__).replace(r"main.py", "")
# Считываем параметры
console_log("Получен путь скрипта: " + path)
config_lines = open(path + "config.txt", encoding='utf-8').readlines()
for line in config_lines:
    config_lines[config_lines.index(line)] = line[line.find("=") + 1:].replace("\n", "")
# Перечисление базовых переменных
is_third_python, allowed_ids, code_word, r_del_min, r_del_max, account_id, task_limit = 0, [], "", 0, 0, 0, 0
try:
    console_log("Получаю параметры запуска...")
    is_third_python = config_lines[3]
    allowed_ids = [int(num) for num in config_lines[5].split(",")]
    account_id = int(config_lines[4])
    r_del_min = int(config_lines[1])
    r_del_max = int(config_lines[2])
    code_word = config_lines[6]
    task_limit = int(config_lines[7])
    vk_session = vk_api.VkApi(token=config_lines[0])
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
except Exception as e:
    console_log("Ошибка: " + str(e))
    reboot(is_third_python)


def main():
    tasks = []
    task_file = open(path + "tasks.txt", encoding='utf-8').readlines()
    if task_file and len(task_file) <= task_limit:
        for task in task_file:
            tasks.append(AutoPostThread(task, task_file.index(task) + 1))
    elif len(task_file) > task_limit:
        raise Exception("Превышен лимит задач.")
        exit(0)
    while True:
        try:
            for event in longpoll.listen():
                global is_third_python, allowed_ids, account_id, r_del_min, r_del_max, code_word
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
                            if not task_file:
                                send_msg(peer_id=peer_id, message="Задач нет.")
                            else:
                                text = "Действующие задачи: \n" + resolve_task_to_text(task_file)
                                send_msg(peer_id=peer_id, message=text)

                        if command == code_word:
                            if event.from_chat:
                                send_msg(peer_id=int(account_id), message="Айди чата: " + str(event.chat_id))

                        if message_length > 5:
                            if words[0] == "новая" and words[1] == "задача":
                                if words[2] == "чат" or words[2] == "пользователь":
                                    if len(tasks) < task_limit:
                                        task = give_words(message_text, 5)
                                        id = int(words[3])
                                        interval = int(words[4])
                                        task_code = str(id) + "|" + task + "[" + str(interval) + "]"
                                        if words[2] == "чат":
                                            task_code += "c"
                                        else:
                                            task_code += "u"
                                        task_file.append(task_code)
                                        open('tasks.txt', 'w', encoding='utf-8').write('\n'.join(task_file))
                                        tasks.append(AutoPostThread(task_code, len(task_file)))
                                        send_msg(peer_id=peer_id, message="Задача создана и начата!")
                                    else:
                                        send_msg(peer_id=peer_id, message="Достигнут лимит задач")

                        if message_length > 2:
                            if words[0] == "удалить" and words[1] == "задачу":
                                if words[2].isdigit():
                                    tasks[int(words[2]) - 1].alive = False
                                    tasks.pop(int(words[2]) - 1)
                                    task_file.pop(int(words[2]) - 1)
                                    for task_index in range(len(tasks)):
                                        tasks[task_index].index = task_index + 1
                                    open('tasks.txt', 'w', encoding='utf-8').write('\n'.join(task_file))
                                    send_msg(peer_id=peer_id, message="Задача удалена!")

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
