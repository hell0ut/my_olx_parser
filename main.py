import datetime
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re


def clean(text):
    return text.replace('\t', '').replace('\n', '').strip() or np.NAN


class OlxParser:

    def __init__(self,url,num_pages=32768):
        self.url = url
        self.max_number_of_pages = num_pages
        self.result = []
        self.session = requests.Session()
        self.cur_text = self.session.get(f'{self.url}?page={1}').text
        self.cur_soup = BeautifulSoup(self.cur_text, 'html.parser')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val and len(self.result)>0:
            self.write()

        if exc_val:
            date = datetime.datetime.now()
            with open(f'{date}_log.txt','w') as f:
                f.write(f'{exc_type},{exc_val},{exc_tb}')
            with open(f'{date}.html','w') as f:
                f.write(self.cur_text)

    def pass_pages(self):
        self.get_max_page()
        self.get_list_data()
        i = 2
        while i<self.max_number_of_pages+1:
            print('Parsing page ', str(i), ' of ', str(self.max_number_of_pages))
            page_url = f'{self.url}?page={i}'
            self.cur_text = self.session.get(page_url).text
            self.cur_soup = BeautifulSoup(self.cur_text, 'html.parser')
            self.get_list_data()
            if i%10 ==0:
                self.write()
            i+=1

    def write(self):
        df = pd.DataFrame.from_records(self.result)
        df.to_csv(f'data_{datetime.datetime.now()}.csv', index=False)
        self.result = []

    def get_max_page(self):
        uls = self.cur_soup.find('ul', {'class': 'pagination-list'}) or self.cur_soup.find('div', {'class': 'pager'})

        if uls is None:
            self.max_number_of_pages = 1
        else:
            hrefs = uls.find_all('a')

            if len(hrefs) > 0:
                pages = []
                for a in hrefs:
                    pages.extend(re.findall(r'\d+', a.text))
                pages = list(map(int, pages))
                self.max_number_of_pages = min(max(pages), self.max_number_of_pages)
            else:
                self.max_number_of_pages = 1


    def get_list_data(self):
        lcard = False
        rows = self.cur_soup.find_all('tbody')
        if len(rows) == 0:
            rows = self.cur_soup.find_all('div', {'data-cy': 'l-card'})
            lcard = True
        counter = 1
        if lcard:
            class_dict = {'class': 'css-rc5s2u'}
            pre_url = 'https://www.olx.ua'
        else:
            class_dict = {'class': 'linkWithHash'}
            pre_url = ''
        for row in rows:
            print('Parsing item ', str(counter), ' of ', str(len(rows)))
            url = row.find('a', class_dict)
            if url:
                url = pre_url + url.get('href')
                self.get_item_data(url)
            else:
                continue
            counter += 1

    def get_item_data(self,item_url):
        r = requests.get(item_url)
        soup = BeautifulSoup(r.content, "html.parser")
        name = clean(soup.find('h1', {'class': 'css-r9zjja-Text eu5v0x0'}).text)
        price = clean(soup.find('h3', {'class': 'css-okktvh-Text eu5v0x0'}).text)
        description = clean(soup.find('div', {'class': 'css-g5mtbi-Text'}).text)
        date = clean(soup.find('span', {'class': 'css-19yf5ek'}).text)
        cats = soup.find_all('li', {'data-testid': "breadcrumb-item"})
        location = [clean(el.find('a').text.split('-')[1]) for el in cats[-3:] if '-' in el.text]
        oblast, city, district = '', '', ''

        if len(location) == 3:
            oblast, city, disctrict = location
        else:
            oblast, city = location

        categories = [np.NAN] * 8
        for i, el in enumerate(cats[1:]):
            text = el.find('a').text
            if '-' in text:
                break
            categories[i] = text

        item = {'name': name, 'price': price,
                'description': description,
                'date': date, 'city': city,
                'oblast': oblast, 'district': district,
                'category0': categories[0], 'category1': categories[1],
                'category2': categories[2], 'category3': categories[3],
                'category4': categories[4], 'category5': categories[5],
                'category6': categories[6]}

        self.result.append(item)


if __name__ == '__main__':
    parse_url = 'https://www.olx.ua/d/uk/elektronika/noutbuki-i-aksesuary/noutbuki/'
    with OlxParser(parse_url) as p:
        p.pass_pages()
