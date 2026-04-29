from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import threading
import subprocess
import re
import socket
from datetime import datetime
import ipaddress
import json
import os
import ctypes
from types import SimpleNamespace

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

devices_lock = threading.Lock()
devices = {}
dns_domain_ips_cache = {}
reverse_dns_cache = {}
hotspot_prefixes = [ipaddress.ip_network("192.168.137.0/24")]
firewall_log_path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), r"System32\LogFiles\Firewall\pfirewall.log")
firewall_log_cursor = 0

MAX_TRAFFIC_PER_DEVICE = 40
FIREWALL_RULE_NAME = "SmartWall Domain Block"
STRICT_BLOCK_RULE_NAME = "SmartWall Strict Block All"
STRICT_ALLOW_RULE_NAME = "SmartWall Strict Allowlist"
QUIC_BLOCK_RULE_NAME = "SmartWall Block QUIC 443"

rules = {
    "social_media": False,
    "streaming": False,
    "gaming": True
}
blocked_services = []
strict_mode = False
enforcement_state = {
    "enabled_domains": [],
    "resolved_ips": [],
    "strict_mode": False,
    "updated_at": None,
    "status": "idle",
    "message": "No firewall enforcement applied yet."
}
runtime_state = {
    "monitor_started": False,
    "is_admin": False,
    "firewall_log_readable": False,
    "telemetry_mode": "firewall_log",
    "last_events_count": 0
}

DOMAINS = {
    "social_media": ["instagram.com", "facebook.com", "twitter.com", "x.com", "snapchat.com", "tiktok.com"],
    "streaming": ["youtube.com", "netflix.com", "hulu.com", "primevideo.com", "disneyplus.com"],
    "gaming": ["freefire.com", "poki.com", "bgmi.com", "pubg.com", "roblox.com","chess.com"]
}

APP_DOMAIN_EXPANSIONS = {
    "streaming": ["googlevideo.com", "ytimg.com", "youtubei.googleapis.com", "ggpht.com", "youtu.be"],
    "gaming": ["garena.com", "ff.garena.com", "rbxcdn.com", "pubgmobile.com", "proximabeta.com"],
    "social_media": ["cdninstagram.com", "fbcdn.net", "whatsapp.net"],
}

def is_public_ip(value):
    try:
        parsed_ip = ipaddress.ip_address(value)
        return not (
            parsed_ip.is_private
            or parsed_ip.is_loopback
            or parsed_ip.is_multicast
            or parsed_ip.is_reserved
            or parsed_ip.is_link_local
        )
    except ValueError:
        return False


def get_domains_to_block():
    domains = set(blocked_services)
    for category, active in rules.items():
        if active:
            domains.update(DOMAINS.get(category, []))
            domains.update(APP_DOMAIN_EXPANSIONS.get(category, []))
    return sorted(domains)


def normalize_domain(value):
    return value.strip().lower().removeprefix("www.")


def domain_matches(blocked_domain, candidate_domain):
    blocked = normalize_domain(blocked_domain)
    candidate = normalize_domain(candidate_domain)
    return candidate == blocked or candidate.endswith(f".{blocked}")


def resolve_domain_ips(domains):
    resolved_ips = set()
    common_prefixes = ["", "www", "m", "api", "graph", "cdn", "mobile"]
    for domain in domains:
        normalized = normalize_domain(domain)
        cached = dns_domain_ips_cache.get(normalized)
        if cached:
            resolved_ips.update(cached)
            continue

        found_ips = set()
        for prefix in common_prefixes:
            host = f"{prefix}.{normalized}" if prefix else normalized
            try:
                results = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
                for result in results:
                    found_ips.add(result[4][0])
            except socket.gaierror:
                continue
        dns_domain_ips_cache[normalized] = found_ips
        resolved_ips.update(found_ips)
    return sorted(resolved_ips)


def run_powershell(command):
    try:
        return subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            check=False,
            timeout=12
        )
    except subprocess.TimeoutExpired:
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="PowerShell command timed out after 12 seconds."
        )


