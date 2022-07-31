import job
import requests
from bs4 import BeautifulSoup
import csv


def write_csv(result):
    with open('file.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['ser=,'])
        for item in result:
            writer.writerow((item['name'],
                             item['price'],
                             item['description'],
                             item['author'],
                             item['business_or_private'],
                             item['phone_number'],
                             item['url']
                             ))


def clean(text):
    return text.replace('\t', '').replace('\n', '').strip()


def get_phone():
    return 'null'


def get_item_data(item_url):
    print(item_url)
    r = requests.get(item_url)
    soup = BeautifulSoup(r.content)
    result = []
    name = clean(soup.find('h1', {'class': 'css-r9zjja-Text eu5v0x0'}).text)
    price = clean(soup.find('h3', {'class': 'css-okktvh-Text eu5v0x0'}).text)
    description = clean(soup.find('div', {'class': 'css-g5mtbi-Text'}).text)
    author = clean(soup.find('h4', {'class': 'css-1rbjef7-Text eu5v0x0'}).text)
    business_or_private = clean(soup.find('p', {'class': 'css-xl6fe0-Text eu5v0x0'}).text)
    phone_number = get_phone()
    item = {'name': name, 'price': price, 'description': description, 'author': author,
            'business_or_private': business_or_private, 'phone_number': phone_number, 'url': item_url}
    result.append(item)
    if job.print_items_data_to_terminal:
        print(item_url)
        print(name, price, author, business_or_private)
        print(description)
    return result


def get_list_data(page_url):
    r = requests.get(page_url)
    soup = BeautifulSoup(r.content)
    rows = soup.find_all('div', {'class': 'css-19ucd76'})
    counter = 1
    result = []
    for row in rows:
        print('Parsing item ', str(counter), ' of ', str(len(rows)))
        url = row.find('a')
        if url:
            url = url.get('href')
            full_url = 'https://olx.ua' + url
        else:
            continue
        print(full_url)
        result += get_item_data(full_url)
        counter += 1
    return result


def main(main_url, number_of_pages):
    r = requests.get(main_url)
    soup = BeautifulSoup(r.content)
    result = []
    for i in range(1, number_of_pages + 1):
        print('Parsing page ', str(i), ' of ', str(number_of_pages))
        page_url = main_url + '?page=' + str(i)
        print(page_url)
        result += get_list_data(page_url)
    write_csv(result)


if __name__ == '__main__':
    main(job.main_url, job.number_of_pages)
