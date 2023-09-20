import requests
from bs4 import BeautifulSoup
import time
import logging
import telebot


base_url = "https://www.marathonbet.ru"
url = "https://www.marathonbet.ru/su/live/22723/"
headers = {
    'Cookie': 'puid=rBkp8WOa9QE/vDhEAxCIAg==; lhnContact=f24a1609-f5cf-4650-b072-df22445d0f74-8102-QirYPJ5k; lhnStorageType=cookie; lhnJWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ2aXNpdG9yIiwiZG9tYWluIjoiIiwiZXhwIjoxNjczMzU0MTIxLCJpYXQiOjE2NzMyNjc3MjEsImlzcyI6eyJhcHAiOiJqc19zZGsiLCJjbGllbnQiOjgxMDIsImNsaWVudF9sZXZlbCI6ImJhc2ljIiwibGhueF9mZWF0dXJlcyI6W10sInZpc2l0b3JfdHJhY2tpbmciOnRydWV9LCJqdGkiOiJmMjRhMTYwOS1mNWNmLTQ2NTAtYjA3Mi1kZjIyNDQ1ZDBmNzQiLCJyZXNvdXJjZSI6eyJpZCI6ImYyNGExNjA5LWY1Y2YtNDY1MC1iMDcyLWRmMjI0NDVkMGY3NC04MTAyLVFpcllQSjVrIiwidHlwZSI6IkVsaXhpci5MaG5EYi5Nb2RlbC5Db3JlLlZpc2l0b3IifX0.zxDOrEF-NbXtTs0H6CHm32w21jen307ZXhSXoXH_xp8; lhnRefresh=34d44483-0455-4fc8-a35d-e0ecb534e2b3; SESSION_KEY=25ecdf61575e4dfc9b199b8626863c49',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
}

bot = telebot.TeleBot(token='6315871029:AAFSj1iBRtszJqT0FtryVltXQV6FfX4Unjk')
users = [310403765, 896182229]


def find_match(find):
    result = dict()
    finded = dict()
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    sportname = soup.find('a', 'sport-category-label')
    if not sportname or sportname.text != 'Теннис':         # если сейчас нет игр в категории "Теннис"
        time.sleep(70)
        return result, finded
    
    championships = soup.find_all("div", "category-container")          # находим соревнования
    if championships == None:                                           # если нет соревнований
        time.sleep(55)
        return result, finded
    
    for championship in championships:
        games = championship.find_all("div", "bg coupon-row")           # находим матчи в соревновании
        for game in games:
            game_place = game.find("div", "cl-left red")                # здесь находится счет
            if not game_place:                                          # если счета нет - игра не началась
                continue

            game_name = game.attrs["data-event-name"]
            score1, score2 = set_calc(game_place.text.strip())          # получаем счет
            if score1 is False:                                         # если это не первый сет и получили False
                if game_name in find.keys():                            # если отслеживаем результат этой игры
                    finded[game_name] = game_place.text.strip().split(' ')[0]   # записываем счет
                continue

            champoinship_name = championship.h2.text
            command1 = game_name[:game_name.find(' - ')].strip()
            command2 = game_name[game_name.find(' - ')+2:].strip()
            
            link_ = game.find("div", "live-today-member-name nowrap")
            k1_ = game.find("td", "price height-column-with-price first-in-main-row coupone-width-1")
            k2_ = game.find("td", "price height-column-with-price coupone-width-1")
            if k1_ == None or k2_ == None or link_ == None:
                continue
            link = base_url + link_.a.attrs["href"]
            k1 = float(k1_.text.strip())
            k2 = float(k2_.text.strip())
            
            indicators = game.find_all('div', 'sport-indicator')        # в этом div должна находиться картинка жирной точки, обозначающая подачу
            if not indicators:                                          # если счёт отображается, но игра ещё не началась и контейнера для точки нет
                continue
            indicator1, indicator2 = bool(indicators[0].img), bool(indicators[1].img)            
            result[game_name] = {'champoinship_name': champoinship_name, 'link': link,
                                 command1: [score1, indicator1, k1], command2: [score2, indicator2, k2]}
            support_log.debug(f'Нашли матч со счетом 0:0: {result[game_name]}')
    return result, finded


