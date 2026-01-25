from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dotenv import load_dotenv
import json, time, os, base64, hashlib, difflib
from urllib.parse import urlparse, parse_qs
from detection_engine.engine.detection_engine import detect_ip

cfg = json.load(open(f"berry.json", 'r')) # load config file
hostName = cfg["hostName"]
serverPort = cfg["serverPort"]

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
            margin-top: 50px;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin: 10px;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        a {
          text-decoration: none;
        }
        small {
          color: lightgray;
        }
    </style>
</head>
"""
htmlpage = """
!head!

<body id="main">
    <h1>How old are you?</h1>
    <a href="/submi1/!path!">
        <button id="under-13">Under 13</button>
    </a>
    <a href="/submi2/!path!">
        <button id="over-13">13 and over</button>
    </a>
    <br><br><small>By pressing either button, your IP address and browser fingerprint will be securely logged for verification purposes.</small>
    <script>

    sendFingerprint();
    </script>
</body>

</html>
""".replace("!head!", head)

pleasewait = """
!head!

<body id="main">
    Please wait...

    <script>
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

    function sendFingerprint() {
        const fingerprint = {
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            timezoneOffset: new Date().getTimezoneOffset(),
            userAgent: navigator.userAgent,
            canvas: getCanvasFingerprint()
        };
    
        const params = new URLSearchParams(fingerprint).toString();
        
        // If fingerprint params already exist in URL, don't redirect infinitely
        if (!window.location.search.includes('screenWidth')) {
            window.location.href = window.location.pathname + "?" + params;
        }
    }

    sendFingerprint();
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
invalid = "<!DOCTYPE html><html><head><title>Verification Error</title></head><body><p>Error 400: Invalid Session</p></body></html>"

def combine_fingerprints(header_fp, query_params):
    combined = {}
    # header_fp might be a string or dict? 
    # Let's assume header_fp is a dict for flexibility; else convert it to dict
    if isinstance(header_fp, dict):
        combined.update(header_fp)
    else:
        print(header_fp)
        combined['header'] = header_fp
    
    # query_params from parse_qs has list values, flatten them:
    for k, v in query_params.items():
        combined[k] = v[0] if isinstance(v, list) and len(v) > 0 else v
    return combined

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
        except Exception:
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
    else:
        if query_params:
            path = path[1:]
            return htmlpage.replace("!path!", path)
        else:
            return pleasewait

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
    webServer = ThreadingHTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
