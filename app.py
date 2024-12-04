DEBUG = True

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from flask_socketio import SocketIO, emit
import sqlite3

import threading


if DEBUG:
    import os
    os.remove("./data/srcml.db3")

import srcml_database
from srcml_analysis import *

app = Flask(__name__)
socket_io = SocketIO(app)

srcml_database._create_database()


@app.route('/clone', methods=['GET', 'POST'])
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

        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/')
@app.route('/home')
def home():
    return redirect(url_for('index'))

@app.route('/table/<table_name>')
def table_view(table_name=None):
    table_names = srcml_database.fetch_table_names()

    if table_names == []:
        columns = []
        rows = []
        return render_template('database.html', columns=columns, rows=rows, table_name="", table_names=table_names)

        # return redirect(url_for('index'))
    else:
        columns, rows = srcml_database.fetch_table_data(table_name)
        print(rows)
    return render_template('database.html', columns=columns, rows=rows, table_name=table_name, table_names=table_names)




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
    socket_io.emit("finish",{'redirect':f'/home'})

if __name__ == '__main__':
    app.run(debug=True)
