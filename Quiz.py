import json
import random
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from token_gen import token


# states
class Mode(StatesGroup):
    admin_check = State()
    admin1 = State()
    admin2 = State()


class Game(StatesGroup):
    asking = State()
    answering = State()


class Add(StatesGroup):
    question = State()
    ans1 = State()
    ans2 = State()
    ans3 = State()
    ans4 = State()


# bot init
bot = Bot(token=token())
dp = Dispatcher(bot, storage=MemoryStorage())

# data receiving
with open('questions.json', 'r', encoding='utf-8') as file_q:
    questions = json.load(file_q)
with open('answers.json', 'r', encoding='utf-8') as file_a:
    answers = json.load(file_a)

usr_q, usr_a = [], []
password = 'qwerty'
counter = 0
current_question = {}
anti_repeat = {}


# navigation buttons
async def buttons(names):
    button_list = ReplyKeyboardMarkup(resize_keyboard=True)
    for button in names:
        button_list.add(button)
    return button_list


# bot start
@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message):
    ans = "Привет!\n" \
          "Это - бот с квизами про Манчестер Юнайтед.\n" \
          "Нажмите /question, чтобы получить вопрос.\n" \
          "/help - вызов справки. Обязательно прочитай справку, чтобы понять, когда работают команды.\n" \
          "/add - добавить вопрос."
    names = ['/question', '/help', '/add']
    button_list = await buttons(names)
    await message.answer(ans, reply_markup=button_list)


# bot restart
@dp.message_handler(commands=['restart'], state='*')
async def restart(message: types.Message, state: FSMContext):
    ans = 'Перезапускаю бота'
    await state.finish()
    names = ['/question', '/help']
    button_list = await buttons(names)
    await message.answer(ans, reply_markup=button_list)


# admin mode
@dp.message_handler(commands=['admin'], state='*')
async def admin_mode(message: types.Message):
    await message.answer('Введите пароль:', reply_markup=ReplyKeyboardRemove())
    await Mode.admin_check.set()


@dp.message_handler(state=Mode.admin_check)
async def check_password(message: types.Message, state: FSMContext):
    if message.text == password:
        ans = 'Добро пожаловать в режим администратора!\n' \
              'Введите /mod, чтобы модерировать пользовательские вопросы.'
        await message.answer(ans, reply_markup=ReplyKeyboardRemove())
        global usr_a, usr_q
        checker = os.stat('user_questions.json')
        if checker.st_size:
            with open('user_questions.json', 'r', encoding='utf-8') as file_u:
                user_questions = json.load(file_u)
            for current_q, current_answer in user_questions.items():
                usr_q.append(current_q)
                usr_a.append(current_answer)
            await Mode.admin1.set()
        else:
            await message.answer('Вопросов на модерацию нет, выхожу из режима администратора', reply_markup=ReplyKeyboardRemove())
            await state.finish()
    else:
        await message.answer('Некорректный пароль, еще попытка - /admin.', reply_markup=ReplyKeyboardRemove())
        await state.finish()


@dp.message_handler(commands=['mod'], state=Mode.admin1)
async def moderating(message: types.Message, state: FSMContext):
    global usr_a, usr_q, counter, questions, answers
    if counter == len(usr_a):
        await message.answer('Больше вопросов на модерацию нет', reply_markup=ReplyKeyboardRemove())
        await bot.send_message(338152217, 'Вопросы отмодерированы')
        os.system(r'nul>user_questions.json')
        counter = 0
        await state.finish()
        return
    await bot.send_message(message.chat.id, 'Вопрос - '
                           + usr_q[counter] + '\n'
                           'Варианты ответа - ' +
                           str(usr_a[counter]))
    counter += 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('Добавляем', 'Удаляем')
    await message.reply('Что делаем с вопросом?', reply_markup=markup)
    await Mode.admin2.set()


