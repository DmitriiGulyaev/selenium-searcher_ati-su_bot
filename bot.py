import time

import telebot
from telegram import ParseMode
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Edge(options=options)

users = [161296982]
API_KEY = open("token.txt", "r").read()
bot = telebot.TeleBot(API_KEY)
indent = '          '
indent_city = '   '


def send_all(line):
    for i in users:
        bot.send_message(chat_id=i, text=line)


def check_lst(lst):
    for i in lst:
        if i is not None:
            return True
    return False


def check_none(elm, prs=None, h=None):
    h = True if h is not None else False
    prs = prs if prs is not None else False
    if prs:
        prs += f':\n{indent}' if h else ': '
    return (('' if h == 1 else indent) + ('' if prs is None else prs) + f"{elm}\n") if elm is not None else ''


def send_pretty_info(di):
    line = str()

    d = di['direction']
    if check_lst(d):
        line_d = f"<b>Направление:\n</b>" \
                 + check_none(d['distance'], 'расстояние') \
                 + check_none(d['route'], 'маршрут')
        line += line_d

    t = di['transport']
    if check_lst(t):
        line_t = f"<b>Транспорт:\n</b>" \
                 + check_none(t['type'], 'тип') \
                 + check_none(t['orientation'], 'загр/выгр')
        line += line_t

    if di['cargo'] is not None:
        line_c = check_none(di['cargo'], '<b>Вес,т / объём,м³, груз</b>', 1)
        line += line_c

    for i in ('loading', 'unloading'):
        u = di[i]
        if check_lst(u):
            line_u = (f"<b>Погрузка:\n</b>" if i == 'loading' else f"<b>Разгрузка:\n</b>") \
                     + check_none(u['city'], 'г') \
                     + check_none(u['region'], 'рег.') \
                     + f"<i>{check_none(u['nearest_cities'], 'ближ.города')}</i>" \
                     + check_none(u['date'], 'дата')
            line += line_u

    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(di['direction']['route'], url=di['link_info']))
    for i in users:
        bot.send_message(chat_id=i, parse_mode=ParseMode.HTML, text=line, reply_markup=markup)


def get_pretty_info_d(d):
    if d['transport']['orientation'] is not None:
        d['transport']['orientation'] = d['transport']['orientation'][-1]
    if d['cargo'] is not None:
        d['cargo'] = f"{indent}" + ' '.join(d['cargo'])

    for i in d:
        if isinstance(d[i], dict):
            for j in d[i]:
                if isinstance(d[i][j], list):
                    if len(d[i][j]) == 1:
                        d[i][j] = d[i][j][0]
                    else:
                        d[i][j] = ' '.join(d[i][j])
        elif isinstance(d[i], list):
            d[i] = ' '.join(d[i])

    for i in ('loading', 'unloading'):
        if d[i]['nearest_cities'] is not None:
            if d[i]['nearest_cities'].count(' км') != 3:
                d[i]['nearest_cities'] = None
            else:
                d[i]['nearest_cities'] = f"\n{indent}{indent_city}" + d[i]['nearest_cities'].replace(' км ', f' км\n{indent}{indent_city}')
    send_pretty_info(d)


