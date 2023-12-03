from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_restx import Api, Resource, reqparse, fields
import subprocess
import logging
import schedule
import time
import pandas as pd
from threading import Thread
from datetime import datetime, timedelta

app = Flask(__name__)
api = Api(app, doc='/swagger', title='Stress-ng Test API',
          description='A simple API for running stress-ng tests.')
local_stress_test_namespace = api.namespace('local_stress_test', description='Local Stress Tests')
stress_ng_test_namespace = api.namespace('remote_server_stress-test', description='Remote Stress Tests')
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


# Login page
@app.route('/login', methods=['GET', 'POST'])
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


# Logout
@app.route('/logout')
def logout():
  session.pop('username', None)
  return redirect(url_for('login'))


# Home page
@app.route("/home")
def home_page():
  return render_template('home.html')


# Stress_ng page
@app.route("/stress_ng")
def stress_ng_page():
  return render_template('stress_ng.html')


# Stress-ng API routes
output_model = api.model('Output', {'output': fields.String})


# Stress CPU parser
stress_cpu_parser = reqparse.RequestParser()
stress_cpu_parser.add_argument('cpu_workers', type=int, default=1, help='Number of workers')
stress_cpu_parser.add_argument('stress_time', type=int, default=60, help='Stress time in seconds')

# Stress Memory parser
stress_memory_parser = reqparse.RequestParser()
stress_memory_parser.add_argument('stress_time', type=int, default=60, help='Stress time in seconds')
stress_memory_parser.add_argument('vm_bytes', type=str, default='512M', help='Percentage of memory using all the vm stressors')
stress_memory_parser.add_argument('vm_stressors', type=int, default=1, help='Number of vm stressors')

# Stress IO parser
stress_io_parser = reqparse.RequestParser()
stress_io_parser.add_argument('io_workers', type=int, default=1, help='Number of I/O workers')
stress_io_parser.add_argument('stress_time', type=int, default=60, help='Stress time in seconds')

common_parser = reqparse.RequestParser()
common_parser.add_argument('io_workers',
                           type=int,
                           default=1,
                           help='Number of I/O workers')
common_parser.add_argument('stress_time',
                           type=int,
                           default=60,
                           help='Stress time in seconds')



def format_output(output):
  return '<br>'.join(output.split('\n'))


