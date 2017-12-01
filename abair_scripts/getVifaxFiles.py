import requests
from bs4 import BeautifulSoup

url = "http://vifax.maynoothuniversity.ie/cartlann/sport/"

r = requests.get(url)
html_doc = r.text

soup = BeautifulSoup(html_doc, 'html.parser')

print(soup)

print(soup.title)


for link in soup.find_all('a'):
    print(link.get('href'))
