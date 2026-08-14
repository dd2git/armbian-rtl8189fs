#!/usr/bin/env python3
"""Fallback hotspot and small Wi-Fi provisioning portal for Armbian."""

import html
import json
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOTSPOT_NAME = "armbian-setup-hotspot"
HOTSPOT_SSID = "Armbian-Setup"
HOTSPOT_PASSWORD = "armbian-setup"
HOTSPOT_IFACE = "wlan0"
CLIENT_IFACE = "wlan1"
HOTSPOT_ADDRESS = "10.42.0.1/24"
PORT = 80

lock = threading.Lock()
status = {"busy": False, "message": "Bereit", "ok": True}


def run(args, timeout=35, check=False):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or "Befehl fehlgeschlagen")
    return result


def nm(*args, timeout=35, check=False):
    return run(["nmcli", "--colors", "no", *args], timeout=timeout, check=check)


def connection_exists(name):
    return nm("-g", "connection.id", "connection", "show", name).returncode == 0


def ensure_hotspot_profile():
    if not connection_exists(HOTSPOT_NAME):
        nm("connection", "add", "type", "wifi", "ifname", HOTSPOT_IFACE,
           "con-name", HOTSPOT_NAME, "ssid", HOTSPOT_SSID, check=True)
    nm("connection", "modify", HOTSPOT_NAME,
       "connection.autoconnect", "no",
       "802-11-wireless.mode", "ap",
       "802-11-wireless.band", "bg",
       "802-11-wireless-security.key-mgmt", "wpa-psk",
       "802-11-wireless-security.psk", HOTSPOT_PASSWORD,
       "ipv4.method", "shared",
       "ipv4.addresses", HOTSPOT_ADDRESS,
       "ipv6.method", "disabled", check=True)


def device_connection(iface):
    result = nm("-g", "GENERAL.CONNECTION", "device", "show", iface)
    return result.stdout.strip() if result.returncode == 0 else ""


def client_connected():
    for iface in (CLIENT_IFACE, HOTSPOT_IFACE):
        conn = device_connection(iface)
        if conn and conn not in ("--", HOTSPOT_NAME):
            state = nm("-g", "GENERAL.STATE", "device", "show", iface).stdout.strip()
            if state.startswith("100"):
                return True
    return False


def hotspot_active():
    return device_connection(HOTSPOT_IFACE) == HOTSPOT_NAME


def ensure_hotspot_active():
    if hotspot_active():
        return True
    ensure_hotspot_profile()
    result = nm("connection", "up", HOTSPOT_NAME, "ifname", HOTSPOT_IFACE, timeout=45)
    if result.returncode:
        set_status("Hotspot konnte nicht gestartet werden: " + (result.stderr or result.stdout).strip(), False)
        return False
    set_status("Hotspot aktiv – WLAN auswählen", True)
    return True


def set_status(message, ok=True, busy=None):
    with lock:
        status["message"] = message
        status["ok"] = ok
        if busy is not None:
            status["busy"] = busy


def split_nmcli(line):
    fields, current, escaped = [], [], False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    fields.append("".join(current))
    return fields


def scan_networks():
    result = nm("-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list",
                "ifname", CLIENT_IFACE, "--rescan", "yes", timeout=30)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or "Scan fehlgeschlagen")
    best = {}
    for line in result.stdout.splitlines():
        fields = split_nmcli(line)
        if len(fields) < 3 or not fields[0]:
            continue
        ssid, signal, security = fields[0], fields[1], ":".join(fields[2:]) or "Offen"
        try:
            strength = int(signal)
        except ValueError:
            strength = 0
        if ssid not in best or strength > best[ssid]["signal"]:
            best[ssid] = {"ssid": ssid, "signal": strength, "security": security}
    return sorted(best.values(), key=lambda item: item["signal"], reverse=True)


def safe_connection_name(ssid):
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", ssid).strip("-")[:40] or "wlan"
    return "armbian-wifi-" + clean


