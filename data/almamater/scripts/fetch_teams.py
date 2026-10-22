import os, json, urllib.request, pathlib
D = pathlib.Path(__file__).resolve().parent/"cache"; f = D/"teams.json"
if not f.exists():
    req = urllib.request.Request("https://api.collegefootballdata.com/teams", headers={"Authorization": "Bearer " + os.environ["CFBD_KEY"]})
    with urllib.request.urlopen(req, timeout=120) as r:
        f.write_bytes(r.read()); msg=f"teams remaining={r.headers.get('X-CallLimit-Remaining')}"
    print(msg); open(D/"calls.log","a").write(msg+"\n")
d=json.load(open(f)); print(len(d)); print(d[0])