def is_admin_user():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def upsert_firewall_rule(display_name, action, remote_addresses):
    exists_check = run_powershell(
        f"Get-NetFirewallRule -DisplayName '{display_name}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"
    )
    rule_exists = bool(exists_check.stdout.strip())
    remote_csv = ",".join(remote_addresses)

    if rule_exists:
        update_result = run_powershell(
            f"Get-NetFirewallRule -DisplayName '{display_name}' | "
            f"Set-NetFirewallRule -Action {action} -Service SharedAccess -Profile Any -Direction Outbound -Enabled True; "
            f"Get-NetFirewallRule -DisplayName '{display_name}' | "
            f"Get-NetFirewallAddressFilter | "
            f"Set-NetFirewallAddressFilter -RemoteAddress '{remote_csv}'"
        )
        return update_result.returncode == 0

    create_result = run_powershell(
        f"New-NetFirewallRule -DisplayName '{display_name}' "
        f"-Direction Outbound -Action {action} -RemoteAddress '{remote_csv}' "
        f"-Profile Any -Enabled True -Service SharedAccess"
    )
    return create_result.returncode == 0


def remove_firewall_rule(display_name):
    delete_result = run_powershell(
        f"Remove-NetFirewallRule -DisplayName '{display_name}' -ErrorAction SilentlyContinue"
    )
    return delete_result.returncode == 0


def upsert_quic_block_rule(enabled):
    if not enabled:
        remove_firewall_rule(QUIC_BLOCK_RULE_NAME)
        return True

    exists_check = run_powershell(
        f"Get-NetFirewallRule -DisplayName '{QUIC_BLOCK_RULE_NAME}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"
    )
    rule_exists = bool(exists_check.stdout.strip())

    if rule_exists:
        update_result = run_powershell(
            f"Get-NetFirewallRule -DisplayName '{QUIC_BLOCK_RULE_NAME}' | "
            f"Set-NetFirewallRule -Action Block -Service SharedAccess -Profile Any -Direction Outbound -Enabled True"
        )
        return update_result.returncode == 0

    create_result = run_powershell(
        f"New-NetFirewallRule -DisplayName '{QUIC_BLOCK_RULE_NAME}' "
        f"-Direction Outbound -Action Block -Protocol UDP -RemotePort 443 "
        f"-Profile Any -Enabled True -Service SharedAccess"
    )
    return create_result.returncode == 0


def apply_firewall_rules():
    global strict_mode
    domains = get_domains_to_block()
    ips = resolve_domain_ips(domains)

    now_value = datetime.now().strftime("%I:%M %p")
    enforcement_state["enabled_domains"] = domains
    enforcement_state["resolved_ips"] = ips
    enforcement_state["strict_mode"] = strict_mode
    enforcement_state["updated_at"] = now_value

    if strict_mode:
        strict_ok = upsert_firewall_rule(STRICT_BLOCK_RULE_NAME, "Block", ["Any"])
        if not strict_ok:
            enforcement_state["status"] = "warning"
            enforcement_state["message"] = "Strict mode rule failed. Start backend as administrator."
            return

        # In strict mode, targeted domain block is not needed.
        remove_firewall_rule(FIREWALL_RULE_NAME)
        upsert_quic_block_rule(True)
        enforcement_state["status"] = "active"
        enforcement_state["message"] = "Strict mode active: all hotspot-forwarded internet traffic is blocked."
        return

    remove_firewall_rule(STRICT_BLOCK_RULE_NAME)
    quic_ok = upsert_quic_block_rule(bool(rules.get("streaming") or rules.get("gaming")))
    if not quic_ok:
        enforcement_state["status"] = "warning"
        enforcement_state["message"] = "QUIC app-block rule failed. Start backend as administrator."
        return

    if not ips:
        remove_firewall_rule(FIREWALL_RULE_NAME)
        enforcement_state["status"] = "idle"
        enforcement_state["message"] = "No active domains to block."
        return

    updated = upsert_firewall_rule(FIREWALL_RULE_NAME, "Block", ips)
    if updated:
        enforcement_state["status"] = "active"
        enforcement_state["message"] = f"Firewall created for {len(domains)} blocked domains."
    else:
        enforcement_state["status"] = "warning"
        enforcement_state["message"] = "Firewall rule creation failed. Start backend with administrator privileges."


def configure_firewall_logging():
    global firewall_log_cursor
    # Enables both allowed and dropped packets logging for real-time hotspot telemetry.
    commands = [
        "netsh advfirewall set allprofiles logging allowedconnections enable",
        "netsh advfirewall set allprofiles logging droppedconnections enable",
        f'netsh advfirewall set allprofiles logging filename "{firewall_log_path}"',
        "netsh advfirewall set allprofiles logging maxfilesize 16384",
    ]
    for command in commands:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return False

    if os.path.exists(firewall_log_path):
        firewall_log_cursor = os.path.getsize(firewall_log_path)
        runtime_state["firewall_log_readable"] = os.access(firewall_log_path, os.R_OK)
    return True