def connect_worker(ssid, password):
    set_status("Verbindung mit „%s“ wird getestet …" % ssid, True, True)
    name = safe_connection_name(ssid)
    try:
        if connection_exists(name):
            nm("connection", "delete", name)
        args = ["device", "wifi", "connect", ssid, "ifname", CLIENT_IFACE, "name", name]
        if password:
            args += ["password", password]
        result = nm(*args, timeout=60)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout).strip() or "Anmeldung fehlgeschlagen")
        deadline = time.time() + 25
        while time.time() < deadline and not client_connected():
            time.sleep(1)
        if not client_connected():
            raise RuntimeError("WLAN wurde nicht verbunden")
        nm("connection", "modify", name, "connection.autoconnect", "yes",
           "connection.autoconnect-priority", "20")
        nm("connection", "down", HOTSPOT_NAME)
        set_status("Verbunden mit „%s“. Der Hotspot wurde deaktiviert." % ssid, True)
    except Exception as exc:
        nm("connection", "delete", name)
        ensure_hotspot_active()
        set_status("Verbindung fehlgeschlagen: %s – Hotspot bleibt aktiv." % exc, False)
    finally:
        with lock:
            status["busy"] = False


def page():
    with lock:
        current = dict(status)
    color = "#16794b" if current["ok"] else "#b42318"
    return f"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content='width=device-width,initial-scale=1'>
<title>Armbian WLAN-Einrichtung</title><style>
body{{font:16px system-ui,sans-serif;background:#eef2f5;margin:0;color:#17202a}}
main{{max-width:620px;margin:32px auto;padding:24px;background:white;border-radius:14px;box-shadow:0 4px 24px #0002}}
h1{{margin-top:0}} button{{background:#1769aa;color:white;border:0;border-radius:8px;padding:11px 16px;font-weight:600;cursor:pointer}}
input,select{{width:100%;box-sizing:border-box;padding:11px;margin:6px 0 16px;border:1px solid #abb5bf;border-radius:8px}}
#message{{padding:12px;border-left:5px solid {color};background:#f5f7f8;margin:16px 0}} small{{color:#52606d}}
</style></head><body><main><h1>WLAN einrichten</h1>
<div id=message>{html.escape(current['message'])}</div>
<button type=button onclick=scan()>Netzwerke suchen</button><p id=scanstatus></p>
<form method=post action=/connect><label>WLAN-Netz</label><select name=ssid id=ssid required><option value=''>Zuerst suchen …</option></select>
<label>WLAN-Passwort</label><input name=password type=password maxlength=128 autocomplete=current-password>
<button {'disabled' if current['busy'] else ''}>Verbinden</button></form>
<p><small>Nach erfolgreicher Anmeldung endet der Hotspot automatisch. Bei einem Fehler bleibt er erreichbar.</small></p>
<script>async function scan(){{let s=document.getElementById('scanstatus'),x=document.getElementById('ssid');s.textContent='Suche …';
try{{let r=await fetch('/scan'),a=await r.json();if(!r.ok)throw Error(a.error);x.innerHTML='';for(let n of a){{let o=document.createElement('option');o.value=n.ssid;o.textContent=`${{n.ssid}} (${{n.signal}} %, ${{n.security}})`;x.appendChild(o)}}s.textContent=a.length?`${{a.length}} Netzwerke gefunden`:'Keine Netzwerke gefunden';}}catch(e){{s.textContent='Fehler: '+e.message}}}}</script>
</main></body></html>""".encode()


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, code, body, content_type="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/scan":
            try:
                body = json.dumps(scan_networks(), ensure_ascii=False).encode()
                self.send_bytes(200, body, "application/json; charset=utf-8")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode()
                self.send_bytes(500, body, "application/json; charset=utf-8")
        elif self.path in ("/", "/index.html"):
            self.send_bytes(200, page())
        else:
            self.send_bytes(302, b"", "text/plain")

    def do_POST(self):
        if self.path != "/connect":
            self.send_bytes(404, b"Nicht gefunden", "text/plain; charset=utf-8")
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 4096)
            form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
            ssid = form.get("ssid", [""])[0].strip()
            password = form.get("password", [""])[0]
            if not ssid or len(ssid.encode()) > 32 or len(password) > 128:
                raise ValueError("Ungültige Eingabe")
            with lock:
                if status["busy"]:
                    raise ValueError("Eine Verbindung wird bereits getestet")
            threading.Thread(target=connect_worker, args=(ssid, password), daemon=True).start()
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        except Exception as exc:
            self.send_bytes(400, ("Fehler: " + str(exc)).encode(), "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):
        print("web:", fmt % args, flush=True)


def monitor():
    while True:
        try:
            with lock:
                busy = status["busy"]
            if not busy:
                if client_connected():
                    if hotspot_active():
                        nm("connection", "down", HOTSPOT_NAME)
                else:
                    ensure_hotspot_active()
        except Exception as exc:
            set_status("Überwachungsfehler: " + str(exc), False)
        time.sleep(10)


if __name__ == "__main__":
    ensure_hotspot_profile()
    threading.Thread(target=monitor, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
