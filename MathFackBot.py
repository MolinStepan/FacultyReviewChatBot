import telebot
from telebot import types
import locale
import random
import sqlite3 as sql
import hashlib

locale.setlocale(locale.LC_ALL, 'ru')
bot = telebot.TeleBot("5703064203:AAHbwCppKSQb-mLi61Ufh0fmeDAi7Zr2RZI")
bot.set_my_description("Бот работает")
bot.set_my_short_description("Бот работает")
state = dict() # словарь, в котором хранится вся информация для запущеных процессов оценивания
reviewing_len = [15, 9]
year = 2023
questions = [["1. Процент Фундаментальных знаний:",
              "2. Сложность фундаментальных знаний:",
              "3. Сложность понимания фундаментальных знаний:", 
              "4. Полезность фундаментальных знаний:", 
              "5: Интересность фундаментальных знаний",
              "6. Сложность прикладных знаний:", 
              "7. Сложность понимания прикладных знаний:", 
              "8. Полезность прикладных знаний:", 
              "9: Интересность прикладных знаний", 
              "10. Процент совпадения материала с другими курсами:", 
              "11. Комментарий:"], 
             ["1. Способность идти на контакт:", 
              "2. Сложность выдаваемых задач:", 
              "3. Интересность выдаваемых задач:", 
              "4. Лояльность при оценивании:", 
              "5. Комментарий:"]]
Answers = ["0%", "25%", "50%", "75%", "100%", "Без понятия"]
markup_starter = types.ReplyKeyboardMarkup(resize_keyboard = True)
btnCourse = types.KeyboardButton("/reviewcourse")
btnTeacher = types.KeyboardButton("/reviewteacher")
btnGetCourse = types.KeyboardButton("/getcourseinfo")
btnGetTeacher = types.KeyboardButton("/getteacherinfo")
btnHelp = types.KeyboardButton("/help")
markup_starter.row(btnHelp, btnCourse, btnTeacher) 
markup_starter.row(btnGetCourse, btnGetTeacher)
markup_percents = types.ReplyKeyboardMarkup(resize_keyboard = True)
btn0 = types.KeyboardButton(Answers[0])
btn25 = types.KeyboardButton(Answers[1])
btn50 = types.KeyboardButton(Answers[2])
btn75 = types.KeyboardButton(Answers[3])
btn100 = types.KeyboardButton(Answers[4])
btnUnsure = types.KeyboardButton(Answers[-1])
markup_percents.row(btn0, btn25, btn50)
markup_percents.row(btn75, btn100, btnUnsure)
markup_comment = types.ReplyKeyboardMarkup(resize_keyboard = True)
btnNoComment = types.KeyboardButton("Без комментариев")
markup_comment.row(btnNoComment) 
markup_change = types.ReplyKeyboardMarkup(resize_keyboard = True)
btnYes = types.KeyboardButton("Да")
btnChange = types.KeyboardButton("Изменить")
btnClear = types.KeyboardButton("Стереть")
markup_change.row(btnYes, btnChange, btnClear)
markup_stopchange = types.ReplyKeyboardMarkup(resize_keyboard = True)
button = types.KeyboardButton('Завершить редактирование')
markup_stopchange.row(button)

#stopcommand, останавливает выполение по команде /stop
def teststop(message, uselessvar1=0, uv2=0, uv3=0, uv4=0, uv5=0, uv6=0):
    if message.text == "/stop":
        bot.send_message(message.chat.id, "Сброшено")
        if message.from_user.id in state:
            del state[message.from_user.id]
        return True
    return False
def stopcommand(func):
    def wrapper(*args, **kwargs):
        if teststop(*args, **kwargs):
            return
        func(*args, **kwargs)
    return wrapper 

#registered_check
def registered_check(message):
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute(f"SELECT COUNT() FROM students WHERE id = '{message.from_user.id}'")
        if 0 == cur.fetchone()[0]:
            bot.send_message(message.chat.id, "Вы не зарегистрированы, зарегистрируйтесь с помощью /register")
            return False
    return True

#admin_check
def admin_check(message):
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute(f"SELECT COUNT() FROM students WHERE id = '{message.from_user.id}' AND isAdmin = 1")
        if 0 == cur.fetchone()[0]:
            bot.send_message(message.chat.id, "Вы не администратор")
            return False
    return True