@local_stress_test_namespace.route('/stress_cpu')
class StressCpuResource(Resource):

    @api.expect(stress_cpu_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = stress_cpu_parser.parse_args()
        cpu_workers = args['cpu_workers']
        stress_time = args['stress_time']
        wsl_username = subprocess.check_output(['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
        cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --cpu {cpu_workers} --timeout {stress_time}s --metrics-brief"'
        print(f"Executing command: {cmd}")

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            formatted_output = format_output(output.decode('utf-8'))
            return {'output': formatted_output}
        except subprocess.CalledProcessError as e:
            app.logger.error(f"Error executing stress-ng command: {e}")
            return {'error': f"Error: {e.output.decode('utf-8')}"}, 500


@api.expect(common_parser)
@api.marshal_with(output_model)
def post(self):
    args = common_parser.parse_args()
    cpu_workers = args['io_workers']
    stress_time = args['stress_time']
    wsl_username = subprocess.check_output(
        ['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
    cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --cpu {cpu_workers} --timeout {stress_time}s --metrics-brief"'
    print(f"Executing command: {cmd}")

    try:
      output = subprocess.check_output(cmd,
                                       stderr=subprocess.STDOUT,
                                       shell=True)
      formatted_output = format_output(output.decode('utf-8'))
      return {'output': formatted_output}
    except subprocess.CalledProcessError as e:
      return {'error': f"Error: {e.output.decode('utf-8')}"}




@local_stress_test_namespace.route('/stress_memory')
class StressMemoryResource(Resource):

    @api.expect(stress_memory_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = stress_memory_parser.parse_args()
        vm_stressors = args['vm_stressors']
        stress_time = args['stress_time']
        vm_bytes = args['vm_bytes']  
        wsl_username = subprocess.check_output(['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
        cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --vm {vm_stressors} --vm-bytes {vm_bytes} --timeout {stress_time}s --metrics-brief"'
        print(f"Executing command: {cmd}")

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            formatted_output = format_output(output.decode('utf-8'))
            return {'output': formatted_output}
        except subprocess.CalledProcessError as e:
            app.logger.error(f"Error executing stress-ng command: {e}")
            return {'error': f"Error: {e.output.decode('utf-8')}"}, 500


@api.expect(common_parser)
@api.marshal_with(output_model)
def post(self):
    args = common_parser.parse_args()
    memory_workers = args['memory_workers']
    stress_time = args['stress_time']
    wsl_username = subprocess.check_output(
        ['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
    cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --vm {memory_workers} --timeout {stress_time}s --metrics-brief"'
    print(f"Executing command: {cmd}")

    try:
      output = subprocess.check_output(cmd,
                                       stderr=subprocess.STDOUT,
                                       shell=True)
      formatted_output = format_output(output.decode('utf-8'))
      return {'output': formatted_output}
    except subprocess.CalledProcessError as e:
      return {'error': f"Error: {e.output.decode('utf-8')}"}



@local_stress_test_namespace.route('/stress_io')
class StressIOResource(Resource):

    @api.expect(stress_io_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = stress_io_parser.parse_args()
        io_workers = args['io_workers']
        stress_time = args['stress_time']
        wsl_username = subprocess.check_output(['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
        cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --io {io_workers} --timeout {stress_time}s --metrics-brief"'
        print(f"Executing command: {cmd}")

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            formatted_output = format_output(output.decode('utf-8'))
            return {'output': formatted_output}
        except subprocess.CalledProcessError as e:
            app.logger.error(f"Error executing stress-ng command: {e}")
            return {'error': f"Error: {e.output.decode('utf-8')}"}, 500
# Stress CPU parser
remote_stress_parser = reqparse.RequestParser()
remote_stress_parser.add_argument('username', type=str, required=True, help='Username for SSH connection')
remote_stress_parser.add_argument('password', type=str, required=True, help='Password for SSH connection')
remote_stress_parser.add_argument('remote_server_name', type=str, required=True, help='for SSH connection')
remote_stress_parser.add_argument('remote_cpu_workers', type=int, default=1, help='Number of CPU workers')
remote_stress_parser.add_argument('remote_stresstime', type=int, default=60, help='Stress time in seconds')

# Stress Memory parser
remote_stress_memory_parser = reqparse.RequestParser()
remote_stress_memory_parser.add_argument('username', type=str, required=True, help='Username for SSH connection')
remote_stress_memory_parser.add_argument('password', type=str, required=True, help='Password for SSH connection')
remote_stress_memory_parser.add_argument('remote_server_name', type=str, required=True, help='for SSH connection')
remote_stress_memory_parser.add_argument('memory_workers', type=int, default=1, help='Number of workers')
remote_stress_memory_parser.add_argument('remote_stresstime', type=int, default=60, help='Stress time in seconds')
remote_stress_memory_parser.add_argument('remote_vmbytes', type=str, default='512M', help='Percentage of memory using all the vm stressors')

# Stress IO parser
remote_io_stress_parser = reqparse.RequestParser()
remote_io_stress_parser.add_argument('username', type=str, required=True, help='Username for SSH connection')
remote_io_stress_parser.add_argument('password', type=str, required=True, help='Password for SSH connection')
remote_io_stress_parser.add_argument('remote_server_name', type=str, required=True, help='for SSH connection')
remote_io_stress_parser.add_argument('remote_ioworkers', type=int, default=1, help='Number of I/O workers')
remote_io_stress_parser.add_argument('remote_stresstime', type=int, default=60, help='Stress time in seconds')



@stress_ng_test_namespace.route('/re_stress_cpu')
class StressCpuResource(Resource):
    @api.expect(remote_stress_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = remote_stress_parser.parse_args()
        username = args['username']
        password = args['password']
        remote_server = session.get('remote_server', '')
        remote_cpu_workers = args['remote_cpu_workers']
        remote_stresstime = args['remote_stresstime']
        ssh_command = f'sshpass -p "{password}" ssh {username}@{remote_server} '
        cpu_command = f'{ssh_command}"stress-ng --cpu {remote_cpu_workers} --timeout {remote_stresstime}s --metrics-brief"'

        result, error = run_remote_command(cpu_command)
        return render_template('result.html', result=result, error=error)

@stress_ng_test_namespace.route('/re_stress_memory')
class StressMemoryResource(Resource):
    @api.expect(remote_stress_memory_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = remote_stress_memory_parser.parse_args()
        username = args['username']
        password = args['password']
        remote_server = session.get('remote_server', '')
        memory_workers = args['memory_workers']
        remote_stresstime = args['remote_stresstime']
        remote_vmbytes = args['remote_vmbytes']  
        ssh_command = f'sshpass -p "{password}" ssh {username}@{remote_server} '
        memory_command = f'{ssh_command}"stress-ng --vm {memory_workers} --vm-bytes {remote_vmbytes} --timeout {remote_stresstime}s --metrics-brief"'

        result, error = run_remote_command(memory_command)
        return render_template('result.html', result=result, error=error)

@stress_ng_test_namespace.route('/re_stress_io')
class StressIOResource(Resource):
    @api.expect(remote_io_stress_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = remote_io_stress_parser.parse_args()
        username = args['username']
        password = args['password']
        remote_server = session.get('remote_server', '')
        remote_ioworkers = args['remote_ioworkers']
        remote_stresstime = args['remote_stresstime']
        ssh_command = f'sshpass -p "{password}" ssh {username}@{remote_server} '
        io_command = f'{ssh_command}"stress-ng --io {remote_ioworkers} --timeout {remote_stresstime}s --metrics-brief"'

        result, error = run_remote_command(io_command)
        return render_template('result.html', result=result, error=error)

def run_remote_command(command):
    remote_server = session.get('remote_server')
    if not remote_server:
        return None, "Error: Remote server not set."

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        formatted_output = format_output(output.decode('utf-8'))
        return formatted_output, None
    except subprocess.CalledProcessError as e:
        return None, f"Error: {e.output.decode('utf-8')}"


@api.expect(common_parser)
@api.marshal_with(output_model)
def post(self):
    args = common_parser.parse_args()
    io_workers = args['io_workers']
    stress_time = args['stress_time']
    wsl_username = subprocess.check_output(
        ['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
    cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --io {io_workers} --timeout {stress_time}s --metrics-brief"'
    print(f"Executing command: {cmd}")

    try:
      output = subprocess.check_output(cmd,
                                       stderr=subprocess.STDOUT,
                                       shell=True)
      formatted_output = format_output(output.decode('utf-8'))
      return {'output': formatted_output}
    except subprocess.CalledProcessError as e:
      return {'error': f"Error: {e.output.decode('utf-8')}"}



@app.route('/swagger')
def swagger_ui():
  return render_template('swaggerui.html')




@app.route('/remote')
def remote_ui():
  # Add the logic for your remote route
  return render_template('remote.html')


# Output route
@app.route('/output')
def output():
  output_data = request.args.get('output', '')
  formatted_output = format_output(output_data)
  return render_template('output.html', output=formatted_output)


#load management page websitename.com/load_management
@app.route("/load_management")
def load_management_page():
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


@app.route('/set_remote_server', methods=['POST'])
def set_remote_server():
    remote_server = request.form['remote_server']
    session['remote_server'] = remote_server
    return redirect(url_for('home_page'))


# Run the app


if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