def main():
    searched_matches = dict()
    matchs, _ = find_match(searched_matches)
    while True:
        time.sleep(25)
        now_matchs, finded_matchs = find_match(searched_matches)        # парсим новые матчи
        for match in finded_matchs.keys():                              # перебираем информацию об оконченных сетах
            score1, score2 = get_score(finded_matchs[match])
            support_log.debug(f'Закончился матч: {match}, {finded_matchs[match]}')
            winner = 1 if score1 > score2 else 0                        # получаем победителя
            if winner and match.startswith(searched_matches[match]['bid']) or not(winner) and match.endswith(searched_matches[match]['bid']):
                print(searched_matches[match], 'ПОБЕДА')
                main_log.info(f'ПОБЕДА: {searched_matches[match]}')
                support_log.info(f'ПОБЕДА: {searched_matches[match]}')
                send_massages(f'ПОБЕДА: {match}\n{searched_matches[match]["champoinship_name"]}')
            else:
                print(searched_matches[match], 'ПРОИГРЫШ')
                main_log.info(f'ПРОИГРЫШ: {searched_matches[match]}')
                support_log.info(f'ПРОИГРЫШ: {searched_matches[match]}')
                send_massages(f'ПРОИГРЫШ: {match}\n{searched_matches[match]["champoinship_name"]}')
            del searched_matches[match]
        
        if not now_matchs:                                              # если не находим новых матчей - спим 30 сек
            time.sleep(30)
            continue
        for match in matchs.keys():                                     # перебираем все матчи
            if not match in now_matchs.keys():                          # если такого матча не нашли - удаляем его из массива
                continue
            
            commands = list(now_matchs[match].keys())                   # получаем список команд (их 2)
            commands.remove('champoinship_name')
            commands.remove('link')
            
            if now_matchs[match][commands[0]][1] == matchs[match][commands[0]][1]:   # если подача не завершилась
                continue
            
            old, new = matchs[match], now_matchs[match]
            if old[commands[0]][1] and (old[commands[0]][0] == new[commands[0]][0]): # если подавал первый игрок и его счёт не изменился (не подал)
                searched_matches[match] = old                                        # отслеживаем этот матч, "делаем ставку"
                searched_matches[match]['bid'] = commands[1]
                main_log.info(f'Ставка на команду 2: {matchs[match]}')
                support_log.info(f'Ставка на команду 2: {matchs[match]}')
                send_massages(f'{match}\n{matchs[match]["champoinship_name"]}\n' \
                              f'{commands[0]}: {matchs[match][commands[0]][0]}, {matchs[match][commands[0]][2]}\n' \
                              f'{commands[1]}: {matchs[match][commands[1]][0]}, {matchs[match][commands[1]][2]}\n' \
                              f'Ставка на команду 2\n{matchs[match]["link"]}')
                del now_matchs[match]
            elif old[commands[1]][1] and (old[commands[1]][0] == new[commands[1]][0]):
                searched_matches[match] = old
                searched_matches[match]['bid'] = commands[0]
                main_log.info(f'Ставка на команду 1: {matchs[match]}')
                support_log.info(f'Ставка на команду 1: {matchs[match]}')
                send_massages(f'{match}\n{matchs[match]["champoinship_name"]}\n' \
                              f'{commands[0]}: {matchs[match][commands[0]][0]}, {matchs[match][commands[0]][2]}\n' \
                              f'{commands[1]}: {matchs[match][commands[1]][0]}, {matchs[match][commands[1]][2]}\n' \
                              f'Ставка на команду 1\n{matchs[match]["link"]}')
                del now_matchs[match]
        matchs = dict()
        for match in now_matchs.keys():                                 # очищаем матчи, заполняем заново
            if not match in searched_matches.keys():
                commands = list(now_matchs[match].keys())
                commands.remove('champoinship_name')
                commands.remove('link')
                val1, ind1 = now_matchs[match][commands[0]][0], now_matchs[match][commands[0]][1]
                val2, ind2 = now_matchs[match][commands[1]][0], now_matchs[match][commands[1]][1]
                if (ind1 and [val1, val2] in [[5, 4], [5, 3]]) or (ind2 and [val2, val1] in [[5, 4], [5, 3]]):
                    support_log.info(f'Отслеживаем матч: {match}')
                    matchs[match] = now_matchs[match]
        

def set_calc(string):
    ''' по входной строке вычисляет, какой сейчас тайм
        возвращает (счет1, счет2), если первый тайм
        (False, False) если не первый '''
    count = string.count('(')               # получаем кол-во скобочек в строке
    if count == 0:                          # если их вообще нет - то это первый сет. возвразаем счет
        return get_score(string)
    elif count == 1 and not ',' in string:  # если в строке одна скобка и нет запятых - возвращаем счет до скобки
        return get_score(string[:string.find('(')-1])
    return False, False                     # если 2 скобки или одна скоба с запятыми - возвращаем False, это точно не первый сет


def get_score(string):
    ''' получает на вход строку вида "5:6", возвращает - два числа '''
    splited = [int(i.strip()) for i in string.split(':')]
    return splited[0], splited[1]


def send_massages(text):
    for uid in users:
        try:
            bot.send_message(uid, text)
        except:
            pass


if __name__ == "__main__":
    main_log = logging.getLogger('1')
    main_log.setLevel(logging.INFO)
    FH_main = logging.FileHandler("main_log.log")
    basic_format_main = logging.Formatter('%(asctime)s: [%(levelname)s]: %(message)s')
    FH_main.setFormatter(basic_format_main)
    main_log.addHandler(FH_main)

    support_log = logging.getLogger('2')
    support_log.setLevel(logging.DEBUG)
    FH_support = logging.FileHandler("support_log.log")
    basic_format_support = logging.Formatter('%(asctime)s: [%(levelname)s]: %(message)s')
    FH_support.setFormatter(basic_format_support)
    support_log.addHandler(FH_support)
    
    main()

