from time import sleep
from glob import glob
import csv
import codecs
import re
from selenium import webdriver
from bs4 import BeautifulSoup
# import and variable below - allowing the crawler to browse https pages even when a certificate is not verified -
# from https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Set the filename of the CSV file where metadata will be/is stored
metadata_file = "metadata_all.csv"

# Set options for the Firefox webdriver
options = webdriver.FirefoxOptions()
options.add_argument('--headless')
driver = webdriver.Firefox(options=options)

files = glob('*links.csv')

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
}

# First we download the HTML files from the website, getting the links from the previously generated *links.csv files
for file in files:
    print(file)
    with open(file, 'r') as f:
        readcsv = csv.reader(f)
        next(readcsv, None)
        rows = [r for r in readcsv]
        for row in rows:
            print(row)
            fname = re.search(r'.*?available/(.*?)/', row[0])
            fname = fname.group(1)
            fout = codecs.open('downloaded/' + fname + '.html', 'a')
            print(fname)
            # line below loads the custom chain used by morethesis website, downloaded from the website
            # otherwise requests can't accept the (incorrect) certificate chain
            #page = requests.get(line, verify='keys/etd-dmz-ext-unimo-it-chain.pem', headers = headers)
            driver.get(row[0])
            soup = BeautifulSoup(driver.page_source, 'lxml')
            print('Collecting ' + fname + '.html')
            fout.write(str(soup))
            # print(soup)
            sleep(4)

# Now check if the file where the metadata will be saved already exists; if it does, then:
if os.path.isfile(metadata_file):
    # Open the file in 'appending' mode ('a') - so that every time a new content is written to it, it is added to the end of
    # the file -, and initiate a 'writer' to write the contents in CSV format, using the tav character as delimiter
    metadata_writer = csv.writer(
        open("metadata_all.csv", "a", encoding="utf-8"), delimiter="\t"
    )
# If the file does not exist
else:
    # Create the file in 'appending' mode ('a') - so that every time a new content is written to it, it is added to the end of
    # the file -, and initiate a 'writer' to write the contents in CSV format, using the tav character as delimiter
    metadata_writer = csv.writer(
        open("metadata_all.csv", "a", encoding="utf-8"), delimiter="\t"
    )
    # Write as first row the names of the columns
    metadata_writer.writerow(
        [
            "doc_id",
            "tipo_tesi",
            "autore",
            "urn",
            "titolo_it",
            "titolo_en",
            "struttura",
            "corso_di_studi",
            "keywords",
            "data",
            "disponibilità",
            "abstract",
        ]
    )

# Create a list of all the filenames with '.html' extension contained in the subfolder 'downloaded' and all of its possible subfolders
files = sorted(glob.glob("./downloaded/*.html", recursive=True))

# Now we extract the metadata from the downloaded HTML files:
for file in files:
    # Open the file
    f = open(file, encoding="utf8")
    # Remove the '.html' extension from the filename
    filename = file.replace(".html", "")
    # Read the contents of the file with BeautifulSoup and store them inside of the variable 'soup'
    soup = BeautifulSoup(f, "lxml")
    # Find the <table> element tag and assign its contents to the variable 'table'
    table = soup.find("table")
    # Inside <table>, find the <tbody> element tag and store its contents inside the variable 'tbody'
    tbody = table.find("tbody")
    # Find metadata elements by searching for the <th> element tag containing the relevant label (indicated by 'text="LABEL"'),
    # and extract the text from the next adjacent <td> element tag (where the metadata value is stored)
    tipotesi = tbody.find("th", text="Tipo di tesi").find_next("td").text.strip()
    autore = tbody.find("th", text="Autore").find_next("td").text.strip()
    urn = tbody.find("th", text="URN").find_next("td").text.strip()
    titolo_it = tbody.find("th", text="Titolo").find_next("td").text.strip()
    titolo_en = tbody.find("th", text="Titolo in inglese").find_next("td").text.strip()
    corso_di_studi = (
        tbody.find("th", text="Corso di studi").find_next("td").text.strip()
    )
    keywords = tbody.find("th", text="Parole chiave").find_next("td").text.strip()
    data = tbody.find("th", text="Data inizio appello").find_next("td").text.strip()
    disponibilita = tbody.find("th", text="Disponibilità").find_next("td").text.strip()
    abstract = tbody.find_all("td", {"colspan": "2"})[1].text

    # The following verification is required as some catalogue cards contain a field named 'Settore scientifico disciplinare'
    # (Disciplinary scientific area), while others have 'Struttura' (Facility) instead. Either way, the resulting value is stored
    # inside of a metadata attribute labelled 'struttura'.
    # Check if a <th> tag with value 'Settore scientifico disciplinare' exists; if so:
    if tbody.find("th", text="Settore scientifico disciplinare") is not None:
        # Extract the value and save it to the variable 'struttura'
        struttura = (
            tbody.find("th", text="Settore scientifico disciplinare")
            .find_next("td")
            .text.strip()
        )
    # If it does not exist, extract the value from the <th> element tag with value 'Struttura'
    else:
        struttura = tbody.find("th", text="Struttura").find_next("td").text.strip()

    # Save all the extracted metadata elements to a list called 'metadata_line', in the order they are to be written in the output CSV
    metadata_line = [
        filename,
        tipotesi,
        autore,
        urn,
        titolo_it,
        titolo_en,
        struttura,
        corso_di_studi,
        keywords,
        data,
        disponibilita,
        abstract,
    ]
    # Write the values stored in 'metadata_line' as one row in the CSV file
    metadata_writer.writerow(metadata_line)