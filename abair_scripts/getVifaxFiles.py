# -*- coding: utf-8 -*-

import os, requests, io, re
from bs4 import BeautifulSoup

urls = ["http://vifax.maynoothuniversity.ie/cartlann/sport"]


def main(urls):
    for url in urls:
        getVifaxFiles(url)

def getVifaxFiles(url):

    vifax_base_dir = "vifax"
    vifax_name = re.sub("^.*/([^/]+)$", r"\1", url)
    vifax_file = "%s/%s.html" % (vifax_base_dir, vifax_name)
    vifax_dir = "%s/%s" % (vifax_base_dir, vifax_name)

    #soup = downloadVifaxFile(url)
    soup = loadVifaxFile(vifax_file)
    titles = getTitles(soup)
    for key in titles:
        for (title, videourl, pdfurl) in titles[key]:
            print(u"%s\t%s\t%s" % (title, videourl, pdfurl))
            getVideoAndPdf(vifax_dir, title, videourl, pdfurl)


def downloadVifaxFile(url):
    r = requests.get(url)
    html_doc = r.text
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup

def loadVifaxFile(filename):
    html_doc = open(filename).read()
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup


def getTitles(soup):
    titles = {}
    for table in soup("table"):
        title = table.find("th").string.lower().replace(" ", "_").replace(u"’","")
        title = title.replace(u"á","a")
        title = title.replace(u"é","e")
        title = title.replace(u"í","i")
        title = title.replace(u"ó","o")
        title = title.replace(u"ú","u")
        
        
        video = table.find_all("td")[0].find("source")["src"]
        pdf = table.find_all("td")[1].find("a")["href"]
        if title in titles:
            newtitle = "%s_%d" % (title, len(titles[title]))
            titles[title].append((newtitle,video, pdf))
        else:
            titles[title] = [(title,video, pdf)]
    return titles


def getVideoAndPdf(vifax_dir, title, videourl, pdfurl):

    videofile = "%s/%s.mp4" % (vifax_dir, title)
    pdffile = "%s/%s.pdf" % (vifax_dir, title)
    wavfile = "%s/%s.wav" % (vifax_dir, title)

    #downloadVideo(videofile, videourl)
    #convertVideoToWav(videofile, wavfile)

    downloadPdf(pdffile, pdfurl)
    res = convertPdf(pdffile)

    for speaker_text in res:
        speaker = speaker_text["speaker"]
        text = speaker_text["text"]
        print("SPEAKER: %s\nTEXT: %s" % (speaker, text))






def downloadVideo(videofile, url):
    r = requests.get(url)
    fh = io.open(videofile, "wb")
    fh.write(r.content)
    fh.close()

def convertVideoToWav(videofile, wavfile):
    mplayer_cmd = "mplayer -benchmark -vc null -vo null -ao pcm:fast -ao pcm %s -ao pcm:waveheader -ao pcm:file=%s" % (videofile, wavfile)
    print(mplayer_cmd)
    sox_cmd = "sox %s -r 16000 -c 1 tmp.wav; mv tmp.wav %s" % (wavfile, wavfile)
    print(sox_cmd)
    os.system(mplayer_cmd)
    os.system(sox_cmd)
    
def downloadPdf(pdffile, url):
    r = requests.get(url)
    fh = io.open(pdffile, "wb")
    fh.write(r.content)
    fh.close()

def convertPdf(pdffile):
    title = os.path.splitext(pdffile)[0]
    
    htmlfile = title+"s.html"
    txtfile = title+".txt"

    pdfto_cmd = u"pdftohtml -i %s" % pdffile
    print(pdfto_cmd)
    os.system(pdfto_cmd)

    speaker_texts = getSpeakerText(htmlfile)

    os.system("rm %s*.html" % title)

    fh = io.open(txtfile, "w", encoding="utf-8")
    for speaker_text in speaker_texts:
        speaker = speaker_text["speaker"]
        text = speaker_text["text"]
        fh.write("SPEAKER: %s\nTEXT: %s\n" % (speaker, text))
    fh.close()
    
    return speaker_texts

    
def getSpeakerText(htmlfile):
    result = []
    html_doc = open(htmlfile).read()
    soup = BeautifulSoup(html_doc, 'html.parser')

    pages = soup.find_all("a")
    for page in pages:
        if "name" in page.attrs and page["name"] == "4":
            startoftext = page

    speaker_element = startoftext.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling

    try:
        speaker = speaker_element.getText()
    except AttributeError:
        #This happens if the text is on page 5..
        #Find a way to know which page to read!
        return result
        
    next_element = speaker_element
    text_list = []
    speaker_list = []
    speaker_text = (speaker, speaker_list)
    while True:
        try:
            next_element = next_element.next_sibling
            if next_element.name == "b":
                speaker = next_element.getText()
                #print("SPEAKER: %s" % speaker)
                text_list.append(speaker_text)
                speaker_list = []
                speaker_text = (speaker, speaker_list)
                
            try:
                chunk = next_element.string.strip()
                if re.match("^[0-9]$", chunk):
                    #if the chunk is only a number, it's a footnote,
                    #and the text is finished
                    text_list.append(speaker_text)
                    break
                    
                if chunk != None and chunk != "":
                    chunk = chunk.replace(u"\xa0\xa0", " ")
                    chunk = chunk.replace(u"\xa0", " ")
                    #remove note references
                    chunk = re.sub(r"(\S)[0-9]", r"\1", chunk)
                    speaker_list.append(chunk)
            except AttributeError:
                next
        except AttributeError:
            text_list.append(speaker_text)
            break
        
    for (speaker, speaker_list) in text_list:        
        text = "%s" % " ".join(speaker_list)
        result.append({"speaker":speaker, "text":text})
    return result

main(urls)
