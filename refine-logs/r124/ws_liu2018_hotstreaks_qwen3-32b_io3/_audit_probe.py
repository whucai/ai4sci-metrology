import socket,sys,json
net={'reachable':False,'err':''}
try:
    s=socket.create_connection(('1.1.1.1',53),timeout=3); net['reachable']=True; s.close()
except Exception as e: net['err']=type(e).__name__
open('/workspace/_audit_net.json','w').write(json.dumps(net))
