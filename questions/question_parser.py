import requests
import bs4

site_url = 'https://gotquestions.online'

def open_question_by_id(id: int):
    try:
        response = requests.get(url=f"{site_url}/question/{str(id)}")
        data = response.content
        soup = bs4.BeautifulSoup(markup=data, features="html.parser")
        questions = soup.find_all(name="script")
        for question in questions:
            if r'\"question\":' in str(question):
                raw_text = str(question)
                raw_text = raw_text.replace(r'\"', '\"')
                raw_text = raw_text.replace(',\"', ',\"\"')
                new_dict = {}
                for item in raw_text.split(",\""):
                    if "\":" in item:
                        key = item.split(':', 1)[0].strip('\"')
                        value = item.split(':', 1)[1].strip('\"')
                        value = value.replace(r"\\\\", '')
                        value = value.replace(r'\\"', '\"')
                        if (key != 'answer' or new_dict.get("answer") is None) and (key != "comment" or new_dict.get("comment") is None):
                            # To prevent appellations answers from parsing
                            new_dict.update({key: value})
                print(f"Parsed {new_dict}")
                return new_dict
        return {}
    except Exception as err:
        print(repr(err))
        return {}