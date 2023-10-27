from grobid_client.grobid_client import GrobidClient

papersDir = "dir/to/Papers"
client = GrobidClient(config_path="./config.json")
client.process(
    "processFulltextDocument", 
    papersDir,
    output=papersDir+"/.embeddings/", 
    n=8,
    verbose=True)