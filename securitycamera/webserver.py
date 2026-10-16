import os
import socket
import time


def get_photo_list():
    """Returns a list of all JPEG images stored on the device root."""
    try:
        return [f for f in os.listdir('/sd') if f.lower().endswith('.jpg') or f.lower().endswith('.jpeg')]
    except OSError:
        return []


def generate_web_ui():
    """Generates the dynamic gallery HTML interface."""
    html = """<!DOCTYPE html><html><head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Security Camera Photo Hub</title>
    <style>
        body{font-family:sans-serif; background:#f4f4f4; margin:20px; text-align:center;}
        .btn{background:#007BFF; color:white; padding:10px 20px; border:none; border-radius:4px; cursor:pointer; text-decoration:none; display:inline-block; margin:10px;}
        .gallery{display:flex; flex-wrap:wrap; justify-content:center; gap:20px; margin-top:20px;}
        .card{background:white; padding:10px; border-radius:8px; box-shadow:0 4px 6px rgba(0,0,0,0.1); width:200px;}
        .card img{width:100%; height:140px; object-fit:cover; border-radius:4px;}
        .actions{margin-top:10px;}
        .dl,.del{display:inline-block; box-sizing:border-box; border:none; border-radius:4px; color:white; font:bold 10px sans-serif; line-height:1.2; padding:6px 12px; text-decoration:none; cursor:pointer; vertical-align:middle;}
        .dl{background:#28a745;}
        .del{background:#dc3545; margin-left:10px;}
        .toolbar{margin-top:20px;}
        .delall{background:#dc3545; color:white; border:none; padding:10px 20px; border-radius:4px; cursor:pointer;}
        form{display:inline; margin:0;}
    </style>
    </head><body>
    <h1>ESP32-CAM Storage</h1>"""

    photos = get_photo_list()
    if not photos:
        html += "<p>No photos saved yet.</p>"
    else:
        html += """<div class='toolbar'>
        <form method='post' action='/delete_all' onsubmit="return confirm('Delete ALL photos?');">
            <button class='delall' type='submit'>Delete all</button>
        </form>
        </div>"""

    html += "<div class='gallery'>"
    for p in photos:
            html += f"""
            <div class='card'>
                <img src='/file?path={p}' loading='lazy'>
                <p style='font-size:12px; word-break:break-all;'>{p}</p>
                <div class='actions'>
                    <a class='dl' href='/file?path={p}' download='{p}'>Download</a>
                    <form method='post' action='/delete' onsubmit="return confirm('Delete {p}?');">
                        <input type='hidden' name='path' value='{p}'>
                        <button class='del' type='submit'>Delete</button>
                    </form>
                </div>
            </div>"""

    html += "</div></body></html>"
    return html


def run(access_point):
    _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _socket.bind(('', 80))
    _socket.listen(5)
    # Time out accept() so the station check below runs even when no client is requesting
    _socket.settimeout(1)
    print("Web UI Server running on port 80...")

    while True:
        if not access_point.status('stations'):
            print("No devices connected. Stopping web server.")
            break

        try:
            _buffer, addr = _socket.accept()
        except OSError:
            # Accept timed out; loop back and re-check connected stations
            continue

        try:
            request = _buffer.recv(1024).decode('utf-8')
            head, _, body = request.partition('\r\n\r\n')

            # Simple routing logic parse
            first_line = head.split('\r\n')[0]
            if not first_line:
                continue

            method, path = first_line.split(' ')[0:2]

            # Read the rest of a form body if it did not arrive with the headers
            content_length = 0
            for line in head.split('\r\n'):
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1])
            while len(body) < content_length:
                chunk = _buffer.recv(content_length - len(body))
                if not chunk:
                    break
                body += chunk.decode('utf-8')

            # Route: Delete a photo from the SD card
            if method == 'POST' and path == '/delete':
                filename = body.split('=')[1]
                try:
                    os.remove('/sd/' + filename)
                    print(f"Deleted photo: {filename}")
                except OSError as e:
                    print("Failed to delete photo:", e)
                _buffer.send('HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n')

            # Route: Delete every photo from the SD card
            elif method == 'POST' and path == '/delete_all':
                for filename in get_photo_list():
                    try:
                        os.remove('/sd/' + filename)
                    except OSError as e:
                        print("Failed to delete photo:", filename, e)
                print("Deleted all photos")
                _buffer.send('HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n')

            # Route: Dashboard UI
            elif path == '/' or path == '/index.html':
                _buffer.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                _buffer.sendall(generate_web_ui())

            # Route: Serve/Stream an individual image file
            elif path.startswith('/file?path='):
                filename = path.split('=')[1]
                try:
                    with open('/sd/' + filename, 'rb') as f:
                        _buffer.send('HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n\r\n')
                        # Stream file in smaller chunks to avoid memory fragmentation
                        while True:
                            chunk = f.read(512)
                            if not chunk:
                                break
                            _buffer.sendall(chunk)
                except Exception as e:
                    _buffer.send('HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nFile Not Found')

            else:
                _buffer.send('HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 Page Not Found')

        except Exception as ex:
            print("Error handling client connection:", ex)
        finally:
            _buffer.close()

    _socket.close()
