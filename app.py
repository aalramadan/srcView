DEBUG = True

from flask import Flask, render_template, request, redirect, send_file
from flask_socketio import SocketIO

import threading
import io


if DEBUG:
    import os
    os.remove("./data/srcml.db3")

import srcml_database
from srcml_analysis import *







app = Flask(__name__)
socket_io = SocketIO(app)

srcml_database._create_database()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    if request.method == 'POST':
        # filePath = request.form['filePath']
        github_link = request.form['githubLink']
        # You can replace the following line with actual srcML processing logic
        result = f"Executing srcML for the GitHub repository: {github_link}"

        thread = threading.Thread(target=process_github_link,args=(github_link,))
        thread.start()

        return render_template('index.html', result=result)
    return render_template('index.html')


def process_github_link(github_link):
    socket_io.emit("update",{'message':'Downloading...'})
    status = download_github_repo(github_link)
    if status:
        socket_io.emit("update",{'message':'Downloaded the file!'})
    else:
        socket_io.emit("update",{'message':'Error downloading the file.'})
        return


    socket_io.emit("update",{'message':'Converting to srcML...'})

    repo_name = "/".join(github_link.split("/")[-2:])
    status = convert_to_srcml(repo_name) and convert_to_srcml(repo_name,True) and add_srcml_to_database(repo_name)
    if status:
        socket_io.emit("update",{'message':'Converted!'})
    else:
        socket_io.emit("update",{'message':'Error!'})
        return

    socket_io.emit("update",{'message':'Running stereocode...'})
    status = run_stereocode(repo_name)
    if status:
        socket_io.emit("update",{'message':'Stereotyped!'})
    else:
        socket_io.emit("update",{'message':'Error!'})
        return

    socket_io.emit("update",{'message':'Collecting names...'})
    status = run_namecollector(repo_name) and add_names_to_database(repo_name)
    if status:
        socket_io.emit("update",{'message':'Collected!'})
    else:
        socket_io.emit("update",{'message':'Error!'})
        return

    socket_io.emit("update",{'message':'Counting tags...'})
    status = count_tags(repo_name)
    if status:
        socket_io.emit("update",{'message':'Counted!'})
    else:
        socket_io.emit("update",{'message':'Error!'})
        return

    socket_io.emit("update",{'message':'Done! Redirecting...'})
    socket_io.emit("finish",{'redirect':f'/files/{srcml_database.get_repo_id_from_name(repo_name)}'})



@app.route('/repos')
def repos():
    repos = srcml_database.retrieve_repos()
    return render_template('repos.html', repos=repos)

@app.route('/files/<repo_id>')
def list_files(repo_id):
    files = srcml_database.retrieve_files(repo_id)
    return render_template('files.html', files=files,repo=srcml_database.get_repo_name_from_id(repo_id))

@app.route('/identifiers/file/<file_id>')
def list_identifiers(file_id):
    identifiers = srcml_database.retrieve_identifiers(file_id)
    return render_template('identifiers.html', identifiers=identifiers,display=srcml_database.get_file_name_from_id(file_id))

@app.route('/identifiers/repo/<repo_id>')
def list_identifiers_from_repo(repo_id):
    identifiers = srcml_database.retrieve_identifiers_from_repo(repo_id)
    return render_template('identifiers.html', identifiers=identifiers,display=srcml_database.get_repo_name_from_id(repo_id))

@app.route('/tags/file/<file_id>')
def list_tags(file_id):
    tags = srcml_database.retrieve_tags(file_id)
    return render_template('tags.html', tags=tags,display=srcml_database.get_file_name_from_id(file_id))

@app.route('/tags/repo/<repo_id>')
def list_tags_from_repo(repo_id):
    tags = srcml_database.retrieve_tags_from_repo(repo_id)
    print(dict(tags))
    return render_template('tags.html', tags=tags,display=srcml_database.get_repo_name_from_id(repo_id))


@app.route('/xpath_run/repo/<repo_id>',methods=['GET', 'POST'])
def xpath_on_repo(repo_id):
    if request.method == 'GET':
        return render_template('run_xpath.html')
    if request.method == 'POST':
        xpath = request.form['xpath']
        thread = threading.Thread(target=execute_xpath_on_repo,args=(repo_id,xpath))
        thread.start()

        result="Running your XPath!"
        return render_template('run_xpath.html', result=result)

def execute_xpath_on_repo(repo_id,xpath):
    run_xpath_on_repo(repo_id,xpath)
    socket_io.emit("finish",{'redirect':'/repos'})



@app.route('/download/file/<file_id>', methods=['GET'])
def download_file(file_id):
    repo_name = srcml_database.get_repo_name_from_file_id(file_id)
    file_name = srcml_database.get_file_name_from_id(file_id)
    file_buffer = io.BytesIO()
    file_buffer.write(get_unit_text(repo_name,file_name))
    file_buffer.seek(0)

    return send_file(file_buffer,as_attachment=True,download_name=file_name.split("/")[-1],mimetype="text/plain")

@app.route('/download/repo/<repo_id>', methods=['GET'])
def download_repo(repo_id):
    return send_file("data/"+srcml_database.get_repo_name_from_id(repo_id)+"/code.xml")


if __name__ == '__main__':
    app.run(debug=True)
