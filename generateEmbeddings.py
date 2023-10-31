import openai
import os
#import tiktoken
import pandas as pd
from scipy import spatial
import argparse
import time
import numpy as np
from bs4 import BeautifulSoup
import textwrap

import json

model = "text-embedding-ada-002"
directory = "/mnt/c/Users/Nicholas Barron/OneDrive - The Pennsylvania State University/PSU/Didlake Group-PSU/Papers/.embeddings/"
with open("key.ini", "r") as f:
    openai.api_key = f.read()


def generateEmbeddings(text, model):
    text = text.replace("\n", " ")
    embedding = openai.Embedding.create(input = text, model=model)['data'][0]['embedding']
    return embedding


def parseXML(soup):
    body = soup.body
    
    # extract metadata
    meta = "Title: "+ soup.title.get_text()+"\n\n"
    meta+= "Authors: "
    for author in soup.teiHeader.find_all('author'):
        meta+= author.forename.get_text()+" "+author.surname.get_text()+", "
    meta = meta[:-2]+"\n\n"
    meta+= "Published: "+soup.date.get_text()+"\n\n"
    meta+= "Abstract: "
    for p in soup.abstract.find_all('p'):
        meta+= p.get_text()+"\n"
    meta+="\n\n"

    paper=[]
    print(type(body.get_text()))
    for text in textwrap.wrap(body.get_text(), 7000):
        paper.append(meta+text)

    
    


    return paper



df = pd.DataFrame(columns=["name",  "string", "embedding"])

files = os.listdir(directory)
for file in files:
    if file.endswith(".xml"):
        text = open(directory+file, "r")
        soup = BeautifulSoup(text, 'xml')
        
        try:
            paper = parseXML(soup)
        except AttributeError:
            continue

        for text in paper:
            errorCount = 0
            while 1:
                try:
                    embedding = generateEmbeddings(text, model)
                    break
                except Exception as e:
                    errorCount+=1
                    if errorCount > 5:
                        break
                    time.sleep(errorCount**2)

            df = pd.concat([df, pd.DataFrame([[file[:-15], text, embedding]], columns=["name","string", "embedding"])], ignore_index=True)

        df.to_csv(directory+"embeddings.csv")


