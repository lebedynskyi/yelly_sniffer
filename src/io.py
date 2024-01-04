import errno
import os
import ssl
import urllib.parse
import urllib.request

ssl._create_default_https_context = ssl._create_unverified_context


def do_get(url):
    if not url:
        raise ValueError("url cannot be empty")
    request = urllib.request.Request(url)

    request.add_header("Content-Encoding", "UTF-8")
    request.add_header("Accept-Charset", "UTF-8")
    request.add_header("User-Agent",
                       "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36")
    request.add_header("Accept-Language", "enUS,en;q=0.9")

    stream = urllib.request.urlopen(request)
    return stream.read().decode("utf-8'")


def download_file(url, file):
    if not url:
        raise ValueError("url cannot be empty")

    # todo ADD header ?
    stream = urllib.request.urlopen(url)
    with open(file, 'wb') as output:
        output.write(stream.read())

    return True


def dump_to_file(file_path, content):
    if os.path.exists(file_path):
        return False

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(file_path, 'w') as outfile:
        outfile.writelines(content)

    return True


def ensure_folder_for_site(base_folder, url):
    host = urllib.parse.urlparse(url)
    site_folder = os.path.join(base_folder, host.netloc)
    os.makedirs(site_folder, exist_ok=True)
    return site_folder
