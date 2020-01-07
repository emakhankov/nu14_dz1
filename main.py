import requests
from bs4 import BeautifulSoup
import json
import pandas as pd



def get_settings():

    with open("settings.json", "r") as read_file:
        data = json.load(read_file)
        return data


def create_dataframe(data, url):

    df = pd.DataFrame(data, columns=['num', 'href', 'customer', 'description', 'price', 'start', 'finish', 'state'])
    df[['start', 'finish']] = df[['start', 'finish']].apply(pd.to_datetime)
    df[['price']] = df[['price']].apply(pd.to_numeric)
    df['href'] = df['href'].apply(lambda x: f'{url}{x}')
    return df

def get_data(url, rows):
    print('gathering from:', url)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    div_id_content = soup.find('div', id='content')
    if div_id_content is None:
        print('The structure of html is broken. Missing tag <div>, id="content"')
        raise SystemExit

    div_pager = div_id_content.find('div', class_='pager')
    next_exists = False
    for a_href in div_pager.find_all('a'):
        if 'след' in a_href.text.lower():
            next_exists = True

    if next_exists:

        table_zebra = div_id_content.find('table', class_='table zebra')
        if table_zebra is None:
            print('The structure of html is broken. Missing tag <table class="table zebra">')
            raise SystemExit

        table_body = table_zebra.find('tbody')
        if table_body is None:
            print('The structure of html is broken. Missing tag <body>')
            raise SystemExit

        for tr_table_body in table_body.find_all('tr'):
            row_dict = {}
            td_table_body = tr_table_body.find_all('td')
            row_dict['num'] = td_table_body[0].a.text
            row_dict['href'] = td_table_body[0].a.get('href')

            row_dict['description'] = td_table_body[1].a.text

            row_dict['customer'] = td_table_body[2].text

            row_dict['price'] = td_table_body[3].text.replace(',', '.').replace(' ', '')

            row_dict['start'] = td_table_body[4].text

            row_dict['finish'] = td_table_body[5].text

            row_dict['state'] = td_table_body[6].text

            rows.append(row_dict)

        return False

    else:

        return True


if __name__ == '__main__':

    settings = get_settings()
    domain_url = settings['DOMAIN_URL']
    parse_url = settings['PARSE_URL']
    output_excel = settings['OUTPUT_EXCEL']


    print('start gathering info from:', f'{domain_url}{parse_url}')

    i = 0
    rows = []
    while True:
        i += 1
        return_value = get_data(f'{domain_url}{parse_url}/page/{i}', rows)
        if return_value:
            break

    df = create_dataframe(rows, domain_url)
    df.to_excel(output_excel, engine='xlsxwriter')