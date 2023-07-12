from glob import glob
import re
from time import sleep
import os
import urllib.request
import ssl
from bs4 import BeautifulSoup

# first, set script location as current directory
cfol = os.path.dirname(os.path.abspath(__file__))
os.chdir(cfol)

#########################
# force the acceptance of "no valid ssl certificate", taken from https://stackoverflow.com/a/55320961
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
#########################

files = glob('*.html')

for file in files:
    with open(file, encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'lxml')
        try:        
            for counter,link in enumerate(soup.find_all('a', {'href': re.compile('pdf')})):
                flink = 'https://morethesis.unimore.it' + (link['href'])
                etdcode = re.search('(etd.*?)/', flink).group(1)
                fname = link.get_text()
                print(etdcode)
                urllib.request.urlretrieve(flink, 'pdfs/' + etdcode + '_' + str(counter) + 'fname')
                sleep(4)
        except:
            pass