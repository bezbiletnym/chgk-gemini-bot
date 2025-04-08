import dotenv, os, telepot
from google import genai
from flask import Flask, request
from telepot.loop import OrderedWebhook
from telepot.delegate import per_chat_id, create_open, pave_event_space
from questions import question_getter

dotenv.load_dotenv()
genai_client = genai.Client(api_key=os.getenv("API_KEY"))
genai_chat = genai_client.chats.create(model="gemini-2.0-flash")

prompt = f"""
    Привет! Ты — тренер по игре Что?Где?Когда?
    Я буду отправлять тебе вопросы в формате JSON.
    Пожалуйста, задавай мне их (вопрос содержится в поле "text").
    Пожалуйста, не меняй ничего в тексте вопроса и не раскрывай ответ (поле "answer"), пока я не попрошу.
    Перед выводом вопроса выведи значение поля "endDate" с подписью "дата".
    Если поля "razdatkaText" и "razdatkaPic" не пусты, пришли мне их точное содержимое с подписью "РАЗДАТОЧНЫЙ МАТЕРИАЛ."
    Если ты видишь ссылку, не надо пересказывать ее содержание, просто пришли ссылку.
    Переноси строку, если встречаешь '\\n' в тексте вопроса.

    Когда я буду пытаться отвечать, подскажи насколько я близко к ответу по смыслу, но не раскрывай его.
    Если мой ответ есть в поле "zachet", его можно засчитать.
    Если я отвечу правильно или попрошу назвать ответ, помимо полей "answer" и "answerPic" воспроизведи содержимое полей "comment" и "commentPic" с подписью "Комментарий:" (если они не пустые)

    """

class ChgkBot(telepot.helper.ChatHandler):
    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        match query_data:
            case 'start_ai':
                response = genai_chat.send_message(message=prompt)
                self.sender.sendMessage(response.text)
            case 'next':
                question=question_getter.get_random_question(int(os.getenv("MAX_ID", 500000)))
                response = genai_chat.send_message(message=question)
                self.sender.sendMessage(response.text)
        print('Callback query:', query_id, from_id, query_data)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        match msg['text']:
            case '/start_ai':
                response = genai_chat.send_message(message=prompt)
                self.sender.sendMessage(response.text)
            case '/next':
                question = question_getter.get_random_question(int(os.getenv("MAX_ID", 500000)))
                response = genai_chat.send_message(message=question)
                self.sender.sendMessage(response.text)
            case _:
                response = genai_chat.send_message(message=msg['text'])
                self.sender.sendMessage(response.text)

secret = os.getenv('SECRET_NUMBER')
token = os.getenv('AUTHORIZATION_TOKEN')
web_link = os.getenv('WEB_LINK')
bot = telepot.DelegatorBot(token, [
    pave_event_space()(
        per_chat_id(), create_open, ChgkBot, timeout=10),
])
webhook = OrderedWebhook(bot)
bot.setWebhook(f"{web_link}/{secret}", max_connections=1)

app = Flask(__name__)

@app.route(f'/{secret}', methods=['GET', 'POST'])
def pass_update():
    webhook.feed(request.data)
    return 'OK'