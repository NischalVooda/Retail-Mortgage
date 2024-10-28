from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
import random
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.storage.blob import BlobServiceClient
import pymongo
from datetime import datetime
import requests  # Add this line to import the requests library


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://nischal:nischal@cluster0.sab29.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["idDocument"]
collection = db["borrower"]

# Set environment variables (or load from .env)
os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"] = "https://hgsgeneralpurposeidp.cognitiveservices.azure.com/"
os.environ["DOCUMENTINTELLIGENCE_API_KEY"] = "97cb5410020448ea80fc685e4841d766"
os.environ["BLOB_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=costumerdocuments;AccountKey=1yqcWOTGOqmCRYlp/msirGkI+LfaFLQHdBi1Vr1vtvsUxUWYDAXkv/uVONOppB1+GMqsaNgUlhbR+AStN38s3A==;EndpointSuffix=core.windows.net"

# File upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create the BlobServiceClient using the connection string
blob_service_client = BlobServiceClient.from_connection_string(os.environ["BLOB_CONNECTION_STRING"])
container_name = "input"

def upload_blob_file(blob_service_client: BlobServiceClient, container_name: str, local_file_path: str, blob_name: str):
    container_client = blob_service_client.get_container_client(container=container_name)

    # Upload the local file to the blob container
    with open(local_file_path, "rb") as data:
        blob_client = container_client.upload_blob(name=blob_name, data=data, overwrite=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        flash('No selected files')
        return redirect(request.url)

    for file in files:
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Generate a random 6-digit value and construct the blob name
            random_value = str(random.randint(100000, 999999))  # Generate a random 6-digit number
            blob_name = f"{file.filename.split('.')[0]}_{random_value}.{file.filename.split('.')[-1]}"  # Construct the final blob name

            # Upload the file to Blob Storage
            upload_blob_file(blob_service_client, container_name, file_path, blob_name)

            # Process the document and store the results in MongoDB
            analyze_identity_documents(file_path)

    flash('Files successfully uploaded, processed, and stored!')
    return redirect(url_for('index'))

def analyze_identity_documents(path_to_sample_document):
    # Azure Document Intelligence credentials
    endpoint = os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCUMENTINTELLIGENCE_API_KEY"]

    # Initialize the client
    document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Analyze the document
    with open(path_to_sample_document, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-idDocument", analyze_request=f, content_type="application/octet-stream"
        )

    id_documents: AnalyzeResult = poller.result()

    license_exp = False

    # Process the extracted document fields
    if id_documents.documents:
        for id_document in id_documents.documents:
            document_in_dict = id_document.as_dict()

            # Check if the docType is 'idDocument.driverLicense'
            if document_in_dict.get('docType') == "idDocument.driverLicense":
                # Extract DateOfExpiration
                date_of_expiration = document_in_dict["fields"]["DateOfExpiration"]["valueDate"]
                date_of_expiration = datetime.strptime(date_of_expiration, "%Y-%m-%d")
                
                # Get current date from WorldTime API
                response = requests.get("http://worldtimeapi.org/api/timezone/America/Chicago")
                if response.status_code == 200:
                    current_date_str = response.json()["datetime"].split("T")[0]  # Extract date part
                    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
                    
                    # Compare the dates
                    if current_date > date_of_expiration:
                        license_exp = True
                    else:
                        license_exp = False
        
                # Add the license_exp status to the document dictionary
                document_in_dict["license_expired"] = license_exp


            # Convert the document dictionary to JSON
            data = json.loads(json.dumps(document_in_dict))
            
            # Insert data into MongoDB
            collection.insert_one(data)

if __name__ == '__main__':
    app.run(debug=True)