def infer_domain_from_remote_ip(remote_ip):
    if remote_ip in reverse_dns_cache:
        return reverse_dns_cache[remote_ip]
    domain = remote_ip
    try:
        host = socket.gethostbyaddr(remote_ip)[0].lower()
        if host and host != remote_ip:
            domain = normalize_domain(host)
    except socket.herror:
        pass
    reverse_dns_cache[remote_ip] = domain
    return domain


def is_hotspot_interface_ip(ip_value):
    try:
        parsed_ip = ipaddress.ip_address(ip_value)
        return any(parsed_ip in prefix for prefix in hotspot_prefixes)
    except ValueError:
        return False


def detect_hotspot_prefixes():
    global hotspot_prefixes
    try:
        result = run_powershell(
            "Get-NetNat -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty InternalIPInterfaceAddressPrefix | ConvertTo-Json -Compress"
        )
        if result.returncode != 0 or not result.stdout.strip():
            return
        prefixes_raw = json.loads(result.stdout.strip())
        if isinstance(prefixes_raw, str):
            prefixes_raw = [prefixes_raw]
        detected = []
        for prefix in prefixes_raw:
            try:
                detected.append(ipaddress.ip_network(prefix, strict=False))
            except ValueError:
                continue
        if detected:
            hotspot_prefixes = detected
    except Exception:
        pass


def parse_firewall_log_events():
    global firewall_log_cursor
    events = []
    if not os.path.exists(firewall_log_path):
        return events

    try:
        with open(firewall_log_path, "r", encoding="utf-8", errors="ignore") as log_file:
            log_file.seek(firewall_log_cursor)
            new_data = log_file.read()
            firewall_log_cursor = log_file.tell()
    except OSError:
        runtime_state["firewall_log_readable"] = False
        return events

    for line in new_data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # pfirewall.log format:
        # date time action protocol src-ip dst-ip src-port dst-port ...
        parts = line.split()
        if len(parts) < 8:
            continue
        action = parts[2].upper()
        src_ip = parts[4]
        dst_ip = parts[5]
        protocol = parts[3].upper()

        if action not in {"ALLOW", "DROP"}:
            continue
        if not is_public_ip(dst_ip):
            continue

        events.append({
            "action": action,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": protocol,
            "time": datetime.now().strftime("%I:%M %p"),
        })
    runtime_state["firewall_log_readable"] = True
    runtime_state["last_events_count"] = len(events)
    return events


def scan_network_and_collect_traffic():
    """
    Background task that:
    1. Reads ARP table to discover hotspot clients.
    2. Reads NAT sessions to map real destination IPs per internal hotspot device.
    """
    while True:
        try:
            detect_hotspot_prefixes()
            output = subprocess.check_output("arp -a", shell=True).decode("utf-8", errors="ignore")
            pattern = re.compile(r"^\s*([0-9\.]+)\s+([0-9a-f\-]+)\s+\w+\s*$", re.IGNORECASE)
            interface_pattern = re.compile(r"^Interface:\s+([0-9\.]+)")
            
            current_interface = ""
            
            with devices_lock:
                current_scan_ips = set()
                
                for line in output.split('\n'):
                    iface_match = interface_pattern.match(line)
                    if iface_match:
                        current_interface = iface_match.group(1)
                        continue
                        
                    if not is_hotspot_interface_ip(current_interface):
                        continue
                        
                    match = pattern.match(line)
                    if match:
                        ip = match.group(1)
                        mac = match.group(2).replace('-', ':').upper()
                        
                        if ip.startswith("224.") or ip.startswith("239.") or ip.endswith(".255") or ip == "255.255.255.255" or ip.endswith(".1"):
                            continue
                        if mac == "FF:FF:FF:FF:FF:FF" or mac == "00:00:00:00:00:00":
                            continue
                        
                        current_scan_ips.add(ip)
                        if ip not in devices:
                            try:
                                # Attempt reverse DNS lookup for hostname
                                name = socket.gethostbyaddr(ip)[0]
                            except socket.herror:
                                name = f"Device-{mac[-8:]}"
                                
                            devices[ip] = {
                                "mac": mac,
                                "name": name,
                                "traffic": [],
                                "seen_sessions": set()
                            }
                            
                keys_to_remove = [ip for ip in devices.keys() if ip not in current_scan_ips]
                for ip in keys_to_remove:
                    del devices[ip]
            active_block_domains = list(get_domains_to_block())
            events = parse_firewall_log_events()

            with devices_lock:
                for event in events:
                    internal_ip = event["src_ip"]
                    remote_ip = event["dst_ip"]
                    protocol = event["protocol"]
                    if internal_ip not in devices:
                        continue

                    domain = infer_domain_from_remote_ip(remote_ip)
                    session_key = f"{event['action']}:{protocol}:{remote_ip}"
                    info = devices[internal_ip]
                    if session_key in info["seen_sessions"]:
                        continue
                    info["seen_sessions"].add(session_key)

                    blocked_by_policy = strict_mode or any(
                        domain_matches(blocked_domain, domain) for blocked_domain in active_block_domains
                    )
                    blocked = event["action"] == "DROP" or blocked_by_policy

                    info["traffic"].insert(0, {
                        "domain": domain,
                        "remote_ip": remote_ip,
                        "time": event["time"],
                        "blocked": blocked
                    })
                    info["traffic"] = info["traffic"][:MAX_TRAFFIC_PER_DEVICE]
                    if len(info["seen_sessions"]) > 240:
                        info["seen_sessions"] = set(list(info["seen_sessions"])[-140:])
        except Exception as e:
            print(f"Background task error: {e}")
            
        time.sleep(2)

