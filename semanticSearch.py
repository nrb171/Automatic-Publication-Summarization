import openai
import os
import tiktoken
import pandas as pd
from scipy import spatial
import numpy as np
import argparse

import json

parser = argparse.ArgumentParser(description="Search for similar embeddings")
parser.add_argument("-q", "--query", type=str, required=True, help="Query to search for")
parser.add_argument("-d", "--directory", type=str, default="./", help="Directory to load data from")
parser.add_argument("-n", "--top_n", type=int, default=100, help="Number of results to return")
parser.add_argument("-m", "--model", type=str, default="gpt-3.5-turbo", help="Model to use")

args = parser.parse_args()

def similaritySearch(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = 100
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    embeddingModel = "text-embedding-ada-002"
    query_embedding_response = openai.Embedding.create(
        model=embeddingModel,
        input=query
    )
    query_embedding = query_embedding_response["data"][0]["embedding"]
    strings_and_relatednesses = []
    for i in range(len(df)):
        embedding = df[2][i]
        embedding = embedding[1:-2].split(", ")
        embedding = [float(i) for i in embedding]
        relatedness = relatedness_fn(query_embedding, embedding)
        strings_and_relatednesses.append({"string": df[1][i], "relatedness": relatedness})

    # sort by relatedness
    strings_and_relatednesses.sort(key=lambda x: x["relatedness"], reverse=True)
    return strings_and_relatednesses[:top_n]

def main():
    with open("key.ini", "r") as f:
        openai.api_key = f.read()
    embeddingModel = "text-embedding-ada-002"
    encodingName="cl100k_base"
    gptModel = args.model

    #load data into array
    df = pd.read_csv(args.directory+"/embeddings/embeddings.csv", header=None)
    #get columns 2nd and 3rd columns

    similaritySearchResults = similaritySearch(args.query, df, top_n=args.top_n)
    print(similaritySearchResults)

main()