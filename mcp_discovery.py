import requests

def discover_mcp_servers(possible_hosts):
    discovered = []
    for host in possible_hosts:
        try:
            r = requests.get(f"http://{host}:5000/list")
            if r.status_code == 200:
                discovered.append(host)
        except Exception:
            continue
    return discovered 