@dp.message_handler(state=Mode.admin2)
async def decision(message: types.Message):
    global usr_a, usr_q, counter, questions, answers
    if message.text == 'Добавляем':
        # answers[usr_q[counter - 1]] = usr_a[counter - 1][0]
        random.shuffle(usr_a[counter - 1])
        questions[usr_q[counter - 1]] = usr_a[counter - 1]
        with open('questions.json', 'w', encoding='utf-8') as file_q_rewrite:
            json.dump(questions, file_q_rewrite, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))
        with open('answers.json', 'w', encoding='utf-8') as file_a_rewrite:
            json.dump(answers, file_a_rewrite, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))
        names = ['/mod']
        button_list = await buttons(names)
        await message.answer('/mod - следующий вопрос', reply_markup=button_list)
    else:
        names = ['/mod']
        button_list = await buttons(names)
        await message.answer('/mod - следующий вопрос', reply_markup=button_list)
    await Mode.admin1.set()


# display help
@dp.message_handler(commands=['help'], state='*')
async def process_help_command(message: types.Message, state: FSMContext):
    await state.finish()
    ans = "Вопросы могут повторяться. Чем больше вопросов Вы предлагаете," \
          " тем меньше шанс повторений!\nЗаранее спасибо за контент!\n" \
          "Бот будет совершенствоваться!\n" \
          "/question - случайный вопрос.\n" \
          "/add - добавить свой вопрос. Добавление вопросов доступно только" \
          " после того, как дан ответ на текущий вопрос.\n" \
          "Заметил баг - пиши @insane_myrr\n" \
          "Если бот не работает, пробуйте команду /restart."
    names = ['/question', '/add']
    button_list = await buttons(names)
    await message.answer(ans, reply_markup=button_list)


# question asking
@dp.message_handler(commands=['question'], state=None)
async def start_question_mode(message: types.Message):
    global anti_repeat
    ans = 'Внимание, вопрос!\n' \
          'Если что-то не работает, может помочь команда /restart.'
    if str(message.chat.id) not in anti_repeat.keys():
        anti_repeat[str(message.chat.id)] = []
    await message.answer(ans, reply_markup=ReplyKeyboardRemove())
    await Game.asking.set()
    await question_mode(message)


@dp.message_handler(state=Game.asking)
async def question_mode(message: types.Message):
    global current_question, anti_repeat
    generated = random.choice(list(questions.keys()))
    while generated in anti_repeat[str(message.chat.id)]:
        generated = random.choice(list(questions.keys()))
    current_question[str(message.chat.id)] = random.choice(list(questions.keys()))
    if len(anti_repeat[str(message.chat.id)]) <= 5:
        anti_repeat[str(message.chat.id)].append(current_question[str(message.chat.id)])
    else:
        anti_repeat[str(message.chat.id)][-1] = current_question[str(message.chat.id)]
    button_list = await question_asking(current_question[str(message.chat.id)])
    await message.answer(current_question[str(message.chat.id)], reply_markup=button_list)
    await Game.answering.set()


async def question_asking(random_question):
    button_list = ReplyKeyboardMarkup(resize_keyboard=True)
    # print(random_question)
    temp = questions[random_question]
    random.shuffle(temp)
    for answer in temp:
        button_list.add(answer)
    return button_list


@dp.message_handler(state=Game.answering)
async def question_answering(message: types.Message, state: FSMContext):
    global current_question
    if message.text == '/next':
        ans = answers[current_question[str(message.chat.id)]]
        await message.answer('Ответ на предыдущий вопрос - ' + ans + ''
                                                                     '\n/question - следующий вопрос.',
                             reply_markup=ReplyKeyboardRemove())
        await state.finish()
    else:
        print(current_question)
        answer = message.text
        if answer == answers[current_question[str(message.chat.id)]]:
            ans = 'Верно!\n' \
                  '/question - следующий вопрос.\n' \
                  'Если что-то не работает, может помочь команда /restart.'
            names = ['/question', '/help']
            button_list = await buttons(names)
            await state.finish()
        else:
            ans = 'Жаль, но это неправильный ответ, попробуйте ответить еще раз.\n' \
                  'Если Вы хотите получить другой вопрос, нажмите /next\n' \
                  'Если что-то не работает, может помочь команда /restart.'
            button_list = await question_asking(current_question[str(message.chat.id)])
            button_list.add('/next')
        await message.answer(ans, reply_markup=button_list)


