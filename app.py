from flask import Flask, render_template, request
from flask_socketio import SocketIO

import threading


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


    socket_io.emit("update",{'message':'Converting to srcML...'})

    repo_name = "/".join(github_link.split("/")[-2:])
    status = convert_to_srcml(repo_name) and convert_to_srcml(repo_name,True)

    if status:
        socket_io.emit("update",{'message':'Converted!'})


    status = add_srcml_to_database(repo_name)




if __name__ == '__main__':
    app.run(debug=True)