#tomark, переводит строку в оценку от 0 до 100 плюс значение -1 для неопределившихся
def tomark(string):
    if string == "Без понятия":
        return -1
    n=101
    if string[-1] == "%":
        string = string[:-1]
    try:
        n=int(string)
    except ValueError:
        n=101
    return n

#add_to_db
def add_to_db(Id):
    command = "INSERT INTO "
    if state[Id][0] == 0:
        command += "course_evaluation VALUES ('"
        command += f"""{state[Id][3]}', '{state[Id][2].replace(", ", "', '")}'{(", NULL" * (3 - state[Id][2].count(",") ) )}"""
    else:
        command += f"teacher_evaluation VALUES ('{state[Id][3]}'"
    command += f", {year}, {state[Id][1]}"
    for i in range(4,len(state[Id]) - 1):
        command += f""", {(state[Id][i] if state[Id][i] >= 0 else "NULL")}"""
    command += f""", {(("'" + state[Id][-1] + "'") if state[Id][-1] != "—" else "NULL")}, """
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute(f"SELECT name, num FROM students WHERE id = '{Id}'")
        temp = cur.fetchone()
        temp = hash(temp[0] + ", " + str(temp[1])) 
        command += str(temp) + ")"
        cur.execute(command)

#hash, хеширует имя студента, возможно надо переписать
def hash(string):
    res = hashlib.sha3_224(string)
    return res & 281474976710655

@bot.message_handler(commands=["start"])
def startbot(message):
    if registered_check(message):
        bot.send_message(message.chat.id, "Под этим солцнем и небом мы тепло приветствуем тебя", reply_markup=markup_starter )

