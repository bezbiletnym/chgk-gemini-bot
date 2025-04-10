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
    Если поля "razdatkaText" и "razdatkaPic" не пусты, пришли мне их точное содержимое с подписью "РАЗДАТОЧНЫЙ МАТЕРИАЛ."
    Если ты видишь ссылку, не надо пересказывать ее содержание, просто пришли ссылку.
    Переноси строку, если встречаешь '\\n' в тексте вопроса.

    Когда я буду пытаться отвечать, подскажи насколько я близко к ответу по смыслу и задай направление мысли, но не раскрывай его.
    Если мой ответ есть в поле "zachet", его можно засчитать.
    Если я отвечу правильно или попрошу назвать ответ, помимо полей "answer" и "answerPic" воспроизведи содержимое полей "comment" и "commentPic" с подписью "Комментарий:" (если они не пустые)
    
    Если ты все понял, в ответ на это сообщение напиши "Начинаем тренировку"

    """

class Handler(telepot.helper.ChatHandler):
    def send_message_to_genai(self, message: str):
        try:
            print('sending to genai...')
            response = self.genai_chat.send_message(message=message)
            print(f"genai response: {str(response.text)}")
            self.sender.sendMessage(str(response.text))
        except Exception as err:
            print(repr(err))

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.sender.sendMessage('Начинаю новую сессию...')
        self.genai_chat = genai_client.chats.create(model="gemini-2.0-flash-lite")
        self.send_message_to_genai(message=prompt)

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
            message_to_genai = str(question)
        elif text == '/next_give':
            self.sender.sendMessage('Поиск вопроса с раздаткой может занять некоторое время...')
            question = question_getter.get_random_question(max_number=int(os.getenv("MAX_ID", 500000)), razdatka=True)
            message_to_genai = str(question)
        self.send_message_to_genai(message=message_to_genai)

    def on__idle(self, event):
        self.sender.sendMessage(f'Сессия закончена. Отправь любое сообщение, чтобы начать новую')
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
