import requests
from bs4 import BeautifulSoup

url = "http://vifax.maynoothuniversity.ie/cartlann/sport/"

r = requests.get(url)
html_doc = r.text

soup = BeautifulSoup(html_doc, 'html.parser')

#for link in soup.find_all('a'):
#    print(link.get('href'))

for div in soup.find_all("div", class_="wp-video"):
    print(div)
    source = div.find("source")
    print(source["src"])

    print(div.parentnext_sibling)

