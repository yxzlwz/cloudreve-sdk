from requests import Session


def download_file(url: str, save_path: str, session: Session = None):
    s = session or Session()

    r = session.get(url, stream=True)

    with open(save_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
