import glob
import os
import re
from time import sleep
from bs4 import BeautifulSoup
from lxml import etree
import pandas as pd
from lingua.language import Language
from lingua.detector import LanguageDetectorBuilder
from grobid_client.grobid_client import GrobidClient
# The script assumes that a working local instance of GROBID is running - using GROBID from docker image -
# with 8GB of RAM set in config. The image is run with:
# docker run -t -m 8GB --rm -p 8070:8070 lfoppiano/grobid:0.7.1
# A working 'grobid_config.json' is assumed to be in path, and to contain the following settings - that can be copy-pasted
# in a new file named 'grobid_config.json'
'''
{
    "grobid_server": "http://localhost:8070",
    "batch_size": 1000,
    "sleep_time": 5,
    "timeout": 360,
    "coordinates": [ "persName", "figure", "ref", "biblStruct", "formula", "s" ]
}
'''

# Setup some variables and parameters to be later used
languages = [Language.ENGLISH, Language.FRENCH, Language.GERMAN, Language.SPANISH, Language.ITALIAN]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

# create function to detect the language using lingua, and substitute lingua's labels with two-letter labels; 
# also include 'none' when no language is recognised
def detectLanguage(tag):
    replacements = {
        'language.italian' : 'it',
        'language.french' : 'fr',
        'language.german' : 'de',
        'language.spanish' : 'es',
        'language.english' : 'en',
        'none' : 'none'
    }
    toTag = tag.get_text()
    detected = str(detector.detect_language_of(toTag)).lower()
    outString = replacements[detected]
    return(str(outString))

########################
# First, let's start by finding the PDFs and extracting their contents to XML-TEI using GROBID
########################
cfol = os.path.dirname(os.path.abspath(__file__))
os.chdir(cfol)

pdfs = glob.glob('*.pdf')

client = GrobidClient(config_path="./grobid_config.json")


for pdf in pdfs:
    outname = pdf + '.tei.xml'
    # first check if file already exists and if so, that it is not empty
    if os.path.isfile(outname) and os.stat(outname).st_size > 0:
        pass
    else:
        with open(pdf + '.tei.xml', 'w', encoding="utf-8") as out:
            # get full path of the file, as GROBID client requires the full path
            fullPath = os.path.abspath(pdf)
            print(fullPath)
            # write the last item of the tuple created by GROBID - i.e. the XML file;
            # (other two items are filename and server response - usually '200')
            out.write(client.process_pdf('processFulltextDocument', fullPath, generateIDs='1', consolidate_header=False, consolidate_citations=False,
                      tei_coordinates=False, include_raw_affiliations=False, include_raw_citations=False, segment_sentences=False)[-1])
            # sleep, coz you never know...
            sleep(2)

#####################
# From extracted XML-TEI files (from PDFs) to (almost) final XML corpus files
#####################
# After the PDFs have been extracted, use the resulting files to create the
# corpus files (without tagging)

# create a dataframe to log the results of the scripts; it counts the number of divs and figs in the input XML-TEI file(s)
# and the respective number of divs and figs added to the output XML
logDB = pd.DataFrame(columns = ['urn', 'input divs', 'output divs', 'input figures', 'output figures', 'input notes', 'output notes'])

# then create metadata database (mdb) using the metadata csv file; set the urn as index, and remove duplicates!
# this is needed since the same thesis can appear more than once, e.g. etd-09182019-132243 that appears in
# both LM and LM_2_CS folders (hence, subcategories are included in their supracategory!)
mdb = pd.read_csv('../metadata_all.csv', sep='\t')
mdb = mdb.set_index('urn')
mdb = mdb.groupby(mdb.index).first()

# Now we start looking for the files and we process them
listOfFiles = []
urnRegex = re.compile('etd-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]_0*tei.xml')
xmlfiles = sorted(glob.glob('etd-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]_0*tei.xml'))
listOfFiles.append(xmlfiles)

