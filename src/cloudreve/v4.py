from mimetypes import guess_type
from pathlib import Path
from typing import List, Literal, Union
import time

from requests import Session, request

from .utils import download_file


def revise_file_path(file_path: str) -> str:
    if not file_path.startswith('cloudreve://'):
        if file_path[0] != '/':
            file_path = '/' + file_path
        file_path = 'cloudreve://my' + file_path

    while file_path.endswith('//'):
        file_path = file_path[:-1]

    return file_path


def uris_to_list(uris: Union[str, List[str]]) -> List[str]:
    _items = uris if type(uris) == list else [uris]
    return [revise_file_path(i) for i in _items]


class CloudreveV4:
    session: Session
    user: dict
    refresh_token: Union[str, None] = None

    def __init__(self,
                 base_url: str = 'http://127.0.0.1:5212',
                 proxy=None,
                 verify=True,
                 headers=None,
                 cloudreve_session=None):
        while base_url.endswith('/'):
            base_url = base_url[:-1]
        if not base_url.endswith('/api/v4'):
            base_url += '/api/v4'
        self.base_url = base_url

        self.session = Session()
        self.session.verify = verify
        if proxy is not None:
            if type(proxy) == str:
                self.session.proxies = {'http': proxy, 'https': proxy}
            elif type(proxy) == dict:
                self.session.proxies = proxy
        if cloudreve_session is not None:
            self.session.cookies.update(
                {'cloudreve-session': cloudreve_session})
        if type(headers) == dict:
            self.session.headers.update(headers)

    def request(self, method, url, **kwargs):
        r = self.session.request(method, self.base_url + url, **kwargs)
        # print(r.text) 
        r = r.json()

        if r['code'] != 0:
            raise Exception(f'{r["code"]}: {r["msg"]}')

        return r.get('data')

    def login(self, email, password):
        r = self.request('post',
                         '/session/token',
                         json={
                             'email': email,
                             'password': password,
                         })
        self.user = r['user']
        self.session.headers.update(
            {'Authorization': 'Bearer ' + r['token']['access_token']})
        self.refresh_token = r['token']['refresh_token']

    def list(self,
             uri='/',
             page=0,
             page_size=100,
             order_by: Literal['name', 'size', 'created_at',
                               'updated_at'] = 'created_at',
             order: Literal['asc', 'desc'] = 'asc',
             next_page_token=None):
        return self.request('get',
                            '/file',
                            params={
                                'uri': revise_file_path(uri),
                                'page': page,
                                'page_size': page_size,
                                'order_by': order_by,
                                'order': order,
                                'next_page_token': next_page_token
                            })

    def get_info(self, file_uri):
        return self.request('get',
                            '/file/info',
                            params={
                                'uri': revise_file_path(file_uri),
                                'extended': True
                            })

    get_property = get_info

    def get_download_url(self, file_uri) -> str:
        r = self.request('post',
                         '/file/url',
                         json={
                             'download': True,
                             'uris': [file_uri],
                         })
        url = r['urls'][0]['url']
        if not url.startswith('http'):
            url = self.base_url + url
        return url

    def download(self, file_uri, save_path):
        download_url = self.get_download_url(revise_file_path(file_uri))
        download_file(download_url, save_path, self.session)

    def get_source_url(self, uris):
        is_list = type(uris) == list
        r = self.request('put',
                         '/file/source',
                         json={'uris': uris_to_list(uris)})
        if not is_list:
            return r[0]['link']
        return r

    def get_share_url(self,
                      file_uri,
                      downloads=None,
                      expire=None,
                      password=None,
                      share_view=None,
                      show_readme=None) -> str:
        r = self.request('put',
                         '/share',
                         json={
                             'uri': revise_file_path(file_uri),
                             'downloads': downloads,
                             'expire': expire,
                             'password': password,
                             'is_private': True if password else False,
                             'share_view': share_view,
                             'show_readme': show_readme,
                         })
        return r

    def _create(self,
                uri,
                type: Literal['folder', 'file'],
                err_on_conflict=False):
        return self.request('post',
                            '/file/create',
                            json={
                                'uri': revise_file_path(uri),
                                'type': type,
                                'err_on_conflict': err_on_conflict,
                            })

    def create_file(self, uri, err_on_conflict=False):
        return self._create(uri, 'file', err_on_conflict)

    def create_folder(self, uri, err_on_conflict=False):
        return self._create(uri, 'folder', err_on_conflict)

    create_dir = create_directory = create_folder

    def update_file_content(self, file_uri, content):
        return self.request('put',
                            '/file/content',
                            params={'uri': revise_file_path(file_uri)},
                            data=content)

    def delete(self,
               uris: Union[str | List[str]],
               unlink=False,
               trash_bin=False):
        return self.request('delete',
                            '/file',
                            json={
                                'uris': uris_to_list(uris),
                                'unlink': unlink,
                                'trash_bin': trash_bin
                            })

    remove = delete

    def rename(self, uri: str, new_name: str):
        return self.request('post',
                            '/file/rename',
                            json={
                                'uri': revise_file_path(uri),
                                'new_name': new_name
                            })

    def copy_or_move(self, uris, dst, copy=False):
        return self.request('post',
                            '/file/move',
                            json={
                                'uris': uris_to_list(uris),
                                'dst': revise_file_path(dst),
                                'copy': copy,
                            })

    def copy(self, uris: Union[str, List[str]], dst: str):
        return self.copy_or_move(uris, dst, copy=True)

    def move(self, uris: Union[str, List[str]], dst: str):
        return self.copy_or_move(uris, dst, copy=False)

    def _upload_to_local(self, local_file: Path, session_id, chunk_size,
                         **kwards):
        with open(local_file, 'rb') as file:
            block_id = 0
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                self.request(
                    'post',
                    f'/file/upload/{session_id}/{block_id}',
                    headers={
                        'Content-Length': str(len(chunk)),
                        'Content-Type': 'application/octet-stream',
                    },
                    data=chunk,
                )
                block_id += 1

    def _upload_to_remote_direct(self, local_file: Path, session_id, chunk_size,
                                 upload_urls, credential, **kwards):
        """
        [修正版] 直传 Slave 节点：基于文档规范
        1. 使用 URL Query 参数传递 chunk index (?chunk=0)
        2. 使用 credential 作为 Authorization 头
        """
        base_upload_url = upload_urls[0]
        
        # 构造专属 Header，覆盖 Session 默认的 Token
        # Spec 要求 Authorization 必须是 credential 的值
        headers = {
            'Content-Type': 'application/octet-stream',
            'Authorization': credential
        }

        with open(local_file, 'rb') as file:
            block_id = 0
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                
                headers['Content-Length'] = str(len(chunk))
                
                # Spec: Chunk index is passed through query `chunk`
                # 使用 params 参数自动处理 ?chunk=x
                params = {'chunk': block_id}
                
                # 直发 POST 请求
                # 注意：这里使用 request (来自 requests 库) 而不是 self.request
                r = request('post', base_upload_url, params=params, headers=headers, data=chunk)
                
                if r.status_code != 200:
                     raise Exception(f"Slave Upload Failed: HTTP {r.status_code} - {r.text}")
                
                block_id += 1

    def _upload_to_onedrive(self, local_file: Path, session_id, chunk_size,
                            upload_urls, callback_secret, **kwards):
        upload_url = upload_urls[0]
        file_size = local_file.stat().st_size
        with open(local_file, 'rb') as file:
            for i in range(0, file_size, chunk_size):
                start = i
                end = min(i + chunk_size, file_size) - 1
                request(
                    'put',
                    upload_url,
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'Content-Range': f'bytes {start}-{end}/{file_size}',
                    },
                    data=file.read(chunk_size),
                )
        self.request('post',
                     f'/callback/onedrive/{session_id}/{callback_secret}')

    def upload(self, local_file_path, uri):
        '''
        上传文件
        '''
        local_file = Path(local_file_path)
        if not local_file.is_file():
            raise FileNotFoundError(f'{local_file_path} is not a file')

        uri = revise_file_path(uri)
        dir = uri[:uri.rfind('/')]
        
        policy = self.list(dir)['storage_policy']
        policy_id, policy_type = policy['id'], policy['type']

        mime_type, _ = guess_type(local_file.name)
        size = local_file.stat().st_size
        time = int(local_file.stat().st_mtime * 1000)

        r = self.request('put',
                         '/file/upload',
                         json={
                             'uri': uri,
                             'size': size,
                             'last_modified': time,
                             'policy_id': policy_id,
                             'mime_type': mime_type
                         })

        # 【核心逻辑更新】
        # 1. Remote 直传模式 (检测 upload_urls 是否存在且不为空)
        if policy_type == 'remote' and r.get('upload_urls') and len(r['upload_urls']) > 0:
            return self._upload_to_remote_direct(
                local_file=local_file,
                **r,
            )
        # 2. Local 或 Relay 模式
        elif policy_type == 'local' or policy_type == 'remote':
            return self._upload_to_local(
                local_file=local_file,
                **r,
            )
        # 3. OneDrive
        elif policy_type == 'onedrive':
            return self._upload_to_onedrive(
                local_file=local_file,
                **r,
            )
        else:
            raise ValueError(f'存储策略 {policy_type} 暂时不受支持')