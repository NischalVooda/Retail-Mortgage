import os
import json
from azure.core.exceptions import HttpResponseError
from dotenv import find_dotenv, load_dotenv
import pymongo

client = pymongo.MongoClient("mongodb+srv://nischal:nischal@cluster0.sab29.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["idDocument"]  # Replace with your database name
collection = db["borrower"]  # Replace with your collection name

# Declare dis2 as a global variable
dis2 = None
json_data_dis2 = None

os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"] = "https://hgsgeneralpurposeidp.cognitiveservices.azure.com/"
os.environ["DOCUMENTINTELLIGENCE_API_KEY"] = "97cb5410020448ea80fc685e4841d766"
os.environ["BLOB_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=costumerdocuments;AccountKey=1yqcWOTGOqmCRYlp/msirGkI+LfaFLQHdBi1Vr1vtvsUxUWYDAXkv/uVONOppB1+GMqsaNgUlhbR+AStN38s3A==;EndpointSuffix=core.windows.net"

def analyze_identity_documents():
    global dis2 
    global json_data_dis2
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest

    # For how to obtain the endpoint and key, please see PREREQUISITES above.
    endpoint = os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCUMENTINTELLIGENCE_API_KEY"]

    document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # If analyzing a local document, remove the comment markers (#) at the beginning of these 8 lines.
    # Delete or comment out the part of "Analyze a document at a URL" above.
    # Replace <path to your sample file>  with your actual file path.
    path_to_sample_document = r"C:\Users\nisch\OneDrive\Desktop\HGS\Retail Mortgage\Python_DI\sample documents\license.jpg"
    with open(path_to_sample_document, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-idDocument", analyze_request=f, content_type="application/octet-stream"
        )

    id_documents: AnalyzeResult = poller.result()

    # Print everything in id_documents.documents
    if id_documents.documents:
        for idx, id_document in enumerate(id_documents.documents):
            # print(f"--------Analyzing ID document #{idx + 1}--------")
            document_in_dict = id_document.as_dict()  # Using pprint to print the dictionary in a readable format
            # Create dis2 by copying dis1 (to keep original intact)
            dis2 = document_in_dict.copy()
            json_data_dis2 = json.dumps(dis2, indent=4)
            data = json.loads(json_data_dis2)

            # Insert the data into MongoDB
            collection.insert_one(data)
            print("Data saved")


            # with open('dis1_data_to_json.json', 'w') as file:
            #     file.write(json_data_dis2)
            
            # print("JSON data saved to dis1_data.json")
    else:
        print("No documents found.")

if __name__ == "__main__":
    from azure.core.exceptions import HttpResponseError
    from dotenv import find_dotenv, load_dotenv

    try:
        load_dotenv(find_dotenv())
        analyze_identity_documents()
    except HttpResponseError as error:
        # Examples of how to check an HttpResponseError
        # Check by error code:
        if error.error is not None:
            if error.error.code == "InvalidImage":
                print(f"Received an invalid image error: {error.error}")
            if error.error.code == "InvalidRequest":
                print(f"Received an invalid request error: {error.error}")
            # Raise the error again after printing it
            raise
        # If the inner error is None and then it is possible to check the message to get more information:
        if "Invalid request".casefold() in error.message.casefold():
            print(f"Uh-oh! Seems there was an invalid request: {error}")
        # Raise the error again
        raise


