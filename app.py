'''must install flask environment before running scipt
    run this in the shell:
    
    pip install flask schedule pandas


    if running on local machine, follow instructions in this webpage:
    https://flask.palletsprojects.com/en/3.0.x/installation/#python-version
    need to set up virtual environment on local machine
'''

#import flask, only place flask import needed
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import subprocess
import logging
import schedule
import time
import pandas as pd
from threading import Thread
from datetime import datetime, timedelta


app = Flask(__name__)

app.secret_key = "SecretKey"


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variable to store the scheduled percentage and time
scheduled_percentage = 50
scheduled_time = None

def set_cpu_percentage(percentage):
    try:
        # Update process_name to the actual process name
        subprocess.run(['sudo', 'cpulimit', '-l', str(percentage), '-e', 'process_name'])
        logger.info(f'CPU usage set to {percentage}%')
    except Exception as e:
        logger.error(f'Error setting CPU usage: {str(e)}')

def scheduled_job():
    global scheduled_percentage
    set_cpu_percentage(scheduled_percentage)

# Schedule the job to run every minute
schedule.every(1).minutes.do(scheduled_job)

def schedule_runner():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the schedule runner in a separate thread
schedule_thread = Thread(target=schedule_runner)
schedule_thread.start()

def schedule_cpu_at_time(percentage, time_str):
    global scheduled_percentage, scheduled_time

    try:
        scheduled_percentage = percentage
        scheduled_time = datetime.strptime(time_str, '%H:%M').time()

        now = datetime.now().time()
        time_difference = datetime.combine(datetime.today(), scheduled_time) - datetime.combine(datetime.today(), now)

        # If the scheduled time is in the future, schedule the job
        if time_difference.total_seconds() > 0:
            schedule.every().day.at(time_str).do(scheduled_job)
            return True, None
        else:
            return False, 'Scheduled time should be in the future'
    except ValueError:
        return False, 'Invalid time format'



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

@app.route('/load_management')
def index():
    return render_template('load_management.html')

@app.route('/set-cpu-usage', methods=['POST'])
def set_cpu_usage():
    percentage = int(request.json.get('percentage', 50))

    if 0 <= percentage <= 100:
        set_cpu_percentage(percentage)
        return jsonify({'success': True, 'message': f'Immediate CPU usage set to {percentage}%'})
    else:
        return jsonify({'error': 'Invalid percentage value'}), 400

@app.route('/schedule-cpu-usage', methods=['POST'])
def schedule_cpu_usage():
    percentage = int(request.json.get('percentage', 50))
    time_str = request.json.get('time', '')

    success, message = schedule_cpu_at_time(percentage, time_str)

    if success:
        return jsonify({'success': True, 'message': f'Scheduled CPU usage set to {percentage}% at {time_str}'})
    else:
        return jsonify({'error': message}), 400
    
@app.route('/get-cpu-data')
def get_cpu_data():
    # Read data from CSV file
    df = pd.read_csv('cpu_data.csv')

    # Return data in JSON format
    data = {
        'labels': df['Timestamp'].tolist(),  # Assuming 'Timestamp' is a column in your CSV
        'data': df['CPU Usage'].tolist(),    # Assuming 'CPU Usage' is a column in your CSV
    }

    return jsonify(data)


@app.route('/get-solar-energy-data')
def get_solor_energy_data():
    # Read data from CSV file
    dfl = pd.read_csv('solar_energy_data.csv')

    # Return data in JSON format
    data= {
        'labels': dfl['time'].tolist(),  # Assuming 'Time' is a column in your CSV
        'data': dfl['generation_solar'].tolist(),    # Assuming 'solar' is a column in your CSV
    }

    return jsonify(data)

@app.route('/get-wind-energy-data')
def get_wind_energy_data():
    # Read data from CSV file
    df2 = pd.read_csv('wind_energy_data.csv')

    # Return data in JSON format
    data= {
        'labels': df2['time'].tolist(),  # Assuming 'Time' is a column in your CSV
        'data': df2['generation_wind'].tolist(),    # Assuming 'solar' is a column in your CSV
    }

    return jsonify(data)

#run app
if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