def get_info(id_load, html):
    info_json = {
        'direction': {'pr_soup': '_3TPf3 yopdr', 'location': '_2V8wZ', 'distance': '_1yVto', 'route': '_13eVH'},
        'transport': {'pr_soup': '_3TPf3 _1EqYq', 'type': '_3qUC2', 'orientation': '_2wVDu', 'description': '_3Tp_t', },
        'cargo': '_1o_ZY',
        'loading': {'pr_soup': '_3TPf3 huFkH', 'city': '_15Q0N HptCF', 'region': '_2Mm7H',
                    'nearest_cities': 'glz-tooltiptext', 'date': '_35iFG _1V6yy'},
        'unloading': {'pr_soup': '_3TPf3 _3tY-M', 'city': '_15Q0N HptCF', 'region': '_2Mm7H',
                      'nearest_cities': 'glz-tooltiptext', 'date': '_35iFG _1V6yy'},
    }
    soup = BeautifulSoup(str(BeautifulSoup(html, 'lxml').select(f'div[data-load-id="{id_load}"]')), 'lxml')

    for key in info_json:

        if type(info_json[key]) == dict:

            pr_soup = soup.find(class_=info_json[key]['pr_soup'])
            info_json[key].pop('pr_soup')

            for ki in info_json[key]:
                info_json[key][ki] = pr_soup.find(class_=info_json[key][ki])
                if info_json[key][ki] is not None:
                    info_json[key][ki] = info_json[key][ki].find_all(text=True)

        elif type(info_json[key]) == str:
            info_json[key] = soup.find(class_=info_json[key]).find_all(text=True)

    t = info_json['transport']
    for i in (t['type'] if isinstance(t['type'], list) else []) + (t['orientation'] if isinstance(t['orientation'], list) else []):
        t['description'].remove(i)

    info_json['link_info'] = 'https://loads.ati.su/loadinfo/' + id_load

    get_pretty_info_d(info_json)


def get_last_id_load(html):
    return BeautifulSoup(html, 'lxml').find(class_='_3QU4W').parent.parent.get('data-load-id')


def get_source_html(url):
    send_all('Бот запущен')
    driver.get(url=url)
    time.sleep(5)
    html = driver.page_source

    old_id = get_last_id_load(html)
    print("old_id:", old_id)
    get_info(old_id, html)

    while True:
        time.sleep(3)
        driver.execute_script('document.querySelector("#__next > div > main > div.main_search__Y3rwv > div > '
                              'div:nth-child(3) > div.Sticky_container___lIp6 > div.Sticky_action__6I_3Q > '
                              'button").click()')
        print(time.asctime(time.localtime(time.time())), end='')
        html = driver.page_source
        new_id = get_last_id_load(html)
        print(" | ", new_id, "==", old_id, end="")

        if new_id != old_id:
            print(" | TRUE")
            old_id = new_id
            get_info(old_id, html)
        else:
            print(" | FALSE")


def time_out():
    start_time = time.time()
    try:
        get_source_html(link)
    except KeyboardInterrupt:
        send_all(
            f'Бот проработал {int((time.time() - start_time) // 1 // 60)}.{int((time.time() - start_time) // 1 % 60)} минут\nПриостановлен Администратором')
    except Exception:
        send_all(
            f'ОШИБКА!\nБот проработал {int((time.time() - start_time) // 1 // 60)}.{int((time.time() - start_time) // 1 % 60)} минут\nПрофилактика бота составит 5 минут')
        time.sleep(300)
        time_out()


link = 'https://loads.ati.su/#?filter=%7B%22exactFromGeos%22:true,%22fromList%22:%7B%22id%22:%229f654ef8-e210-e311-b4ec-00259038ec34%22,%22name%22:%22%D0%A1%D0%B5%D0%B2%D0%B5%D1%80%D0%BE-%D0%9A%D0%B0%D0%B2%D0%BA%D0%B0%D0%B7%D1%81%D0%BA%D0%B8%D0%B9%20%D1%84%D0%B5%D0%B4.%20%D0%BE%D0%BA%D1%80%D1%83%D0%B3%22,%22type%22:0%7D,%22exactToGeos%22:true,%22toList%22:%7B%22id%22:%22df6866d7-1ce7-e711-b46b-002590e45781%22,%22name%22:%22%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%20+%20%D0%9C%D0%BE%D1%81%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B0%D1%8F%20%D0%BE%D0%B1%D0%BB%D0%B0%D1%81%D1%82%D1%8C%22,%22type%22:0%7D,%22firmListsExclusiveMode%22:false,%22dateFrom%22:%222022-08-13%22,%22dateOption%22:%22manual%22,%22withAuction%22:false%7D'
# get_source_html(link)
time_out()
