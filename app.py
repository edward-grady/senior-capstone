'''must install flask environment before running scipt
    run this in the shell:
    
    pip install flask


    if running on local machine, follow instructions in this webpage:
    https://flask.palletsprojects.com/en/3.0.x/installation/#python-version
'''

#import flask, only place flask import needed
from flask import Flask, render_template

app = Flask(__name__)


#home page
@app.route("/")
def home_page():
  return render_template('home.html')


#stress-ng page websitename.com/stress_ng
@app.route("/stress_ng")
def stress_ng_page():
  return render_template('index.html')


#load management page websitename.com/load_management
@app.route("/load_management")
def load_management_page():
  return "load-management"


#run app
if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