for xmlfile in xmlfiles:
    # extract the URN from the filename
    urn = re.search('(etd-[0-9]{8}-[0-9]{6})_[0-9]{1,2}.*', xmlfile).group(1)
    outname = urn + '.clean.xml'
    autore = mdb.loc[urn, 'autore']
    #print(urn + '\t' +  autore)
    doc = etree.Element('doc')
    doc.attrib['urn'] = urn
    doc.attrib['type'] = mdb.loc[urn, 'tipo_tesi']
    # remove the comma between the author's surname and name
    doc.attrib['author'] = re.sub(',', '', mdb.loc[urn, 'autore'])
    doc.attrib['title'] = mdb.loc[urn, 'titolo_it']
    # as not all the theses may have an English title, check if it is so, and assign value 'na' when not available
    doc.attrib['title_en'] = mdb.loc[urn, 'titolo_en'] if not type(None) else 'na'
    doc.attrib['department'] = mdb.loc[urn, 'struttura']
    doc.attrib['degree'] = mdb.loc[urn, 'corso_di_studi']
    # get the date (in the format YYYY-MM-DD) and capture each part into a group
    date = re.search('([0-9]{4})-([0-9]{2})-([0-9]{2})', mdb.loc[urn,'data'])
    doc.attrib['date_y'] = date.group(1)
    doc.attrib['date_m'] = date.group(2)
    doc.attrib['date_d'] = date.group(3)
    #print(date.group(1))
    # Set counters to count the total number of divs and figs in the original XML-TEI files, to be added to
    # the logDB
    inDivs = 0
    inFigs = 0
    outDivs = 0
    outFigs = 0
    inNotes = 0
    outNotes = 0


    for f in sorted(glob.glob(urn + '*.tei.xml')):
        with open(f, 'r') as one:
            print('Processing' + '\t' + f + '\n')
            soup = BeautifulSoup(one, features='xml')
            try:
            # check if tag <abstract> exists - if it does, it precedes <body> and is on the same level
            # and check if the text contained in the <abstract> is longer than 100 characters; this is a rough solution
            # to avoid creating an <abstract> in the corpus when GROBID mistakenly identifies a section as an abstract
            # (e.g. etd-02132019-084716_0-Tesi_di_Laurea_Medicina_e_Chirurgia_Curto_Alberto.pdf - where dedication 'Ai miei genitori'
            # is extracted as <abstract>) or when an <abstract> is created but contains to text.
                if soup.find('abstract') and len(soup.find('abstract').get_text()) > 100:
                    abTag = soup.find('abstract')
                    abstract = abTag.get_text()
                    abstractEl = etree.SubElement(doc, 'abstract')
                    abstractEl.text = abstract
                    abstractEl.attrib['lang'] = detectLanguage(abTag)
                else:
                    pass

                for body in soup.select('body'):
                    inDivs += len(body.find_all('div', recursive=False))
                    inFigs += len(body.find_all('figure', recursive=False))
                    inNotes += len(body.find_all('note', recursive=False))
                    allChildren = body.findChildren(recursive=False)
                    for child in allChildren:
                        #print(child.name)
                    # Here every child could be simplified and treated like body, i.e. list all of its children and operate on each one
                    # depending on their name; for now, let's keep it stricter
                        if child.name == 'div':
                            outDivs += 1
                            div = child
                            sect = etree.SubElement(doc, 'sect')
                            # create a list that will contain the detected language of each <p>
                            pLangs = []
                            #print(div.find_all('head'))
                            #sect.attrib['n'] = str(divNum)
                            #print(div.next_element.name)
                            if div.find('head', recursive=False):
                                for head in div.find_all('head'):
                                    # get the text enclosed in the <head>
                                    heading = head.get_text()
                                    #sect.attrib['name'] = heading
                                    #sect.text = heading
                                    headEl = etree.SubElement(sect, 'head')
                                    headEl.text = heading
                                    #print(heading)
                                
                            else:
                                head = etree.SubElement(sect, 'head')
                            
                            if div.find('p', recursive=False):
                                for p in div.find_all('p'):
                                    pEl = etree.SubElement(sect, 'p')
                                    pEl.text = p.get_text()
                                    # detect the language of the text in this <p> and add it to the list
                                    pLangs.append(detectLanguage(p))
                            
                            else:
                                # in case no <p> is found, it is highly likely the file only contains bibliography/figures
                                # hence, we might need to store this info somewhere to know that the thesis will not be included in the corpus
                                #print('NO TEXT')
                                continue

                            # the most frequent language among all the <p> in this <sect> (contained in the list pLangs) is assigned as value of the attribute 'lang' to <sect>; value may be 'none' if no language is recognised
                            sect.attrib['lang'] = max(set(pLangs), key=pLangs.count)
                            #print(max(set(pLangs), key=pLangs.count))
                            
                            if div.find('note', recursive=False):
                                #print(div('note'))
                                for note in div.find_all('note'):
                                    noteEl = etree.SubElement(sect, 'note')
                                    noteEl.text = note.get_text()
                            else:
                                pass
                        
                        elif child.name == 'figure':
                            outFigs += 1
                            fLangs = []
                            fig = child
                            figEl = etree.SubElement(doc, 'fig')
                            #figDesc = fig.select('figDesc')
                            figEl.text = fig.findChild('figDesc').get_text()
                            #fig.attrib['lang'] = str(detectLanguage(figDesc))
                            # Check if the original <figure> contains the attribute 'type' (it appears it's only used when fig is table);
                            # and if not assign the value 'na'
                            try:
                                figEl.attrib['type'] = fig['type']
                            except NoneType:
                                figEl.attrib['type'] = 'na'
                                pass
                        
                        elif child.name == 'note':
                            outNotes +=1
                            note = child
                            noteEl = etree.SubElement(doc, 'note')
                            noteEl.text = note.get_text
                            
                        else:
                            print('Unknown body-children tag found:\t' + child.name + '\n')       
            except:
                continue
    logDB.loc[len(logDB)] = [urn, inDivs, outDivs, inFigs, outFigs, inNotes, outNotes]
    tree = etree.ElementTree(doc)
    #print(etree.tostring(doc, pretty_print=True))
    #print('\n')
    tree.write(outname, pretty_print=True, xml_declaration=True, encoding="utf-8")
logDB.to_csv('log_extraction.csv')