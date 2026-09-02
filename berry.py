from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dotenv import load_dotenv
import json, time, os, base64, hashlib, difflib, sys
from urllib.parse import urlparse, parse_qs
from detection_engine.engine.detection_engine import detect_ip
sys.stdout.reconfigure(line_buffering=True) # allows thing

cfg = json.load(open(f"berry.json", 'r')) # load config file
hostName = cfg["hostName"]
domainName = cfg.get("domainName", hostName)
serverPort = cfg["serverPort"]
certFile = cfg.get("cert", "raspberry.crt")
keyFile = cfg.get("key", "raspberry.key")
https_enabled = cfg.get("enableHTTPS", False)
ver = "v1.3.1"

if https_enabled:
    # https support
    import ssl, ipaddress
    from datetime import datetime, timezone, timedelta
    from pathlib import Path
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

def generate_certificate(cert_file="raspberry.crt", key_file="raspberry.key"):
    if Path(cert_file).exists() and Path(key_file).exists(): # ignore files if they already exist
        return

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "NeoCat Police"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(domainName),
                x509.IPAddress(ipaddress.ip_address(hostName)),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_file, "wb") as f:
        f.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

# Basic Logic to pull version from bot.py
def openfile(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    return lines

try:
    ncpolver = "v0.0.0 (Version Error)"
    filee = openfile("bot.py")
    for line in filee:
        line = line.strip()
        if line.startswith("ver = "):
            ncpolver = line.replace("ver = ", "").replace("\"", "").replace("'", "")
            break
except Exception:
    pass

load_dotenv()  
salt = os.getenv("salt")

os.makedirs("registry", exist_ok=True)
print("Starting Raspberry...")

def load_db(guildId):
    try:
        with open(f"registry/{guildId}.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to db.json
def save_db(guildId, data):
    with open(f"registry/{guildId}.json", 'w') as f:
        json.dump(data, f, indent=4)

# Credit to https://github.com/milenakos/cat-stand-verification for HTML Verification Page
head = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta content="width=device-width, initial-scale=1.0, maximum-scale=3.0" name="viewport" />
    <title>NeoCat Police Verification</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 80px;
            font-size: 22px;
        }
        h1 {
            font-size: 42px;
            margin-bottom: 40px;
        }
        .option {
            display: block;
            width: 320px;
            margin: 20px auto;
            padding: 22px 30px;
            font-size: 24px;
            border: 3px solid #ccc;
            border-radius: 16px;
            cursor: pointer;
            transition: background-color 0.15s, border-color 0.15s, color 0.15s;
            user-select: none;
        }
        .option:hover {
            border-color: #2f6fed;
        }
        .option input {
            display: none;
        }
        .option.selected {
            background-color: #2f6fed;
            border-color: #2f6fed;
            color: #fff;
        }
        button {
            padding: 16px 40px;
            font-size: 24px;
            margin-top: 30px;
            border-radius: 12px;
            border: none;
            background-color: #2f6fed;
            color: #fff;
            cursor: pointer;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        small {
          color: lightgray;
        }
    </style>
</head>
"""
htmlpage = r"""
!head!

<body id="main">
    <h1>How old are you?</h1>

    <form id="age-form" onsubmit="return false;">
        <label class="option" for="under-13">
            <input type="radio" id="under-13" name="age" value="u">
            Under 13
        </label>

        <label class="option" for="over-13">
            <input type="radio" id="over-13" name="age" value="o">
            13 and over
        </label>

        <button type="submit">Submit</button>
    </form>

    <br>
    <small>
        By pressing submit, your IP address and browser fingerprint will be securely logged for verification purposes.
    </small>

    <script>

        function toBase64Url(base64) {
            return btoa(base64).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
        }

        function getCanvasFingerprint() {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = "14px 'Arial'";
            ctx.textBaseline = "alphabetic";
            ctx.fillStyle = "#f60";
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = "#069";
            ctx.fillText("NeoCat Police", 2, 15);
            ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
            ctx.fillText("NeoCat Police", 4, 17);
            return canvas.toDataURL();
        }

        const fingerprint = {
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            timezoneOffset: new Date().getTimezoneOffset(),
            userAgent: navigator.userAgent,
            canvas: getCanvasFingerprint()
        };
        const data = JSON.stringify(fingerprint)

        document.querySelectorAll('.option input').forEach(function(input) {
            input.addEventListener('change', function() {
                document.querySelectorAll('.option').forEach(function(label) {
                    label.classList.remove('selected');
                });
                input.closest('.option').classList.add('selected');
            });
        });

        document.getElementById("age-form").addEventListener("submit", () => {
            const choice = document.querySelector('input[name="age"]:checked');

            if (!choice) return;

            if (choice.value === "u") {
                window.location.href = "/submi1/!path!" + "?s=" + toBase64Url(data);
            } else {
                window.location.href = "/submi2/!path!" + "?s=" + toBase64Url(data);
            }
        });

    </script>
</body>

</html>
""".replace("!head!", head)

verified = f"""
{head}

<body id="main">
    <h1>Thanks!</h1>You can now close this tab.
</body>

</html>
"""

invalid = f"{head}<body><p>Error 400: Invalid Session</p></body></html>"

info = f"""{head}<body>NeoCat Police Verification Integrated Web Server \"Raspberry\" {ver}<br><small>Running as part of NeoCat Police {ncpolver}</small><p>Raspberry is provided under the AGPL-3.0 Licence<br>Copyright (c) 2025 Lia Milenakos<br>Copyright (c) 2026 Mari Kepler<br>Credit to https://pythonbasics.org/webserver/ for Providing Minimal Python Server Example</p><br></body></html>"""

def combine_fingerprints(header_fp, query_params):
    fingerprint = json.loads(base64.urlsafe_b64decode(query_params['s'][0]).decode('utf-8'))
    return header_fp | fingerprint

def is_tampered(fingerprint):
    # Define required keys:
    required_keys = ['screenWidth', 'screenHeight', 'timezoneOffset', 'userAgent', 'canvas', 'Accept-Encoding', 'Accept-Language', 'Accept', 'Connection']
    
    # Check for missing or empty keys
    for key in required_keys:
        if key not in fingerprint or not fingerprint[key]:
            print(f"{key} missing")
            return True
    
    if len(fingerprint['userAgent']) < 24:
        return True
    if len(fingerprint['canvas']) < 100:
        return True
    
    return False

def fingerprint_similarity(fp1, fp2):
    # Compare two fingerprint dicts and calculate similarity percentage
    keys = set(fp1.keys()) | set(fp2.keys())
    differences = 0
    total_keys = len(keys)
    total_similarity = 0

    for key in keys:
        v1 = str(fp1.get(key, ""))
        v2 = str(fp2.get(key, ""))
        if v1 != v2:
            differences += 1
        # Compute string similarity for values (0 to 1)
        seq = difflib.SequenceMatcher(None, v1, v2)
        total_similarity += seq.ratio()

    avg_similarity = total_similarity / total_keys if total_keys else 1.0

    return differences, avg_similarity

def is_fingerprint_repeat(new_fp, old_fp):
    differences, similarity = fingerprint_similarity(new_fp, old_fp)
    if differences <= 3 or similarity >= 0.9:
        return True
    return False

def genhtmlpage(path, ip, fingerprint, query_params):
    if path.startswith("/submi"):
        if not path[6] in ["1", "2"]:
            return(invalid)
        underage = False
        if path[6] == "1":
            underage = True
        path = path[8:].split("?")[0]
        if not len(path.split("/")) == 2:
            return(invalid)
        guild = path.split("/")[0]
        user = path.split("/")[1]
        try:
            pathd = base64.urlsafe_b64decode(user + '=' * (4 - len(user) % 4))
            pathd = str(int.from_bytes(pathd, 'big'))
            guild_id = base64.urlsafe_b64decode(guild + '=' * (4 - len(guild) % 4))
            guild_id = str(int.from_bytes(guild_id, 'big'))
        except Exception as e:
            print(e)
            return(invalid)
        db = load_db(guild_id)
        db.setdefault(pathd, {})
        full_fingerprint = combine_fingerprints(fingerprint, query_params)

        alreadyregisteredip = False
        ariuser = None
        vpn_detect = False
        fingerprintrepeat = False
        fpruser = None
        tampering = False

        if not full_fingerprint or len(full_fingerprint) < 5 or is_tampered(full_fingerprint):
            tampering = True

        for user in db:
            if user in ("verified", "pending_fails", "underage"):
                continue
            db[user].setdefault("fp", [])
            for fig in db[user]["fp"]:
                if not tampering and is_fingerprint_repeat(full_fingerprint, fig):
                    if not user == pathd:
                        fingerprintrepeat = True
                    fpruser = user

        ipsalt = f'{ip}{salt}'.encode('utf-8')
        result = detect_ip(ip)
        if result['is_suspicious']:
            vpn_detect = True
        hashsalt = hashlib.sha256(ipsalt, usedforsecurity=True).hexdigest()
        for user in db:
            if user in ("verified", "pending_fails", "underage"):
                continue
            db[user].setdefault("ip", [])
            if hashsalt in db[user]["ip"]:
                if not user == pathd:
                    alreadyregisteredip = True
                    ariuser = user

        fail = f"<@{pathd}> has failed verification: "
        failtype = []
        if alreadyregisteredip:
            failtype.append(f"repeated IP of <@{ariuser}>")
        if vpn_detect:
            failtype.append("IP suspected to be a part of a VPN or Proxy")
        if fingerprintrepeat:
            failtype.append(f"repeated fingerprint of <@{fpruser}>")
        if tampering:
            failtype.append("tampering detected")
        fail += ", ".join(failtype)
        if alreadyregisteredip+vpn_detect+fingerprintrepeat+tampering > 0:
            print(fail)

        if not tampering and not fingerprintrepeat:
            db[pathd].setdefault("fp", [])
            if not full_fingerprint in db[pathd]["fp"]:
                db[pathd]["fp"].append(full_fingerprint)

        if not alreadyregisteredip and not vpn_detect:
            db[pathd].setdefault("ip", [])
            if not hashsalt in db[pathd]["ip"]:
                db[pathd]["ip"].append(hashsalt)

        if alreadyregisteredip+vpn_detect+fingerprintrepeat+tampering == 0:
            db.setdefault("verified", [])
            db.setdefault("underage", [])
            if not pathd in db["verified"]:
                db["verified"].append(pathd)
            if underage:
                if not pathd in db["underage"]:
                    db["underage"].append(pathd)
        else:
            db.setdefault("pending_fails", [])
            if not pathd in db["pending_fails"]:
                db["pending_fails"].append(fail)

        save_db(guild_id, db)

        return verified.replace("!path!", path)
    elif path.startswith("/info"):
        return(info)
    else:
        path = path[1:]
        return htmlpage.replace("!path!", path)

# Credit to https://pythonbasics.org for the HTML Server Code
class MyServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # disable logging

    def get_browser_fingerprint(self):
        # Collect some headers that can be used for fingerprinting
        headers_to_use = [
            'User-Agent',
            'Accept-Language',
            'Accept-Encoding',
            'Accept',
            'Connection',
            'Cookie'
        ]
        fingerprint_data = {}
        for header in headers_to_use:
            value = self.headers.get(header, "")
            fingerprint_data[header] = value
        return fingerprint_data

    def do_GET(self):
        try:
            fingerprint = self.get_browser_fingerprint()
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(genhtmlpage(self.path, self.client_address[0], fingerprint, query_params), "utf-8"))
        except Exception as e:
            print("Handler crashed:", repr(e))
            try:
                self.send_error(500)
            except:
                print("failed to send error")
                pass

if __name__ == "__main__":
    if https_enabled:
        generate_certificate(certFile, keyFile)
        webServer = ThreadingHTTPServer((hostName, serverPort), MyServer)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certFile, keyFile)
        webServer.socket = context.wrap_socket( webServer.socket, server_side=True)
        print("Server started https://%s:%s" % (hostName, serverPort)+"/info")
    else:
        webServer = ThreadingHTTPServer((hostName, serverPort), MyServer)
        print("Server started http://%s:%s" % (hostName, serverPort)+"/info")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
