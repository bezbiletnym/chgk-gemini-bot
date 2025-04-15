import time
import os, telepot

import dotenv
from google import genai
from questions import question_getter
from telepot.loop import MessageLoop
from telepot.delegate import per_chat_id, create_open, pave_event_space

dotenv.load_dotenv()

token = os.getenv('AUTHORIZATION_TOKEN')

genai_client = genai.Client(api_key=os.getenv("API_KEY"))

prompt = f"""
    Привет! Ты — тренер по игре Что?Где?Когда?
    Я буду отправлять тебе вопросы в формате JSON.
    Когда я пришлю вопрос, задай мне его, отправив содержимое поля "text"
    Пожалуйста, не меняй ничего в тексте вопроса и не раскрывай ответ (поле "answer"), пока я не попрошу.
    Перед выводом вопроса выведи значение поля "endDate" с подписью "дата", название пакета (поле "packTitle") и номер вопроса из поля "number".
    Если поля "razdatkaText" не пусто, перешли мне его точное содержимое с подписью "РАЗДАТОЧНЫЙ МАТЕРИАЛ."
    Если поле "razdatkaPic" содержит ссылку, пришли эту ссылку.
    Если ты видишь ссылку, не надо пересказывать ее содержание, просто пришли ссылку.
    Переноси строку, если встречаешь '\\n' в тексте вопроса или раздаточного материала.

    Когда я буду пытаться отвечать, подскажи насколько я близко к ответу по смыслу и задай направление мысли, но не раскрывай его.
    Если мой ответ есть в поле "zachet", его можно засчитать.
    Если я отвечу правильно (как в поле "answer" или попрошу назвать ответ, помимо полей "answer", "zachet" и "answerPic" воспроизведи содержимое полей "comment" и "commentPic" с подписью "Комментарий:" (если они не пустые)
    Поле "answer" обязательно выводи с подписью "ОТВЕТ:"
    Если я ответил правильно, в начале сообщения напиши об этом, но все равно выведи поле answer с подписью "ОТВЕТ:"
    
    Если ты все понял, в ответ на это сообщение напиши "Начинаем тренировку. Жду команду"
    Просить следующий вопрос не надо, я пришлю его сам.

    """

class Handler(telepot.helper.ChatHandler):
    def send_message_to_genai(self, message: str):
        if message == prompt:
            print(f"User {self.chat_id} started session")
        else:
            print(f"User {self.chat_id} sent message: {message}")
        try:
            response = self.genai_chat.send_message(message=message)
            print(f"Genai response to {self.chat_id}: {str(response.text)}")
            if "ОТВЕТ:" in str(response.text):
                self.question_is_answered = True
            self.sender.sendMessage(str(response.text))
        except Exception as err:
            print(repr(err))
            self.sender.sendMessage(f"Упс! Что-то сломалось. Попробуй отправить сообщение еще раз.\n{repr(err)}")

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        print(f"Connected user {self.chat_id}")
        self.sender.sendMessage('Начинаю новую сессию...')
        self.genai_chat = genai_client.chats.create(model="gemini-2.0-flash")
        self.send_message_to_genai(message=prompt)
        self.question_counter = 0
        self.current_question = {}
        self.question_is_answered = False

    def restart_ai_session(self):
        self.sender.sendMessage('Рестарт сессии...')
        self.genai_chat = genai_client.chats.create(model="gemini-2.0-flash")
        self.send_message_to_genai(message=prompt)

    def on_new_question(self, question: dict):
        self.question_counter += 1
        self.current_question = question
        self.question_is_answered = False

    def open(self, initial_msg, seed):
        return True  # prevent on_message() from being called on the initial message

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type != 'text':
            self.sender.sendMessage('Пожалуйста, отправь текст')
            return

        text = msg.get('text')
        message_to_genai = text
        if text == '/next':
            question = question_getter.get_random_question(max_number=int(os.getenv("MAX_ID", 500000)))
            self.on_new_question(question)
            message_to_genai = str(question)
        elif text == '/next_give':
            self.sender.sendMessage('Поиск вопроса с раздаткой может занять некоторое время...')
            question = question_getter.get_random_question(max_number=int(os.getenv("MAX_ID", 500000)), razdatka=True)
            self.on_new_question(question)
            message_to_genai = str(question)
        elif text == '/restart_ai':
            self.restart_ai_session()
            return
        self.send_message_to_genai(message=message_to_genai)

    def on__idle(self, event):
        last_message = (f'Сессия закончена. Отправь любое сообщение, чтобы начать новую.\n'
                        f'Вопросов сыграно: {self.question_counter}')
        if not self.question_is_answered:
            last_message += f"\n\nОтвет на последний вопрос: {self.current_question.get('answer')}"
            if self.current_question.get('answerPic'):
                last_message += f"\n{self.current_question.get('answerPic')}"
            if self.current_question.get('comment'):
                last_message += f"\nКомментарий: {self.current_question.get('comment')}"
            if self.current_question.get('commentPic'):
                last_message += f"\n{self.current_question.get('commentPic')}"
        self.sender.sendMessage(last_message)
        self.close()

TOKEN = os.getenv('AUTHORIZATION_TOKEN')

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, Handler, timeout=300),
])
MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
