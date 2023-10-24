# Introduction
Utilize OpenAI API and PDF scraping software to extract summaries of academic papers. Calculate embeddings and store in a vectorized format to allow for semantic search.

# Requirements
- Python 3.6+
install the requirements.txt file
- pip install -r requirements.txt
- Create a file name key.ini and paste your OpenAI API key into it

## Format your Papers folder
Format your `Papers` folder as follows:

`Papers`
  Processed papers are stored here.
    
  `/Papers/.APMS`
    The scripts from APS go here.
    
  `/Papers/.embeddings`
    Processed summarizations and embeddings database stored here.


To run APS, navigate to `Papers` and run `python ./.APS/APS.py`
Additional keyword argument (`-d`) can be accepted to change the directory of the `/Papers/` and `/Papers/.embeddings/` folders.

# Features to be implemented
- [ ] Wrap a chatGPT agent around the semantic search to allow for natural language queries
- [ ] Conversational capabilities
- [ ] Additional glossary-type knowledgebase

# See also:
[Automatic Publication Management System](https://github.com/nrb171/Automatic-Publication-Management-System)
