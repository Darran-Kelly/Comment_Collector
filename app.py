"""
    Author: Darren Kelly
    Student NO: C00191188
"""



from __future__ import print_function

import httplib2
import pymongo
import csv
import flask


from apiclient import discovery
from flask import Flask, render_template, request, send_file, session
from dict_query import DictQuery
from oauth2client import client
from oauth2client import tools


try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

app = Flask(__name__)

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

@app.route('/')
def welcome():
    return render_template('index.html')


@app.route('/tutorial', methods=['post', 'get'])
def tutorial():
    return render_template('tutorial.html')

@app.route('/displayFiles', methods=['post', 'get'])
def display_files():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))

    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    results = service.files().list(
            pageSize=10, fields='files(name, id)').execute()

    filesN = []
    filesID = []
    for i in DictQuery(results).get('files/name'):
        filesN.append(i)
    for k in DictQuery(results).get('files/id'):
        filesID.append(k)
    return render_template('files.html', filesN=filesN, filesID=filesID)

@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets('client_secret.json',
                                            scope='https://www.googleapis.com/auth/drive',
                                            redirect_uri=flask.url_for('oauth2callback', _external=True))
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('display_files'))


@app.route('/storeCommentsAsCSV', methods=['POST', 'GET'])
def retrieve_comments():
    try:
        db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
        data=db[session['collection']].find({},{'_id':0})
        with open('/home/DocumentCommentCollector/mysite/yourComments.csv', 'w+', newline='') as f:
            f = csv.writer(f)
            for i in data :
                f.writerow([str(i)])
                f.writerow('')
        return send_file('yourComments.csv',
                     mimetype='text/csv',
                     attachment_filename='yourComments.csv',
                     as_attachment=True)
    except:
        return render_template('queryComments.html')





@app.route('/displayComments', methods=['post'])
def display_comments_form_recent_files():
    fileId = request.form['button']
    session['FileId'] = fileId
    return render_template('displayComments.html')


@app.route('/displayURL', methods=['post', 'get'])
def display_comments_form_url():
    id = request.form['url']
    url = id.split("/")[1:]
    fileId = ''
    for i in url:
        if len(i) >= 10:
            fileId = i
    session['FileId'] = fileId
    return render_template('displayComments.html')


@app.route('/advancedQuery', methods=['get', 'post'])
def custom_query():
    condition = request.form['condition']
    value = request.form['value']
    db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
    data = db[session['collection']].find({condition: value}, {"_id": 0})

    with open('/home/DocumentCommentCollector/mysite/CommentsbyQuote.csv', 'w+', newline='') as f:
        f = csv.writer(f)
        for i in data :
            f.writerow([str(i)])
            f.writerow('')
    return send_file('CommentsbyQuote.csv',
                     mimetype='text/csv',
                     attachment_filename='CommentsbyQuote.csv',
                     as_attachment=True)


@app.route('/query', methods=['post', 'GET'])
def get_to_the_files():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
    id = session['FileId']
    comments = service.comments().list(fileId=id,
                                           fields='comments').execute()
    collection=session['collection']=request.form['collectionN']
    for i in DictQuery(comments).get('comments'):
        db[collection].insert({"comments": i})
    return render_template('queryComments.html')

@app.route("/authorQ", methods=['post', 'get'])
def authorQ():
    return render_template('authorQuerys.html')


@app.route("/commentsByAuthor", methods=['post', 'get'])
def author_query():
    author = request.form['author']
    db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
    data = db[session['collection']].find({"comments.author.displayName": author}, {"_id": 0})

    with open('/home/DocumentCommentCollector/mysite/comment_by_author.csv', 'w+', newline='') as f:
        f = csv.writer(f)
        for i in data :
            f.writerow([str(i)])
            f.writerow('')
    return send_file('comment_by_author.csv',
                         mimetype='text/csv',
                         attachment_filename='comment_by_author.csv',
                         as_attachment=True)


@app.route("/commentsByTime", methods=['post'])
def date_query():
    date = request.form['Date']
    time = request.form['Time']
    db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
    data = db[session['collection']].find({"comments.createdTime": date + 'T' + time + 'Z'}, {"_id": 0})

    with open('/home/DocumentCommentCollector/mysite/Commentsbytime.csv', 'w+', newline='') as f:
        f = csv.writer(f)
        for i in data :
            f.writerow([str(i)])
            f.writerow('')
        return send_file('Commentsbytime.csv',
                         mimetype='text/csv',
                         attachment_filename='Commentsbytime.csv',
                         as_attachment=True)


@app.route("/commentsByAuthorCount", methods=['post'])
def comment_count():
    author = request.form['author']
    db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
    data = list(db[session['collection']].find({"comments.author.displayName": author}, {"_id": 0}))
    count = 0
    for i in data:
        count += 1
    return render_template('authorQuerys.html', count=count, data=data)


@app.route("/commentsByQuote", methods=['post', 'get'])
def comment_by_quote():
    quote = request.form['quote']
    db= pymongo.MongoClient("mongodb://admin:admin@ds143241.mlab.com:43241/commentcollector").commentcollector
    data = db[session['collection']].find({"comments.quotedFileContent.value": quote}, {"_id": 0})

    with open('/home/DocumentCommentCollector/mysite/CommentsbyQuote.csv', 'w+') as f:
        f = csv.writer(f)
        for i in data:
            f.writerow([str(i)])
            f.writerow('')
    return send_file('CommentsbyQuote.csv',
                     mimetype='text/csv',
                     attachment_filename='CommentsbyQuote.csv',
                     as_attachment=True)

if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.debug = True
    app.run()
