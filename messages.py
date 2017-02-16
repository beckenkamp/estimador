import random


chat_responses = {}

chat_responses['error'] = [
    'Aconteceu um problema na hora de buscar as informações... =(',
    'Alguma coisa deu errado aqui... desculpe... :/',
]

chat_responses['no_answer'] = [
    'Não entendi alguma coisa... =(',
    'Desculpe, não entendi. 8)',
    'Não saquei... foi mal... ;(',
]

chat_responses['pick-a-place'] = [
    'Por favor, escolha um local para continuarmos! :)',
    'Use o botão abaixo para escolher um local! Só assim posso lhe dar a estimativa =)',
]


chat_responses['location-button'] = [
    'Agora escolha o destino! :)',
    'Use o botão abaixo para escolher para onde você vai! =)',
]


chat_responses['greetings'] = [
    'Oi, tudo bem? Vamos estimar uma viagem?',
    'Oie! Tá querendo saber quanto custa um rolê?',
    'Olá! Quer saber quanto vai custar aquele passeio?',
    'Oi! Será que tá caro sair por aí?',
    'Oi! Quer saber quanto custo uma trip?',
    'Oie! Vamos ver quanto está custonado uma saidela?',
]

chat_responses['thanks'] = [
    'De nada! 8)',
    'Eu agradeço. <3',
    'Que isso? Só estou fazendo meu trabalho :)',
]

chat_responses['good-bye'] = [
    'Volte quando quiser! :D',
    'Tchau-tchau! 8)',
]

chat_responses['estimate'] = [
    'Estimativas:{}',
]


def get_message(response_type):
    """
    Return a random string message from a given type
    """
    if response_type in chat_responses:
        return random.choice(chat_responses[response_type])
    return random.choice(chat_responses['no_answer'])


chat_keywords = {}

chat_keywords['greetings'] = [
    'oi',
    'olá',
    'ola',
    'hello',
    'e ai',
    'hey',
    'hi',
    'bom dia',
    'boa tarde',
    'boa noite',
    'eae'
]

chat_keywords['good-bye'] = [
    'tchau',
    'até mais',
    'ate mais',
    'partiu',
    'fui',
    'bye',
    'bye bye',
    'bye-bye',
    'ate logo',
    'até logo',
]

chat_keywords['thanks'] = [
    'obrigado',
    'valeu',
    'thank',
]


def search_keyword(raw_text):
    """
    Search for a keyword on a text and returns the right message
    """
    for key, word_list in chat_keywords.items():
        for word in word_list:
            if word in raw_text.lower():
                return get_message(key)
    return None
