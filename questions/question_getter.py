import random
from time import sleep

import requests
from questions import question_parser

question_api_url = 'https://gotquestions.online/api/question/'
site_url = 'https://gotquestions.online'
headers = {'Content-Type': 'application/json'}

def complete_pic_urls(json_data: dict) -> dict:
    new_data = {}
    pic_keys = ['razdatkaPic', 'answerPic', 'commentPic']
    for pic_key in pic_keys:
        if json_data.get(pic_key):
            new_data.update({
                pic_key: site_url + json_data.get(pic_key)
            })
    return new_data


def get_question_by_id(question_id: int):
    try:
        print(f"Getting a question with id {question_id}...")
        #response = requests.get(url=question_api_url + str(question_id), headers=headers)
        #question_json = response.json()
        # is temporarily disabled until getting access to API

        question_json = question_parser.open_question_by_id(id=question_id)
        question_json.update(complete_pic_urls(question_json))
        return question_json
    except Exception as err:
        print(repr(err))
        return {}

def get_random_question(max_number: int, razdatka:bool = False, max_retries:int = 10):
    question = {}
    for i in range(max_retries):
        question_id = random.randint(1, max_number)
        question = get_question_by_id(question_id=question_id)
        if not question.get("audio") and question.get("text") and question.get("endDate"):
            # try again if a question has audio or a question not found (404 questions don't have endDate)
            #if razdatka and (question.get('razdatkaPic') or question.get('razdatkaText')):
                # searching for a question with razdatka
                #break
            #elif not razdatka:
                #break
            return question # Razdatka is temporarily disabled until getting access to API
        print(f"Let's try again")
        sleep(1)
    return question


