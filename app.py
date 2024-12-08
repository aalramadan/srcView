DEBUG = True

from flask import Flask, render_template, request, redirect, send_file
from flask_socketio import SocketIO
from flask_socketio import SocketIO, emit

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
def repos():
    if request.method == 'POST':
        repo_id = request.form['repo_id']
        success = srcml_database.remove_repo(repo_id)
        if success:
            return redirect('/')  # Redirect to refresh the page

    # For GET requests, retrieve and display repositories
    repos = srcml_database.retrieve_repos()
    return render_template('repos.html', repos=repos)

@app.route('/add', methods=['GET', 'POST'])
def add_repo():
    if request.method == 'GET':
        return render_template('add_repo.html')

    if request.method == 'POST':
        # filePath = request.form['filePath']
        github_link = request.form['githubLink']
        # You can replace the following line with actual srcML processing logic
        result = f"Executing srcML for the GitHub repository: {github_link}"

        thread = threading.Thread(target=process_github_link,args=(github_link,))
        thread.start()

        return render_template('add_repo.html', result=result)
    return render_template('add_repo.html')


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
    socket_io.emit("finish",{'redirect':f'/'})


@app.route('/files/<repo_id>')
def list_files(repo_id):
    navbar = []
    navbar.append(["Home", ""])
    files = srcml_database.retrieve_files(repo_id)
    return render_template('files.html', files=files,repo=srcml_database.get_repo_name_from_id(repo_id), navbar=navbar)

@app.route('/identifiers/file/<file_id>')
def list_identifiers(file_id):
    navbar = []
    navbar.append(["Home", ""])
    identifiers = srcml_database.retrieve_identifiers(file_id)
    return render_template('identifiers.html', identifiers=identifiers,display=srcml_database.get_file_name_from_id(file_id), navbar=navbar)

@app.route('/identifiers/repo/<repo_id>')
def list_identifiers_from_repo(repo_id):
    navbar = get_navbar_links(repo_id)
    identifiers = srcml_database.retrieve_identifiers_from_repo(repo_id)
    return render_template('identifiers.html', identifiers=identifiers,display=srcml_database.get_repo_name_from_id(repo_id), navbar=navbar)

@app.route('/tags/file/<file_id>')
def list_tags(file_id):
    navbar = get_navbar_links(repo_id)
    tags = srcml_database.retrieve_tags(file_id)
    return render_template('tags.html', tags=tags,display=srcml_database.get_file_name_from_id(file_id), navbar=navbar)

@app.route('/tags/repo/<repo_id>')
def list_tags_from_repo(repo_id):
    navbar = get_navbar_links(repo_id)
    tags = srcml_database.retrieve_tags_from_repo(repo_id)
    print(dict(tags))
    return render_template('tags.html', tags=tags,display=srcml_database.get_repo_name_from_id(repo_id), navbar=navbar)

@app.route('/xpath_run/repo/<repo_id>',methods=['GET', 'POST'])
def xpath_on_repo(repo_id):
    navbar = get_navbar_links(repo_id)
    if request.method == 'GET':
        return render_template('run_xpath.html', navbar=navbar)
    if request.method == 'POST':
        xpath = request.form['xpath']
        thread = threading.Thread(target=execute_xpath_on_repo,args=(repo_id,xpath))
        thread.start()

        result="Running your XPath!"
        return render_template('run_xpath.html', result=result, navbar=navbar)

def execute_xpath_on_repo(repo_id,xpath):
    run_xpath_on_repo(repo_id,xpath)
    socket_io.emit("finish",{'redirect':'/repos'})

def get_navbar_links(repo_id):
    nav_links = []
    table_names = srcml_database.fetch_table_names()
    for table in table_names:  
        if table == 'repository':
            nav_links.append(["Home", ""])
        # elif table == 'sqlite_sequence':
        #     nav_links.append(["Identifiers", "identifiers/repo/"+repo_id])
        elif table == 'file':
            nav_links.append(["Files", "files/"+repo_id])
        elif table == 'identifier':
            nav_links.append(["Identifiers", "identifiers/repo/"+repo_id])
        elif table == 'tag_count':
            nav_links.append(["Tags", "tags/repo/"+repo_id])
        elif table == 'query_run':
            nav_links.append(["XPath", "xpath_run/repo/"+repo_id])
        elif table == 'query_run_result':
            nav_links.append(["srcQL", "srcql_run/repo/"+repo_id])
    nav_links.append(["Download", "download/repo/"+repo_id])
    return nav_links

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
