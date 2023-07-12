import re
from glob import glob
import codecs
import csv
from bs4 import BeautifulSoup

files = glob('*.html')
header = ['link', 'downloaded']

for file in files:
    with open(file, encoding="utf8") as f:
        fname = file.replace('.html', '')
        fout = codecs.open(fname + '_links.csv', 'a')
        writer = csv.writer(fout)
        writer.writerow(header)
        soup = BeautifulSoup(f, 'lxml')
        # using regex in soup https://stackoverflow.com/questions/24748445/beautiful-soup-using-regex-to-find-tags
        url = []
        for link in soup.find_all('a', {'href': re.compile(r'.*?theses/available.*?')}):
            print(link['href'])
            writer.writerow([link['href'], 'n'])