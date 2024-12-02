DEBUG = True

from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO

import threading


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
    socket_io.emit("finish",{'redirect':f'/repo/{repo_name}'})




if __name__ == '__main__':
    app.run(debug=True)
