import os
import requests

def fetch_terminals():
    api_key = os.getenv('WSDOT_API_KEY')
    if not api_key:
        raise Exception("WSDOT_API_KEY environment variable not set")
    url = 'https://wsdot.wa.gov/Ferries/API/Terminals/rest/terminalbasics'
    params = {'apiaccesscode': api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    for terminal in data:
        print(f"{terminal['TerminalName']}: {terminal['TerminalID']}")

if __name__ == "__main__":
    fetch_terminals()
