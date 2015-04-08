import json, sys, os, time

with open(sys.argv[1], "r") as fr:
  d = json.loads(fr.read())

for f in d:
  st = os.stat(os.path.join(sys.argv[2], f['fields']['img']))

  f['fields']['created'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_ctime))
  f['fields']['modified'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))

print json.dumps(d, indent=4)

