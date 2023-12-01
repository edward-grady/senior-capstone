from flask import Flask, render_template, request, redirect, url_for, session
from flask_restx import Api, Resource, reqparse, fields
import subprocess

app = Flask(__name__)
api = Api(app, doc='/swagger', title='Stress-ng Test API',
          description='A simple API for running stress-ng tests.')
local_stress_test_namespace = api.namespace('local_stress_test', description='Local Stress Tests')
stress_ng_test_namespace = api.namespace('remote_server_stress-test', description='Remote Stress Tests')
app.secret_key = "SecretKey"


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


#run app


@app.route('/set_remote_server', methods=['POST'])
def set_remote_server():
    remote_server = request.form['remote_server']
    session['remote_server'] = remote_server
    return redirect(url_for('home_page'))


# Run the app


if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
