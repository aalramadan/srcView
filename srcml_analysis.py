import requests
import os
import subprocess

#import pylibsrcml

"""
To download from GitHub:

Input Link: https://github.com/srcML/srcML
Download Link: https://github.com/srcML/srcML/archive/refs/heads/master.zip

"""

def download_github_repo(github_link):
    repo_name = "/".join(github_link.split("/")[-2:])
    download_link = github_link + "/archive/refs/heads/master.zip"
    save_location = "data/"+repo_name
    print(repo_name)
    if not os.path.isdir(save_location):
        os.makedirs(save_location)

    print("Downloading")
    #download the code
    response = requests.get(download_link,stream=True)
    if response.status_code == 200:
        with open(save_location+"/code.zip",'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    return False

def convert_to_srcml(repo_name,get_position=False):
    if not get_position:
        command = ["srcml","data/"+repo_name+"/code.zip","-o","data/"+repo_name+"/code.xml"]
    else:
        command = ["srcml","--position","data/"+repo_name+"/code.zip","-o","data/"+repo_name+"/code_pos.xml"]

    result = subprocess.run(command)

    if result.returncode == 0:
        return True
    else:
        return False

