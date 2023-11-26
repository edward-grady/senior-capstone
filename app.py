from flask import Flask, render_template, request, redirect, url_for, session
from flask_restx import Api, Resource, reqparse, fields
import subprocess

app = Flask(__name__)
api = Api(app, doc='/swagger')

app.secret_key = "SecretKey"

# Login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('home_page'))
        else:
            return render_template('login.html', error='Invalid username or password')
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

common_parser = reqparse.RequestParser()
common_parser.add_argument('io_workers', type=int, default=1, help='Number of I/O workers')
common_parser.add_argument('stress_time', type=int, default=60, help='Stress time in seconds')

def format_output(output):
    return '<br>'.join(output.split('\n'))

@api.route('/stress_cpu')
class StressCpuResource(Resource):
    @api.expect(common_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = common_parser.parse_args()
        cpu_workers = args['io_workers']
        stress_time = args['stress_time']
        wsl_username = subprocess.check_output(['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
        cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --cpu {cpu_workers} --timeout {stress_time}s --metrics-brief"'
        print(f"Executing command: {cmd}")

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            formatted_output = format_output(output.decode('utf-8'))
            return {'output': formatted_output}
        except subprocess.CalledProcessError as e:
            return {'error': f"Error: {e.output.decode('utf-8')}"}

@api.route('/stress_memory')
class StressMemoryResource(Resource):
    @api.expect(common_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = common_parser.parse_args()
        memory_workers = args['memory_workers']
        stress_time = args['stress_time']
        wsl_username = subprocess.check_output(['wsl', '/bin/bash', '-c', 'whoami']).strip().decode('utf-8')
        cmd = f'wsl --user {wsl_username} /bin/bash -c "/usr/bin/stress-ng --vm {memory_workers} --timeout {stress_time}s --metrics-brief"'
        print(f"Executing command: {cmd}")

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            formatted_output = format_output(output.decode('utf-8'))
            return {'output': formatted_output}
        except subprocess.CalledProcessError as e:
            return {'error': f"Error: {e.output.decode('utf-8')}"}

@api.route('/stress_io')
class StressIOResource(Resource):
    @api.expect(common_parser)
    @api.marshal_with(output_model)
    def post(self):
        args = common_parser.parse_args()
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

# Run the app
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
