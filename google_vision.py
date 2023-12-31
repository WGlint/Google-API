import argparse
import os
import subprocess
import logging
import requests
import random
from pprint import pprint

logging.basicConfig(level=logging.CRITICAL)

parser = argparse.ArgumentParser('Use Google API for create label in picture')
parser.add_argument('image', help='Name of image for create label')
parser.add_argument('json_api', help='Name of json file for use google api')

# Argument for supabase
parser.add_argument('--url', '-u', help='Url of supabase', type=str)
parser.add_argument('--key', '-k', help='Key of supabase ( NEED SERVICE ROLE KEY ! )', type=str)
parser.add_argument('--bucket', '-b', help='Name of bucket for upload picture', type=str)
# Argument for google api
parser.add_argument('--nLabel', '-n', help='Number of label for create', type=int)


""" INSTALL ALL LIBRARY FOR USE GOOGLE API """
subprocess.run([
    "pip3", "install", "--upgrade", "google-cloud-vision",
])
subprocess.run([
    "pip3", "install", "Pillow", "supabase", "load-bar", "python-magic"
])
subprocess.run([
    "clear"
])

import loadbar
import mimetypes
import google.auth.transport.requests
from supabase import create_client, Client, StorageException
from PIL import Image
from google.oauth2 import service_account

