import sqlite3
import json
import os

def extract_firefox_cookies(profile_path, output_json, domains):
    db_path = '/tmp/cookies_copy.sqlite'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return False

    # Connect to the SQLite database
    # We might need to copy it if it's locked by Firefox
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cookies = []
    for domain in domains:
        # Query for GitHub cookies
        # Firefox cookies.sqlite columns: host, path, name, value, expiry, isSecure, isHttpOnly, ...
        cursor.execute("SELECT host, path, name, value, expiry, isSecure, isHttpOnly FROM moz_cookies WHERE host LIKE ?", (f'%{domain}%',))
        
        for row in cursor.fetchall():
            cookie = {
                "name": row[2],
                "value": row[3],
                "domain": row[0],
                "path": row[1],
                "expires": row[4],
                "secure": bool(row[5]),
                "httpOnly": bool(row[6]),
                "sameSite": "Lax" # Default for safety
            }
            cookies.append(cookie)
    
    conn.close()

    with open(output_json, 'w') as f:
        json.dump(cookies, f, indent=2)
    
    print(f"Extracted {len(cookies)} cookies to {output_json}")
    return True

if __name__ == "__main__":
    profile = "/home/lzw/.mozilla/firefox/stp0k50c.default-release"
    extract_firefox_cookies(profile, "/tmp/github_cookies.json", ["github.com"])