@app.on_event("startup")
def startup_tasks():
    if runtime_state["monitor_started"]:
        return
    runtime_state["monitor_started"] = True
    runtime_state["is_admin"] = is_admin_user()
    if not runtime_state["is_admin"]:
        enforcement_state["status"] = "warning"
        enforcement_state["message"] = "Backend is not running as Administrator. Real-time capture and blocking will not work."

    logging_ok = configure_firewall_logging()
    if not logging_ok:
        enforcement_state["status"] = "warning"
        enforcement_state["message"] = "Firewall logging could not be enabled. Run backend as administrator."
    threading.Thread(target=scan_network_and_collect_traffic, daemon=True).start()
    threading.Thread(target=apply_firewall_rules, daemon=True).start()

@app.get("/api/devices")
def get_devices():
    with devices_lock:
        safe_devices = {}
        for ip, data in devices.items():
            safe_devices[ip] = {
                "mac": data.get("mac"),
                "name": data.get("name"),
                "traffic": data.get("traffic", [])
            }
    return {"devices": safe_devices}

@app.post("/api/rules/{category}")
def toggle_rule(category: str, enabled: bool):
    if category in rules:
        rules[category] = enabled
        apply_firewall_rules()
        return {"status": "success", "rules": rules, "enforcement": enforcement_state}
    return {"status": "error", "message": "Category not found"}

@app.get("/api/rules")
def get_rules():
    return {
        "rules": rules,
        "blocked_services": blocked_services,
        "strict_mode": strict_mode,
        "enforcement": enforcement_state,
        "runtime": runtime_state,
        "available_domains": DOMAINS
    }


@app.get("/api/diagnostics")
def get_diagnostics():
    return {
        "runtime": runtime_state,
        "enforcement": enforcement_state,
        "hotspot_prefixes": [str(prefix) for prefix in hotspot_prefixes],
        "devices_count": len(devices),
    }


@app.post("/api/services/block")
def add_blocked_service(domain: str):
    normalized = domain.strip().lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="Domain cannot be empty")
    if normalized not in blocked_services:
        blocked_services.append(normalized)
    apply_firewall_rules()
    return {
        "status": "success",
        "blocked_services": blocked_services,
        "enforcement": enforcement_state
    }


@app.delete("/api/services/block")
def remove_blocked_service(domain: str):
    normalized = domain.strip().lower()
    if normalized in blocked_services:
        blocked_services.remove(normalized)
    apply_firewall_rules()
    return {
        "status": "success",
        "blocked_services": blocked_services,
        "enforcement": enforcement_state
    }


@app.post("/api/strict-mode")
def set_strict_mode(enabled: bool):
    global strict_mode
    strict_mode = enabled
    apply_firewall_rules()
    return {
        "status": "success",
        "strict_mode": strict_mode,
        "enforcement": enforcement_state
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
