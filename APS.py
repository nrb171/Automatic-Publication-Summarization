import openai
import os
from PyPDF2 import PdfReader
import tiktoken
import pandas as pd
from scipy import spatial
import argparse

import json

parser = argparse.ArgumentParser(description="Automatic Paper Summarization")
parser.add_argument("-d", "--directory", type=str, required=True, help="Path to directory containing PDF files")
args = parser.parse_args()

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def iterativeDensification(text, gptModel, metadata):
    costIn = 0.003/1000
    costOut = 0.004/1000
    totalCost = 0
    history = []
    questions = [
        "What is the main goal of this paper?",
        "What are the key concepts, techniques, methodologies, and/or theories introduced in this paper?",
        "What are the findings, conclusions, and/or results of this paper?",
        "what is the methodology/technique used in this paper?",
        "what is the source of the data used in this paper?",
        "what does this paper say about the main goal?",
        "What does this paper say about potential issues, problems, or concerns regarding the methodology or results of their study?",
        "What does this paper say about possible future work?",
    ]
    history.append({"role": "system", "content": "You answer questions about academic literature."})
    # gather questions and answers
    for question in questions:
        history.append({"role": "user", "content": question})
        print(history[-1])
        response = openai.ChatCompletion.create(
            model=gptModel,
            temperature=0,
            messages=[
                {"role": "system", "content": "You answer questions about academic literature."},
                {"role": "user", "content": "Answer the following in less than"+str(350)+"words:\n\n"+question+": "+text}
            ]
        )
        totalCost += response["usage"]["prompt_tokens"]*costIn
        totalCost += response["usage"]["completion_tokens"]*costOut
        history.append({"role": "system", "content": response["choices"][0]["message"]["content"]})
        print(history[-1])
    
    history.append({"role": "user", "content": "Now, you will write a plaintext summary of the paper based on what you have learned above. Your goal is to write a concise summary of this paper, focusing primarily on the main goal and each key concept or entity introduced in the paper. Keep the summary brief and to the point."})
    densificationProtocol = [
        "Step 1: Instruction: Based on the initial sumary/list/keywords, refine it by incorporating 1-2 additional key entities or concepts from the document without increasing the overall length. Focus on significant elements or information in the document, and ensure the list remains coherent and concise.",
        "Step 2: Instruction: Further refine the list by searching for and adding 1-2 more salient entities or details from the document, elements a curious and smart reader would note down, without increasing the overall length. Maintain clarity and conciseness while enhancing the informativeness of the summary/list/keywords.",
        "Repeat Step 2"]
    for instruction in densificationProtocol:
        history.append({"role": "user", "content": instruction})
        print(history[-1])
        response = openai.ChatCompletion.create(
            model=gptModel,
            temperature=0,
            messages=history
        )
        totalCost += response["usage"]["prompt_tokens"]*costIn
        totalCost += response["usage"]["completion_tokens"]*costOut
        response_message = response["choices"][0]["message"]["content"]
        history.append({"role": "system", "content": response_message})
        print(history[-1])
    history.insert(2, {"role": "user", "content": "Here is the paper: "+text})
    history.append({"role": "user", "content": "Using what you know about the paper. You will fill out the following form:\n\n---\nAuthors:\n    - FirstName LastName\nYearOfPublication:\"YYYY\"\nTitle: \"\"\n---\n\n#Summary\nPLACE THE SUMMARY HERE. THIS SHOULD INCLUDE THE GOAL, METHODOLOGIES, RESULTS, AND NECESSARY COMMENTARY.\n\n#Data and Methodology\nDESCRIBE THE DATA SOURCE AND TYPE (E.G., SIMULATION OR OBSERVATION). ALSO DISCUSS THE METHODOLOGIES/TECHNIQUES - SPECIFICALLY MENTION NOVEL METHODOLOGIES. \n\n#Results/Conclusions/Findings\nLIST ALL RESULTS/CONCLUSIONS/FINDINGS. ALSO MENTION ANY POTENTIAL SHORTCOMINGS/ISSUES WITH THE STUDY."})
    print(history[-1])

    finalResponse = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=history
    )
    totalCost += finalResponse["usage"]["prompt_tokens"]*0.03/1000
    totalCost += finalResponse["usage"]["completion_tokens"]*0.06/1000
    finalResponse = finalResponse["choices"][0]["message"]["content"]
    history.append({"role": "system", "content": finalResponse})
    print(history[-1])
    return history, totalCost


def pdfTranscription(pdfPath):
    costIn = 0.0015/1000
    costOut = 0.002/1000
    totalCost = 0
    pdf_reader = PdfReader(pdfPath)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    #remove all newlines
    #text = text.replace("\n", " ")
    #chunk into 8000 token chunks
    text = splitString(text, "text-embedding-ada-002", 2056,False)
    

    messages = [
        {"role": "system", "content": "You read pdfs and return summarized transcriptions. You will make sure that words are separated by spaces and that there are no extra spaces."}]
    messages.append({})
    messages.append({"role": "system", "content": "Here is the summarized transcription:"})
    transcripion=""
    for i, page in enumerate(text):
        
        
        messages[1] = ({"role":"user", "content": "Read and provide a summarized transcription the following."+ page})
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            temperature=0,
            messages=messages
        )
        totalCost += response["usage"]["prompt_tokens"]*costIn
        totalCost += response["usage"]["completion_tokens"]*costOut
        print(response["choices"][0]["message"]["content"])
        print(totalCost)
        transcripion += "["+str(i+1)+"] "+response["choices"][0]["message"]["content"]
    return transcripion, totalCost