@bot.message_handler(commands=["createdb"])
def createdb(message):
    if not admin_check(message):
        return
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS students (name TEXT, num INTEGER, id INTEGER, isAdmin INTEGER, course INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS courses (name TEXT, teacher1 TEXT, teacher2 TEXT, teacher3 TEXT, teacher4 TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS teachers (name TEXT, contacts TEXT, interests TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS course_evaluation (name TEXT, teacher1 TEXT, teacher2 TEXT, teacher3 TEXT, teacher4 TEXT, year INTEGER, course INTEGER q1 INTEGER, q2 INTEGER, q3 INTEGER, q4 INTEGER, q5 INTEGER, q6 INTEGER, q7 INTEGER, q8 INTEGER, q9 INTEGER, q10 INTEGER, q11 TEXT, reviewerHASH INTEGER )")
        cur.execute("CREATE TABLE IF NOT EXISTS teacher_evaluation (name TEXT, year INTEGER, course INTEGER, q1 INTEGER, q2 INTEGER, q3 INTEGER, q4 INTEGER, q5 TEXT)")
    print("create")

@bot.message_handler(commands=["stopbot"])
def stopbot(message):
    if not admin_check(message):
        return
    bot.set_my_description("Бот выключен")
    bot.set_my_short_description("Бот выключен")
    print("close")
    exit()

@bot.message_handler(commands=["help"])
def sendhelp(message):
    bot.send_message(message.chat.id, "/help — вывод всех комманд\n"+
                                      "/stop — прекратить текущее действие\n/reviewcourse — обзор курса\n"+
                                      "/reviewteacher — обзор преподавателя\n"+
                                      "/getcourseinfo — посмотреть обзоры на курс\n"+
                                      "/getteacherinfo — посмотреть обзоры на преподавателя"+
                                      "\n/register — регистрация",
                                      reply_markup = markup_starter)

@bot.message_handler(commands=["senddb"])
def sendDB(message):
    if not admin_check(message):
        return
    file = open("./reviews.db", "rb")
    bot.send_document(message.chat.id, file)

@bot.message_handler(commands=["reviewteacher"])
def reviewTeacher(message):
    if not registered_check(message):
        return
    if message.from_user.id in state:
        del state[message.from_user.id]
        bot.send_message(message.chat.id, "Состояние сброшено")
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute(f"SELECT course FROM students WHERE id = {message.from_user.id}")
        state[message.from_user.id] = [1, cur.fetchone()[0], ""]
    bot.send_message(message.chat.id, """Введите полное имя преподавателя, как на сайте """)
    bot.register_next_step_handler(message, reviewTeacher2)
 
@stopcommand #reviewTeacher2, получает имя преподавателя
def reviewTeacher2(message): 
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT() FROM teachers WHERE name = '" + message.text + "'" )
        if cur.fetchone()[0] == 0:
            bot.send_message(message.chat.id, "Такого преподавателя не найдено")
            bot.register_next_step_handler(message, reviewTeacher2)
        else:
            cur.execute("SELECT name, num FROM students WHERE id = '" + str(message.from_user.id) + "'")
            temp = cur.fetchone()
            temp = hash(temp[0] + ", " + str(temp[1])) 
            cur.execute("SELECT COUNT() FROM teacher_evaluation WHERE name = '" + message.text + "' AND reviewerHASH = " + str(temp))
            if cur.fetchone[0] == 0:
                state[message.from_user.id].append(message.text)
                bot.send_message(message.chat.id, questions[1][0], reply_markup = markup_percents)
                bot.register_next_step_handler(message, getVal)
            else:
                bot.send_message(message.chat.id, "Вы уже обозрели этого преподавателя", reply_markup = markup_starter)
                del state[message.from_user.id]
@bot.message_handler(commands=["reviewcourse"])
def reviewcourse(message):
    if not registered_check(message):
        return
    if message.from_user.id in state:
        del state[message.from_user.id]
        bot.send_message(message.chat.id, "Состояние сброшено")
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("SELECT course FROM students WHERE id = " + str(message.from_user.id))
        state[message.from_user.id] = [0, cur.fetchone()[0]]
    bot.send_message(message.chat.id, """Введите название курса (как в книге курсов), если в этом курсе есть и лекции и семинары, через запятую введите "лекции" или "семинары" """)
    bot.register_next_step_handler(message, reviewcourse2) 

@stopcommand #reviewСourse2, получает название курса
def reviewcourse2(message):
    find = message.text.lower()
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT() FROM courses WHERE name = '" + find + "'")
        n = cur.fetchone()[0]
        if 0 == n:
            bot.send_message(message.chat.id, "Такого курса не найдено")
            bot.register_next_step_handler(message, reviewcourse2)
        elif 1 == n:
            cur.execute("SELECT teacher1, teacher2, teacher3, teacher4 FROM courses WHERE name = '" + find + "'")
            i = cur.fetchone()[0]
            i = i[0] + ((", " + i[1])if i[1]!= None else "") + ((", " + i[2])if i[2]!= None else "") + ((", " + i[3])if i[3]!= None else "")
            state[message.from_user.id].append(i)
            state[message.from_user.id].append(find)
            bot.send_message(message.chat.id, questions[0][0], reply_markup = markup_percents )
            bot.register_next_step_handler(message, getVal)
        else:
            cur.execute("SELECT teacher1, teacher2, teacher3, teacher4 FROM courses WHERE name = '" + find + "'")
            names = []
            for i in cur.fetchall():
                names.append(types.KeyboardButton(i[0] + ((", " + i[1])if i[1]!= None else "") + ((", " + i[2])if i[2]!= None else "") + ((", " + i[3])if i[3]!= None else "")))
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            i = len(names)
            while(i>=3):
                markup.row(names[i-1], names[i-2], names[i-3])
                i-= 3
            if i == 2:
                markup.row(names[1], names[0])
            elif i == 1:
                markup.row(names[0])
            bot.send_message(message.chat.id, "Введите полное имя преподавателя (как на сайте сотрудников вышки)", reply_markup=markup)
            bot.register_next_step_handler(message, reviewcourse3, find)
 
@stopcommand #reviewСourse3, получает имена преподавателей
def reviewcourse3(message, find):
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        names = message.text.split(", ")
        names.sort()
        if len(names)>4:
            bot.send_message(message.chat.id, "слишком много преподавателей")
            return
        text=""
        for i in range(len(names)):
            text += "' AND teacher" + str(i+1)+ " = '" + names[i]
        cur.execute("SELECT COUNT() FROM courses WHERE name = '" + find + text + "'" )
        if cur.fetchone()[0] == 0:
            bot.send_message(message.chat.id, "Перподаватель не найден")
            bot.register_next_step_handler(message, reviewcourse3, find)
        else:
            cur.execute("SELECT name, num FROM students WHERE id = '" + str(message.from_user.id) + "'")
            temp = cur.fetchone()
            temp = hash(temp[0] + ", " + str(temp[1])) 
            cur.execute("SELECT COUNT() FROM course_evaluation WHERE name = '" + find + text + "' AND reviewerHASH = " + str(temp))
            if cur.fetchone()[0] == 0:
                state[message.from_user.id].append(message.text)
                print(message.text)
                state[message.from_user.id].append(find)
                bot.send_message(message.chat.id, questions[0][0], reply_markup = markup_percents )
                bot.register_next_step_handler(message, getVal)
            else:
                bot.send_message(message.chat.id, "Вы уже обозрели этот курс", reply_markup = markup_starter)
                del state[message.from_user.id]
                 
@stopcommand #getVal, получает/изменяет значение
def getVal(message):
    if len(state[message.from_user.id]) < reviewing_len[state[message.from_user.id][0]] - 1:
        n = tomark(message.text)
        if n>100:
            bot.send_message(message.chat.id, "Неверный ответ")
            bot.register_next_step_handler(message, getVal)
            return
        state[message.from_user.id].append(n)
        if state[message.from_user.id][0] == 0:
            if len(state[message.from_user.id]) == 5 and state[message.from_user.id][4] == 0:
                state[message.from_user.id].extend((-1, -1, -1, -1))
            elif len(state[message.from_user.id]) == 9 and state[message.from_user.id][4] == 100:
                state[message.from_user.id].extend((-1, -1, -1, -1))
        bot.send_message(message.chat.id, questions[state[message.from_user.id][0] ][len(state[message.from_user.id]) - 4], reply_markup= markup_comment if len(state[message.from_user.id]) == reviewing_len[state[message.from_user.id][0]] - 1 else markup_percents )
        bot.register_next_step_handler(message, getVal)
    elif len(state[message.from_user.id]) == reviewing_len[state[message.from_user.id][0]] - 1:
        state[message.from_user.id].append(message.text if message.text != "Без комментариев" else "—")
        review = ((state[message.from_user.id][2] + ", ") if state[message.from_user.id][0] == 0 else "") + state[message.from_user.id][3] + "\n"
        for i in range(len( questions[state[message.from_user.id][0]]) - 1):
            review +=  questions[state[message.from_user.id][0] ][i] +" <u><b>"+ ((str(state[message.from_user.id][i+4]) + "%") if state[message.from_user.id][i+4] >= 0 else "—") + "</b></u>\n"
        review +=  questions[state[message.from_user.id][0] ][-1] +" <u><b>"+ state[message.from_user.id][reviewing_len[state[message.from_user.id][0]] - 1] +"</b></u>\n"
        review += "Всё верно?"
        bot.send_message(message.chat.id, review, parse_mode='html', reply_markup=markup_change )
        bot.register_next_step_handler(message, changeVal)
    else:
        if message.text.lower() == "завершить редактирование":
            state[message.from_user.id].pop()
            review = ((state[message.from_user.id][2] + ", ") if state[message.from_user.id][0] == 0 else "") + state[message.from_user.id][3] + "\n"
            for i in range(len( questions[state[message.from_user.id][0] ]) - 1):
                review +=  questions[state[message.from_user.id][0] ][i] +" <u><b>"+ ((str(state[message.from_user.id][i+4]) + "%") if state[message.from_user.id][i+4] >= 0 else "—") + "</b></u>\n"
            review +=  questions[state[message.from_user.id][0] ][-1] +" <u><b>"+ state[message.from_user.id][reviewing_len[state[message.from_user.id][0]] - 1] +"</b></u>\n"
            review += "Всё верно?"
            bot.send_message(message.chat.id, review, parse_mode='html', reply_markup=markup_change )
            bot.register_next_step_handler(message, changeVal)
            return
        n=0
        try:
            n=int(message.text)
        except ValueError:
            n = 0
        if n>len( questions[state[message.from_user.id][0] ]) or n<=0:
            bot.send_message(message.chat.id, "Какой <em>номер</em> следует изменить?", parse_mode='html', reply_markup=markup_stopchange )
            bot.register_next_step_handler(message, getVal)
            return
        state[message.from_user.id][-1] = n
        bot.send_message(message.chat.id, "Новое значение", reply_markup= markup_comment if n==len( questions[state[message.from_user.id][0] ]) else markup_percents)
        bot.register_next_step_handler(message, replaceVal)
            
@stopcommand #replaceVal, получает, какое значение надо изменить
def replaceVal(message):
    print("replaceval")
    if state[message.from_user.id][-1] + 3 == reviewing_len[state[message.from_user.id][0]] - 1:
        n = message.text if message.text != "Без комментариев" else "—"
    else:
        n = tomark(message.text)
        if n>100:
            bot.send_message(message.chat.id, "Неверный ответ")
            bot.register_next_step_handler(message, replaceVal)
            return
    state[message.from_user.id][state[message.from_user.id][-1] + 3] = n
    bot.send_message(message.chat.id, "Какой номер следует изменить?", reply_markup = markup_stopchange )
    bot.register_next_step_handler(message, getVal)

@stopcommand #changeVal,  проверяет, надо ли изменять что либо
def changeVal(message):
    if message.text.lower() == "да":
        bot.send_message(message.chat.id, "Ответ записан", reply_markup=markup_starter)
        add_to_db(message.from_user.id)
        del state[message.from_user.id]
    elif message.text.lower() == "изменить":
        bot.send_message(message.chat.id, "Какой номер следует изменить?", reply_markup = markup_stopchange )
        state[message.from_user.id].append("a")
        bot.register_next_step_handler(message, getVal)
    else:
        bot.send_message(message.chat.id, "?")
        bot.register_next_step_handler(message, changeVal)

@bot.message_handler(commands=["register"])
def register(message):
    print(str(message.from_user.id))
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT() FROM students WHERE id = " + str(message.from_user.id))
        if 0 != cur.fetchone()[0]:
            bot.send_message(message.chat.id, "Вы уже зарегистрированы")
            return 
        else:
            bot.send_message(message.chat.id, "Введите номер и полное имя через запятую")
            bot.register_next_step_handler(message, input)
def input(message):  #считывает имя и группу
    text = message.text.split(",")
    if len(text)!=2:
        bot.send_message(message.chat.id, "Некорректный ввод")
        return
    n=0
    if text[1][0] == " ":
        text[1] = text[1][1::]
    try:
        n = str(text[0])
    except ValueError:
        n = 0 
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT() FROM students WHERE num = " + str(n) + " AND name = '" + text[1] + "'")
        if 0 != cur.fetchone()[0]:
            cur.execute("UPDATE students SET id = " + str(message.from_user.id) + " WHERE num = " + str(n) + " AND name = '" + text[1] + "'")
            bot.send_message(message.chat.id, "Вы успешно зарегистрированы", reply_markup=markup_starter)
        else:
            bot.send_message(message.chat.id, "Некорректный ввод")
       
@bot.message_handler(commands=["getcourseinfo"])
def getCourseInfo(message):
    if not registered_check(message):
        return
    bot.send_message(message.chat.id, "Введите название курса")
    bot.register_next_step_handler(message, getCourseInfo2)

@stopcommand #getCourseInfo2, получает название курса
def getCourseInfo2(message):
    find = message.text.lower()
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT() FROM courses WHERE name = '" + find + "'")
        n = cur.fetchone()[0]
        if 0 == n:
            bot.send_message(message.chat.id, "Такого курса не найдено")
            bot.register_next_step_handler(message, getCourseInfo2)
        elif 1 == n:
            cur.execute("SELECT teacher1, teacher2, teacher3, teacher4 FROM courses WHERE name = '" + find + "'")
            i = cur.fetchone()[0]
            i = i[0] + ((", " + i[1])if i[1]!= None else "") + ((", " + i[2])if i[2]!= None else "") + ((", " + i[3])if i[3]!= None else "")
            bot.send_message(message.chat.id, questions[0][0], reply_markup = markup_percents )
            bot.register_next_step_handler(message, getCourseInfo4, find, i)
        else:
            cur.execute("SELECT teacher1, teacher2, teacher3, teacher4 FROM courses WHERE name = '" + find + "'")
            names = []
            for i in cur.fetchall():
                names.append(types.KeyboardButton(i[0] + ((", " + i[1])if i[1]!= None else "") + ((", " + i[2])if i[2]!= None else "") + ((", " + i[3])if i[3]!= None else "")))
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            names.append("Все преподаватели")
            i = len(names)
            while(i>=3):
                markup.row(names[i-1], names[i-2], names[i-3])
                i-= 3
            if i == 2:
                markup.row(names[1], names[0])
            elif i == 1:
                markup.row(names[0])
            bot.send_message(message.chat.id, "Введите полное имя преподавателя (как на сайте сотрудников вышки)", reply_markup=markup)
            bot.register_next_step_handler(message, getCourseInfo3, find)

@stopcommand #getCourseInfo3, получает имена преподавателей
def getCourseInfo3(message, course: str):
    if message.text.lower() == "все преподаватели":
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        button = types.KeyboardButton("Нет")
        markup.row(button)
        bot.send_message(message.chat.id, "Дополнительные характеристики", reply_markup = markup)
        bot.register_next_step_handler(message, getCourseInfo4, course)
        return
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        names = message.text.split(", ")
        names.sort()
        if len(names)>4:
            bot.send_message(message.chat.id, "слишком много преподавателей")
            return
        text=""
        for i in range(len(names)):
            text += "' AND teacher" + str(i+1)+ " = '" + names[i]
        cur.execute("SELECT COUNT() FROM courses WHERE name = '" + course + text + "'" )
        if cur.fetchone()[0] == 0:
            bot.send_message(message.chat.id, "Перподаватель не найден")
            bot.register_next_step_handler(message, getCourseInfo3, course)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            button = types.KeyboardButton("Нет")
            markup.row(button)
            bot.send_message(message.chat.id, "Дополнительные характеристики", reply_markup = markup)
            bot.register_next_step_handler(message, getCourseInfo4, course, names)

@stopcommand #getCourseInfo4, получает дополнительные указания
def getCourseInfo4(message, course: str, names: list[str] = []):
    string = message.text.lower()
    year1 = False
    year2 = False
    i = string.find("годы")
    if i == -1:
        i = string.find("год")
        if i != -1:
            i += 3 
    else:
        i += 4
    if i != -1:
        while i<len(string) and (string[i] == ":" or string[i] == " "):
            i+=1
        while i<len(string) and string[i].isdigit():
            year1 = year1 or 0
            year1 = year1*10 + int(string[i])
            i += 1
        while i<len(string) and string[i] == " ":
            i+=1
        if i<len(string) and (string[i] == "-" or string[i] == "—"):
            i += 1
            while i<len(string) and string[i] == " ":
                i += 1
            while i<len(string) and string[i].isdigit():
                year2 = year2 or 0
                year2 = year2*10 + int(string[i])
                i += 1
    course1 = False
    course2 = False
    i = string.find("курсы")
    if i == -1:
        i = string.find("курс")
        if i != -1:
            i += 4
    else:
        i += 5
    if i != -1:
        while i<len(string) and (string[i] == ":" or string[i] == " "):
            i+=1
        while i<len(string) and string[i].isdigit():
            course1 = course1 or 0
            course1 = course1*10 + int(string[i])
            i += 1
        while i<len(string) and string[i] == " ":
            i+=1
        if i<len(string) and (string[i] == "-" or string[i] == "—"):
            i += 1
            while i<len(string) and string[i] == " ":
                i += 1
            while i<len(string) and string[i].isdigit():
                course2 = course2 or 0
                course2 = course2*10 + int(string[i])
                i += 1

    select = "SELECT AVG(q1), COUNT(q1)"
    for i in range(2,11):
         select += ", AVG(q" + str(i) + "), COUNT(q" + str(i) + ")" 
    select += ", COUNT(q11)"
    command = " FROM course_evaluation WHERE name = '" + course +"'"
    for i in range(len(names)):
        command += " AND teacher" + str(i+1) + " = '" + names[i] + "'"
    if year1:
        if year2:
            command += " AND year >= " + str(year1) + " AND year <= " + str(year2)
        else:
            command += " AND year = " + str(year1)
    if course1:
        if course2:
            command += " AND course >= " + str(course1) + " AND course <= " + str(course2)
        else:
            command += " AND course = " + str(course1)
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute(select + command)
        answers = cur.fetchall()
    answers = answers[0] 
    review = course + (", " if names!=[] else "") + ", ".join(names) + "\n"
    print(year1 or year2 or course1 or course2, year1, year2, course1, course2)
    if year1 or year2 or course1 or course2:
        review+= "за "
        if year1:
            review+=str(year1)
            if year2:
                review += " - " + str(year2) + " годы"
            else:
                review += "год"
            if course1:
                review+=", "
        if course1:
            review+=str(course1)
            if course2:
                review += " - " + str(course2) + " курсы"
            else:
                review += "курс"
        review+="\n"

    for i in range(len( questions[0] ) - 1):
        review +=  questions[0][i] + (" <u><b>" + (str(round(answers[2*i])) + "%" + "</b></u> (" + str(answers[2*i+1]) + ")") if answers[2*i+1]!= 0 else " нет данных") + "\n"
    print(len(answers), answers)
    if answers[-1]!= 0:
        review += ("Показать комментарии? (" + str(answers[-1]) + ")")
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        btnYes = types.KeyboardButton("Да")
        btnNo = types.KeyboardButton("Нет")
        if answers[-1] > 14:
            btn10 = types.KeyboardButton("Показать 10")
            markup.row(btnYes, btnNo, btn10)
        else:
            markup.row(btnYes, btnNo)
        bot.send_message(message.chat.id, review, parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, getCourseInfo5, command, answers[-1])
    else:
        review += "Комментариев нет"
        bot.send_message(message.chat.id, review, parse_mode='html')

@stopcommand #getCourseInfo5, выводит комментарии
def getCourseInfo5(message, command, commentsnum):
    msg = message.text.lower()
    comments = []
    answer = ""
    with sql.connect("reviews.db") as db:
            cur = db.cursor()
            cur.execute("SELECT q11" + command + " AND q11 IS NOT NULL")
            comments = cur.fetchall()
    if msg.find("показать") != -1:
        n=0
        try:
            n=int(msg[8:])
        except ValueError:
            bot.send_message(message.chat.id, "че") 
            return
        if n>commentsnum or n<1:
            bot.send_message(message.chat.id, "че") 
            return
        listofcomments = random.sample(range(commentsnum), n)
        for i in listofcomments:
            answer+= comments[i][0] + "\n\n"
    elif msg == "да":
        for i in comments:
            answer+=i[0]+"\n\n"
    else:
        return 
    bot.send_message(message.chat.id, answer)

@bot.message_handler(commands = ["getteacherinfo"])
def getTeacherInfo(message):
    if not registered_check(message):
        return
    bot.send_message(message.chat.id, "Введите полное имя преподавателя")
    bot.register_next_step_handler(message, getTeacherInfo2)

@stopcommand #getTeacherInfo2, получает имя преподавателя
def getTeacherInfo2(message):
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        name = message.text
        cur.execute("SELECT COUNT() FROM teachers WHERE name = '" + name + "'" )
        if cur.fetchone()[0] == 0:
            bot.send_message(message.chat.id, "Перподаватель не найден")
            bot.register_next_step_handler(message, getTeacherInfo2)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
            button = types.KeyboardButton("Нет")
            markup.row(button)
            bot.send_message(message.chat.id, "Дополнительные характеристики", reply_markup = markup)
            bot.register_next_step_handler(message, getTeacherInfo3, name)

@stopcommand #getTeacherInfo3, получает дополнительные указания, выдаёт информацию
def getTeacherInfo3(message, name: str):
    string = message.text.lower()
    year1 = False
    year2 = False
    i = string.find("годы")
    if i == -1:
        i = string.find("год")
        if i != -1:
            i += 3 
    else:
        i += 4
    if i != -1:
        while i<len(string) and (string[i] == ":" or string[i] == " "):
            i+=1
        while i<len(string) and string[i].isdigit():
            year1 = year1 or 0
            year1 = year1*10 + int(string[i])
            i += 1
        while i<len(string) and string[i] == " ":
            i+=1
        if i<len(string) and (string[i] == "-" or string[i] == "—"):
            i += 1
            while i<len(string) and string[i] == " ":
                i += 1
            while i<len(string) and string[i].isdigit():
                year2 = year2 or 0
                year2 = year2*10 + int(string[i])
                i += 1
    course1 = False
    course2 = False
    i = string.find("курсы")
    if i == -1:
        i = string.find("курс")
        if i != -1:
            i += 4
    else:
        i += 5
    if i != -1:
        while i<len(string) and (string[i] == ":" or string[i] == " "):
            i+=1
        while i<len(string) and string[i].isdigit():
            course1 = course1 or 0
            course1 = course1*10 + int(string[i])
            i += 1
        while i<len(string) and string[i] == " ":
            i+=1
        if i<len(string) and (string[i] == "-" or string[i] == "—"):
            i += 1
            while i<len(string) and string[i] == " ":
                i += 1
            while i<len(string) and string[i].isdigit():
                course2 = course2 or 0
                course2 = course2*10 + int(string[i])
                i += 1

    select = "SELECT AVG(q1), COUNT(q1)"
    for i in range(2,5):
         select += ", AVG(q" + str(i) + "), COUNT(q" + str(i) + ")" 
    select += ", COUNT(q5)"
    command = ""
    if year1:
        if year2:
            command += " AND year >= " + str(year1) + " AND year <= " + str(year2)
        else:
            command += " AND year = " + str(year1)
    if course1:
        if course2:
            command += " AND course >= " + str(course1) + " AND course <= " + str(course2)
        else:
            command += " AND course = " + str(course1)
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        cur.execute(select + " FROM teacher_evaluation WHERE name = '" + name +"'" + command)
        answers = cur.fetchall()
    answers = answers[0] 
    review = name + "\n"
    print(year1 or year2 or course1 or course2, year1, year2, course1, course2)
    if year1 or year2 or course1 or course2:
        review+= "за "
        if year1:
            review+=str(year1)
            if year2:
                review += " - " + str(year2) + " годы"
            else:
                review += "год"
            if course1:
                review+=", "
        if course1:
            review+=str(course1)
            if course2:
                review += " - " + str(course2) + " курсы"
            else:
                review += "курс"
        review+="\n"

    for i in range(len( questions[1] ) - 1):
        review +=  questions[1][i] + (" <u><b>" + (str(round(answers[2*i])) + "%" + "</b></u> (" + str(answers[2*i+1]) + ")") if answers[2*i+1]!= 0 else " нет данных") + "\n"
    print(len(answers), answers)
    if answers[-1]!= 0:
        review += ("Показать комментарии? (" + str(answers[-1]) + ")")
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        btnYes = types.KeyboardButton("Да")
        btnNo = types.KeyboardButton("Нет")
        if answers[-1] > 14:
            btn10 = types.KeyboardButton("Показать 10")
            markup.row(btnYes, btnNo, btn10)
        else:
            markup.row(btnYes, btnNo)
        bot.send_message(message.chat.id, review, parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, getTeacherInfo4, command, answers[-1], name)
    else:
        review += "Комментариев нет"
        bot.send_message(message.chat.id, review, parse_mode='html') 
        markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
        btnYes = types.KeyboardButton("Да")
        btnNo = types.KeyboardButton("Нет")
        markup.row(btnYes, btnNo)
        bot.send_message(message.chat.id, "Показать курсы, которые ведёт преподаватель?", reply_markup = markup)
        bot.register_next_step_handler(message, getTeacherInfo5, command, name)

@stopcommand #getTeacherInfo4, выдаёт комментарии
def getTeacherInfo4(message, command, commentsnum, name):
    msg = message.text.lower()
    comments = []
    answer = ""
    with sql.connect("reviews.db") as db:
            cur = db.cursor()
            cur.execute("SELECT q5" + command + " AND q5 IS NOT NULL")
            comments = cur.fetchall()
    if msg.find("показать") != -1:
        n=0
        try:
            n=int(msg[8:])
        except ValueError:
            bot.send_message(message.chat.id, "че") 
            return
        if n>commentsnum or n<1:
            bot.send_message(message.chat.id, "че") 
            return
        listofcomments = random.sample(range(commentsnum), n)
        for i in listofcomments:
            answer+= comments[i][0] + "\n\n"
        bot.send_message(message.chat.id, answer)
    elif msg == "да":
        for i in comments:
            answer+=i[0]+"\n\n"
        bot.send_message(message.chat.id, answer)
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    btnYes = types.KeyboardButton("Да")
    btnNo = types.KeyboardButton("Нет")
    markup.row(btnYes, btnNo)
    bot.send_message(message.chat.id, "Показать курсы, которые вёл этот преподаватель?", reply_markup=markup)
    bot.register_next_step_handler(message, getTeacherInfo5, command, name)

@stopcommand #getTeacherInfo5, выдаёт обзоры на курсы
def getTeacherInfo5(message, command, name):
    if message.text.lower()!="да":
        return
    select = "SELECT name, AVG(q1), COUNT(q1)"
    for i in range(2,11):
         select += ", AVG(q" + str(i) + "), COUNT(q" + str(i) + ")" 
    command = " FROM course_evaluation WHERE (teacher1 = '" + name + "' OR teacher2 = '" + name + "' OR teacher3 = '" + name + "' OR teacher4 = '" + name + "')" + command + " GROUP BY name"
    result = None
    with sql.connect("reviews.db") as db:
        cur = db.cursor()
        print(select + command)
        cur.execute(select + command)
        result = cur.fetchall()
    print(result)
    for answer in result:
        review = answer[0] + "\n"
        for i in range(len( questions[0] ) - 1):
            review +=  (questions[0][i] + (" <u><b>" + (str(round(answer[2*i + 1])) + "%" + "</b></u> (" + str(answer[2*i+2]) + ")") if answer[2*i+2]!= 0 else " нет данных") + "\n")
        bot.send_message(message.chat.id, review, parse_mode='html') 

@bot.message_handler()
def main(message: telebot.types.Message):
    if message.from_user.id not in state:
        bot.send_message(message.chat.id, "Вы ничего не запустили")
        return

bot.polling(non_stop = True) 

 