# add user question
@dp.message_handler(commands=['add'], state=None)
async def start_asking(message: types.Message):
    await message.answer('Введите вопрос.\n'
                         'ПЕРВЫЙ ВАРИАНТ ОТВЕТА ДОЛЖЕН БЫТЬ ВЕРНЫМ, ОСТАЛЬНЫЕ НЕТ.\n'
                         '/exit - выход из режима добавления вопроса',
                         reply_markup=ReplyKeyboardRemove())
    await Add.question.set()


@dp.message_handler(state=Add.question)
async def add_question(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        ans = 'Выхожу из режима добавления вопроса.'
        await state.finish()
        names = ['/question', '/help']
        button_list = await buttons(names)
        await message.answer(ans, reply_markup=button_list)
    else:
        answer = message.text
        async with state.proxy() as data:
            data['question'] = answer
        await message.answer('Введите верный вариант ответа\n'
                             '/exit - выход из режима добавления вопроса', reply_markup=ReplyKeyboardRemove())
        await Add.next()


@dp.message_handler(state=Add.ans1)
async def add_ans1(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        ans = 'Выхожу из режима добавления вопроса.'
        await state.finish()
        names = ['/question', '/help']
        button_list = await buttons(names)
        await message.answer(ans, reply_markup=button_list)
    else:
        answer = message.text
        async with state.proxy() as data:
            answers[data['question']] = answer
            data['ans1'] = answer
        await message.answer('Введите неправильный вариант ответа 1\n'
                             '/exit - выход из режима добавления вопроса', reply_markup=ReplyKeyboardRemove())
        await Add.next()


@dp.message_handler(state=Add.ans2)
async def add_ans1(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        ans = 'Выхожу из режима добавления вопроса.'
        await state.finish()
        names = ['/question', '/help']
        button_list = await buttons(names)
        await message.answer(ans, reply_markup=button_list)
    else:
        answer = message.text
        async with state.proxy() as data:
            data['ans2'] = answer
        await message.answer('Введите неправильный вариант ответа 2\n'
                             '/exit - выход из режима добавления вопроса', reply_markup=ReplyKeyboardRemove())
        await Add.next()


@dp.message_handler(state=Add.ans3)
async def add_ans1(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        ans = 'Выхожу из режима добавления вопроса.'
        await state.finish()
        names = ['/question', '/help']
        button_list = await buttons(names)
        await message.answer(ans, reply_markup=button_list)
    else:
        answer = message.text
        async with state.proxy() as data:
            data['ans3'] = answer
        await message.answer('Введите неправильный вариант ответа 3\n'
                             '/exit - выход из режима добавления вопроса', reply_markup=ReplyKeyboardRemove())
        await Add.next()


@dp.message_handler(state=Add.ans4)
async def add_ans4(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        ans = 'Выхожу из режима добавления вопроса.'
        await state.finish()
        names = ['/question', '/help']
        button_list = await buttons(names)
        await message.answer(ans, reply_markup=button_list)
    else:
        answer = message.text
        async with state.proxy() as data:
            data['ans4'] = answer
        checker = os.stat('user_questions.json')
        if checker.st_size:
            with open('user_questions.json', 'r', encoding='utf-8') as file_u:
                user_questions = json.load(file_u)
            user_questions[data['question']] = [data['ans1'], data['ans2'], data['ans3'], data['ans4']]
        else:
            user_questions = {data['question']: [data['ans1'], data['ans2'], data['ans3'], data['ans4']]}
        with open('user_questions.json', 'w', encoding='utf-8') as file_u:
            json.dump(user_questions, file_u, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))
        names = ['/question', '/add', '/help']
        button_list = await buttons(names)
        await message.answer("Спасибо за ваши ответы!", reply_markup=button_list)
        await bot.send_message(338152217, 'Добавлен новый вопрос')
        await state.finish()


# antispam and communication
@dp.message_handler(state=None)
async def communication(message: types.Message):
    ans = 'Такой команды не существует или я сломался.\nПопробуйте вызвать справку (/help)' \
          ' или вызвать команду /restart.\n' \
          'Если Вы спамер, то спамить нехорошо.\n' \
          'Если хотите получить вопрос - назжмите /question.'
    names = ['/question', '/add', '/help']
    button_list = await buttons(names)
    await message.answer(ans, reply_markup=button_list)


# run long-polling
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)