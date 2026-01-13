
from django.http import HttpResponse
from django.conf import settings
import socket
import time

def debug_email_view(request):
    output = ["<h1>SMTP Connectivity Check</h1>"]
    
    # Target: smtp.gmail.com
    host = 'smtp.gmail.com'
    ports = [587, 465, 2525, 25]
    
    output.append(f"<h2>target: {host}</h2>")
    
    # 1. Resolve DNS (IPv4 Force)
    try:
        # Force IPv4 resolution
        ips = socket.getaddrinfo(host, 443, socket.AF_INET)
        target_ip = ips[0][4][0]
        output.append(f"<p><strong>Resolved IP (IPv4):</strong> {target_ip}</p>")
    except Exception as e:
        output.append(f"<p style='color:red'>DNS Error: {e}</p>")
        return HttpResponse("".join(output))

    output.append("<ul>")
    
    # 2. Scan Ports
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3) # 3 Second Timeout
        start = time.time()
        try:
            result = s.connect_ex((target_ip, port))
            duration = round((time.time() - start) * 1000, 2)
            
            if result == 0:
                output.append(f"<li style='color:green'><strong>Port {port}: OPEN</strong> ({duration}ms)</li>")
            else:
                output.append(f"<li style='color:red'>Port {port}: CLOSED/BLOCKED (Err: {result})</li>")
        except Exception as e:
            output.append(f"<li style='color:red'>Port {port}: ERROR ({e})</li>")
        finally:
            s.close()
            
    output.append("</ul>")
    
    output.append("<h3>Interpretation:</h3>")
    output.append("<p>If ports are <strong>CLOSED</strong>, Render is blocking SMTP. You MUST use an HTTP-based Email API (like SendGrid, Mailgun) or request Render support to unblock SMTP.</p>")
    
    return HttpResponse("".join(output))