def paperInterrogation(text, gptModel):
    totalCost = 0
    costIn = 0.03/1000
    costOut = 0.06/1000
    prompts = {
        "role": "user",
        "content": 
            "What is the main goal of this paper?"+
            "What are the key concepts, techniques, methodologies, and/or theories introduced in this paper?"+
            "What are the findings, conclusions, and/or results of this paper?"+
            "what is the methodology/technique used in this paper?"+
            "what is the source of the data used in this paper?"+
            "what does this paper say about the main goal?"+
            "What does this paper say about potential issues, problems, or concerns regarding the methodology or results of their study?"+
            "What does this paper say about possible future work?"
    }

    messages = [
        {"role": "system", "content": "You summarize academic papers."},
        {"role": "user", "content": "You will be summarizing and answering questions about the following: "+text},
        {"role": "system", "content": "Great! Let's get started, what questions do you want answered?"},
        {"role": "user", "content": "Please answer the following questions. Use this format for your responses: \n###RESTATE USER QUESTION HERE\n\nYOUR ANSWER HERE\n\n---\n\n"},
        {"role": "system", "content": "Great! Let's get started, what questions do you want answered?"}
    ]
    messages.append(prompts)

    response = openai.ChatCompletion.create(
        model=gptModel,
        messages=messages
    )
    queryResponse = response["choices"][0]["message"]["content"]
    totalCost += response["usage"]["prompt_tokens"]*costIn
    totalCost += response["usage"]["completion_tokens"]*costOut

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You read and answer questions about academic papers. Previously, you had this to say about a paper: "+queryResponse},
            {"role": "user", "content": "Summarize your findings in less than 500 words. Use plain language and be concise. Use this format for your response. \"###Summary\n\nYOUR SUMMARY HERE\n\n---\n\n\""}
        ]
    )
    totalCost += response["usage"]["prompt_tokens"]*costIn
    totalCost += response["usage"]["completion_tokens"]*costOut
    summaryResponse = response["choices"][0]["message"]["content"]
    return summaryResponse+"\n\n"+queryResponse, totalCost

def generateEmbeddings(text, model, encoding):
    text = text.replace("\n", " ")
    embedding = openai.Embedding.create(input = text, model=model)['data'][0]['embedding']
    return embedding

def splitString(
    string: str,
    model: str,
    max_tokens: int,
    print_warning: bool = True,
    ) -> list[str]:
    
    splitStrings = []
    """splits a string to a maximum number of tokens."""
    encoding = tiktoken.encoding_for_model(model)
    encoded_string = encoding.encode(string)
    start = 0
    while len(encoded_string) >= start+max_tokens:
        if print_warning:
            print(
                f"Warning: truncating string of length {len(encoded_string)} to {max_tokens} tokens"
            )
        truncated_string = encoding.decode(encoded_string[start:min([start+max_tokens, len(encoded_string)])])
        
        splitStrings.append(truncated_string)
        start += max_tokens
    
    return splitStrings

def main():

    # OpenAI API Key
    #get API key from ./key.ini
    with open("key.ini", "r") as f:
        openai.api_key = f.read()
    embeddingModel = "text-embedding-ada-002"
    encodingName="cl100k_base"
    gptModel = "gpt-3.5-turbo-16k"
    costIn = 0.003/1000
    costOut = 0.004/1000
    totalCost = 0

    # Take the directory as a command line argument
    directory = args.directory


    #get array of all files in directory
    files = os.listdir(directory)

    #loop through all files in directory
    for i in range(len(files)):
    
        # extract text from pdf
        if files[i].endswith(".pdf"):
            try:
                if not os.path.exists(directory+"/embeddings/"+files[i][:-4]+".md"):
                    errorFree = False
                    attempts = 0
                    while errorFree == False:
                        try:
                            text, transcriptinCost = pdfTranscription(directory+files[i])
                            errorFree = True
                        except:
                            attempts += 1
                            if attempts > 3:
                                raise("Too many attempts")
                            continue
                    
                    
                    #history, densificationCost = iterativeDensification(text, gptModel, metadata)
                    errorFree = False
                    attempts = 0
                    while errorFree == False:
                        try:
                            interrogation, interrogationCost = paperInterrogation(text, "gpt-4")
                            errorFree = True
                        except:
                            attempts += 1
                            if attempts > 3:
                                raise("Too many attempts")
                            continue
                    

                    totalCost = interrogationCost + transcriptinCost
                    print(totalCost)

                    # save the text to a file
                    with open(directory+"/embeddings/"+files[i][:-4]+".md", 'w') as f:
                        f.write(interrogation)

                    # get the embedding
                    embeddings = generateEmbeddings(interrogation, embeddingModel, encodingName)
                    df = pd.DataFrame({"text": interrogation, "embedding": [embeddings]})
                    # add to end of embeddings file
                    with open(directory+"/embeddings/embeddings.csv", 'a') as f:
                        df.to_csv(f, header=False)
                        # save the embedding to the end of the embeddings file
            except:
                continue

main()
            