class AILabel:
    def __init__(self, url_supabase : str, key_supabase : str, name_folder : str, bucket : str, json_api : str, nLabel : str):
        self.supabase = self.create_supabase(url_supabase, key_supabase)
        self.racine_root = os.getcwd()
        self.name_folder = name_folder
        self.bucket = bucket
        self.json_api = json_api
        self.number_label = nLabel  
        self.api_url = "https://vision.googleapis.com/v1/images:annotate"

        # Launch function
        self.create_label()

    def payload_element(self, url : str):
        return {
            "features": [ { "maxResults": self.number_label, "type": "LABEL_DETECTION" } ],
            "image": { "source": { "imageUri": url } }
        }

    def create_payload(self, public_url : list) -> dict:
        payload = {
            "requests": []
        }
        for url in public_url:
            payload["requests"].append(self.payload_element(url["url"]))
        return payload

    def get_mile_type(self, filepath : str) -> str:
        mime_type, _ = mimetypes.guess_type(filepath)
        return mime_type

    def create_supabase(self, url : str, key : str):
        supabase: Client = create_client(url,key)
        return supabase

    def upload_folder_to_supabase(self, path_to_file : str, bucket : str) -> list:
        all_public_url: list = []
        all_picture_in_folder = os.listdir(path_to_file)
        if not os.path.exists(os.path.join(self.racine_root, f"{self.name_folder}_webp")):
            name_folder_webp: str = f"{self.name_folder}_webp"
            os.makedirs(os.path.join(self.racine_root, name_folder_webp))
        else:
            name_folder_webp: str = f"{self.name_folder}_webp_{random.randint(0, 1000)}"
            print(f"Folder {self.name_folder}_webp already exist, create another folder")
            os.makedirs(os.path.join(self.racine_root, name_folder_webp))

        print(f"\nSTEP 1/5 : Upload {len(all_picture_in_folder)} picture to supabase")
        bar = loadbar.LoadBar(max=len(all_picture_in_folder))
        bar.start()
        for i,picture in enumerate(all_picture_in_folder):
            if str(self.get_mile_type(os.path.join(path_to_file, picture))).split("/")[0] == "image":
                path_to_picture_webp = os.path.join(self.racine_root, name_folder_webp, f'{picture.split(".")[0]}.webp')
                with Image.open(os.path.join(path_to_file, picture)) as im:
                    im.save(path_to_picture_webp, 'WEBP')
                try : 
                    with open(path_to_picture_webp, 'rb') as f:
                        self.supabase.storage.from_(bucket).upload(
                            file=f,
                            path=f'photo/{picture.split(".")[0]}.webp',
                            file_options={"content-type": self.get_mile_type(path_to_picture_webp)}
                        )
                except StorageException:
                        pass

                all_public_url.append(
                    {
                        "name": picture.split(".")[0],
                        "url": str(self.supabase.storage.from_(bucket).get_public_url(f'photo/{picture.split(".")[0]}.webp'))
                    }
                )
            bar.update()
        bar.end()
        print(f"{len(all_picture_in_folder)} picture upload to supabase\n\n")

        return all_public_url
    
    def get_access_token(self, json_api : str) -> str:
        print(f"\nSTEP 2/5 : Get access token for use google api")
        SERVICE_ACCOUNT_FILE = os.path.join(self.racine_root, json_api)
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        print(f"SUCCES ! Acces token : {str(credentials.token)[:20]}...\n\n")

        return credentials.token

    def create_list_label(self, response : dict, url : list) -> list:
        list_label = []
        for i, element in enumerate(url):
            labels = []
            try :
                for label in response["responses"][i]["labelAnnotations"]:
                    labels.append({
                        label["description"] : label["score"]
                    })
                list_label.append(
                    {
                        "name": element["name"],
                        "label": labels
                    }
                )
            except KeyError:
                print(f"\n\nWARNING ! Picture {element['name']} it's not download by Google ! \n\n")

        return list_label

    def create_file_label(self, list_label : dict):
        all_word = set()
        label_file_name = f"{self.name_folder}_label"

        for element in list_label:
            for label_word in element["label"]:
                all_word.add(next(iter(label_word)))

        os.makedirs(os.path.join(self.racine_root, label_file_name))

        bar2 = loadbar.LoadBar(max=len(all_word))
        bar2.start()

        for label_word in all_word:
            os.makedirs(os.path.join(self.racine_root, label_file_name, label_word), exist_ok=True)

        for lab in all_word:
            bar2.update()
            label_path = os.path.join(self.racine_root, label_file_name, lab)
            for i,label_picture in enumerate(list_label):
                for label_picture_word in label_picture["label"]:
                    if (lab == next(iter(label_picture_word))):
                        for input_picture in os.listdir(os.path.join(self.racine_root, self.name_folder)):
                            if (input_picture.split(".")[0] == label_picture['name']):
                                with Image.open(os.path.join(self.racine_root, self.name_folder, input_picture)) as f:
                                    f.save(os.path.join(label_path, f"{int(label_picture_word[lab]*100)}_{label_picture['name']}.webp"), "WEBP")
            
        bar2.end()

    def create_label(self):
        public_url = self.upload_folder_to_supabase(os.path.join(self.racine_root, self.name_folder), bucket=self.bucket)
        
        token_vision = self.get_access_token(self.json_api)

        payload = self.create_payload(public_url)

        headers = {
            'Authorization': f'Bearer {token_vision}',
            'Content-Type': 'application/json'
        }

        print(f"\nSTEP 3/5 : Send request to google api")
        response = requests.post(self.api_url, headers=headers, json=payload)
        print(f"SUCCES !\n\n")

        print(f"\nSTEP 4/5 : Create label in supabase")
        list_label = self.create_list_label(response.json(), public_url)
        print(f"SUCCES !\n\n")

        print(f"\nSTEP 5/5 : Create label in supabase")
        self.create_file_label(list_label)
        print(f"SUCCES ! It's Over\n\n")

        print(f"Delete picture storage in supabase...")
        for picture in os.listdir(os.path.join(self.racine_root, self.name_folder)):
            self.supabase.storage.from_(self.bucket).remove(f"photo/{picture}")
        print(f"DONE !")
        
if __name__ == '__main__':
    args = parser.parse_args()

    create_label = AILabel(
        url_supabase="https://tqolweoqyhlblpkdcule.supabase.co",
        key_supabase="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxb2x3ZW9xeWhsYmxwa2RjdWxlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY5NTU3MzE2NSwiZXhwIjoyMDExMTQ5MTY1fQ.CCbgp-12qdtFVAYlwKZSrrRZPVsw5ZFPImYL6bc72uM",
        name_folder=args.image,
        bucket=args.bucket,
        json_api="formazone-8e53616858ff.json",
        nLabel=args.nLabel
    )