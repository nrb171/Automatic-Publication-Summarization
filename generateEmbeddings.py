import openai
import os
from PyPDF2 import PdfReader
import tiktoken
import pandas as pd
from scipy import spatial
import argparse
import time
import numpy as np

import json

model = "text-embedding-ada-002"
directory = "/Users/nrb171/Library/CloudStorage/OneDrive-ThePennsylvaniaStateUniversity/PSU/Didlake Group-PSU/Papers/.embeddings/"
with open("key.ini", "r") as f:
    openai.api_key = f.read()



def generateEmbeddings(text, model):
    text = text.replace("\n", " ")
    embedding = openai.Embedding.create(input = text, model=model)['data'][0]['embedding']
    return embedding


df = pd.DataFrame(columns=["name", "string", "embedding"])

files = os.listdir(directory)
for file in files:
    if file.endswith(".md"):
        text = open(directory+file, "r").read()
        if len(text)<1000:
            os.remove(directory+file)
            continue

        embedding = generateEmbeddings(text, model)
        df = df.append({"name": file, "string": text[:-3], "embedding": embedding}, ignore_index=True)

df.to_csv(directory+"embeddings.csv")


