
import json
import re

def extract():
    with open("tiktok_mobile_debug.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # Try to find all JSON scripts
    scripts = re.findall(r'<script [^>]*type="application/json"[^>]*>(.*?)</script>', html)
    print(f"Found {len(scripts)} scripts")
    
    for i, script in enumerate(scripts):
        if "itemStruct" in script:
            print(f"Script {i} matches!")
            try:
                data = json.loads(script)
                # Find the path to itemStruct
                def find_path(d, target, path=""):
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if k == target:
                                return path + "." + k
                            res = find_path(v, target, path + "." + k)
                            if res:
                                return res
                    elif isinstance(d, list):
                        for i, v in enumerate(d):
                            res = find_path(v, target, path + f"[{i}]")
                            if res:
                                return res
                    return None
                
                path = find_path(data, "itemStruct")
                print(f"Path: {path}")
                # Save just this script for inspection
                with open(f"script_{i}.json", "w", encoding="utf-8") as out:
                    json.dump(data, out, indent=2)
            except Exception as e:
                print(f"Error parsing script {i}: {e}")

if __name__ == "__main__":
    extract()
