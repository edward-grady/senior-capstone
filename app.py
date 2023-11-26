'''must install flask environment before running scipt
    run this in the shell:
    
    pip install flask


    if running on local machine, follow instructions in this webpage:
    https://flask.palletsprojects.com/en/3.0.x/installation/#python-version
    need to set up virtual environment on local machine
'''

#import flask, only place flask import needed
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

app.secret_key = "SecretKey"


#login page
@app.route('/', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    if username == 'admin' and password == 'admin':
      session['logged_in'] = True
      return redirect(url_for('home_page'))
    else:
      return render_template('login.html',
                             error='Invalid username or password')
  else:
    return render_template('login.html')


#logout
@app.route('/logout')
def logout():
  session.pop('username', None)
  return redirect(url_for('login'))


#home page
@app.route("/home")
def home_page():
  return render_template('home.html')


#stress-ng page websitename.com/stress_ng
@app.route("/stress_ng")
def stress_ng_page():
  return render_template('stress_ng.html')


#load management page websitename.com/load_management
@app.route("/load_management")
def load_management_page():
  return render_template('load_management.html')




#run app
if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
