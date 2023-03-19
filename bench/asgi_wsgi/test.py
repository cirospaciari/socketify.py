import sys
import io
import time
import datetime
import socket
import optparse

parser = optparse.OptionParser("usage: %prog [options]", add_help_option=False)
parser.add_option("-h", "--host", dest="host", default='127.0.0.1', type="string")
parser.add_option("-p", "--port", dest="port", default=3000, type="int")
(opt, args) = parser.parse_args()

def get_request(path = r'/', host = '127.0.0.1', port = 3000):
    req  = f'GET {path}' + r' HTTP/1.1' + '\r\n'
    req += f'Host: {host}:{port}\r\n'
    req += r'User-Agent: curl/7.66.0' + '\r\n'
    req += r'Accept: */*' + '\r\n'
    req += '\r\n'
    return req
    
payload_tiny = get_request(host = opt.host, port = opt.port)
payload_tiny = payload_tiny.encode('utf-8')

def create_sock(timeout = 0.001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((opt.host, opt.port))
    return sock

sock = create_sock()
sock.sendall(payload_tiny)
time.sleep(0.020)
resp = sock.recv(4096)
print('====== response ========')
print(resp.decode('utf-8'))
print('========================')
sock.close()

start_time = datetime.datetime.now()
test1_limit = start_time  + datetime.timedelta(seconds = 1)
test2_limit = test1_limit + datetime.timedelta(seconds = 10)

sock = create_sock()
while True:
    if datetime.datetime.now() >= test1_limit:
        break
    sock.sendall(payload_tiny)
    try:
        resp = sock.recv(4096)
    except socket.timeout:
        pass

print(f'Test 1 completed!')
sock.close()

req_num = 1000*1000
payload_huge = payload_tiny * req_num
#print(len(payload_huge))
print(f'Run test 2 ...')
totalsent = 0
totalresp = b''
sock = create_sock()
while True:
    if datetime.datetime.now() >= test2_limit:
        print(f'Test 2: Timeout exceeded!')
        break
    try:
        rc = sock.send(payload_huge[totalsent:])
        if rc == 0:
            #raise RuntimeError("socket connection broken")
            pass
        totalsent += rc
        resp = sock.recv(65*1024)
        totalresp += resp
    except socket.timeout:
        pass
    except ConnectionResetError:
        print(f'totalsent = {totalsent}, totalrecv = {len(totalresp)}')
        print(f'LastResp: {totalresp[-256:]}')
        raise

sock.close()
print("==== Test Finish =====")
