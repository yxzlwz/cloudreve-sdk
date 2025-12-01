from mimetypes import guess_type
from pathlib import Path
from typing import List, Literal, Union

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
    _items = uris if type(uris) is list else [uris]
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
        '''
        @param base_url(str): Cloudreve站点地址
        @param proxy(dict|str|None): 代理
        @param verify(bool): 是否验证ssl证书
        @param headers(dict|None): 自定义请求头
        @param cloudreve_session(str|None): Cloudreve会话ID，提供后可无需调用登录接口
        '''

        while base_url.endswith('/'):
            base_url = base_url[:-1]
        if not base_url.endswith('/api/v4'):
            base_url += '/api/v4'
        self.base_url = base_url

        self.session = Session()
        self.session.verify = verify
        if proxy is not None:
            if type(proxy) is str:
                self.session.proxies = {'http': proxy, 'https': proxy}
            elif type(proxy) is dict:
                self.session.proxies = proxy
        if cloudreve_session is not None:
            self.session.cookies.update(
                {'cloudreve-session': cloudreve_session})
        if type(headers) is dict:
            self.session.headers.update(headers)

    def request(self, method, url, **kwargs):
        r = self.session.request(method, self.base_url + url, **kwargs)
        r = r.json()

        if r['code'] != 0:
            raise Exception(f'{r["code"]}: {r["msg"]}')

        return r.get('data')

    def login(self, email, password):
        '''
        登录（请在执行其他操作前调用此方法）
        @param email: 邮箱
        @param password: 密码
        '''
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
        '''
        列出目录下的文件
        @param path: 目录路径
        @return: 文件列表
            - parent: 目录文件夹信息
            - files: 文件列表
            - storage_policy: 文件存储策略
        '''
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
        '''
        获取文件信息
        @param file_uri: 文件URI
        @return: 文件信息
        '''
        return self.request('get',
                            '/file/info',
                            params={
                                'uri': revise_file_path(file_uri),
                                'extended': True
                            })

    get_property = get_info

    def get_download_url(self, file_uri) -> str:
        '''
        获取文件临时下载链接
        @param file_uri: 文件URI
        @return: 下载链接
        '''
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
        '''
        下载文件至本地
        @param file_uri: 文件URI
        @param save_path: 保存路径
        '''
        download_url = self.get_download_url(revise_file_path(file_uri))
        download_file(download_url, save_path, self.session)

    def get_source_url(self, uris):
        '''
        获取文件直链
        @param uris(str|list): 文件URL，可传递列表
        @return: 直链列表，若link_only=True，则列表项为字符串；否则返回包含file_url和link的字典列表。
        请注意：由于Cloudreve API设计问题，传入的文件URL为列表时，返回的数据无序且不包含file_uri。因此请勿在同时获取多个直链时启用link_only。
        '''
        is_list = type(uris) is list
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
        '''
        获取文件分享链接
        @param file_uri: 文件或文件夹URI
        @param downloads(int|None): 下载次数限制（默认不限制）
        @param expire(int|None): 过期时间（自现在开始的秒数）
        @param password(str|None): 密码
        @param share_view(bool|None): 是否允许预览分享的文件夹（仅对文件夹有效，默认False）
        @param show_readme(bool|None): 是否显示README文件（仅对文件夹有效，默认False）
        @return: 分享链接
        '''
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
        '''
        创建文件夹或文件
        @param uri: 目标URI
        @param type: 创建类型，folder或file
        @param err_on_conflict: 若目标已存在，是否报错
        '''
        return self.request('post',
                            '/file/create',
                            json={
                                'uri': revise_file_path(uri),
                                'type': type,
                                'err_on_conflict': err_on_conflict,
                            })

    def create_file(self, uri, err_on_conflict=False):
        '''
        创建文件
        @param uri: 目标URI
        @param err_on_conflict: 若目标已存在，是否报错
        '''
        return self._create(uri, 'file', err_on_conflict)

    def create_folder(self, uri, err_on_conflict=False):
        '''
        创建文件夹
        @param uri: 目标URI
        @param err_on_conflict: 若目标已存在，是否报错
        '''
        return self._create(uri, 'folder', err_on_conflict)

    create_dir = create_directory = create_folder

    def update_file_content(self, file_uri, content):
        '''
        更新文本文件内容
        @param file_uri: 文件URI
        @param content: 新内容
        '''
        return self.request('put',
                            '/file/content',
                            params={'uri': revise_file_path(file_uri)},
                            data=content)

    def delete(self,
               uris: Union[str | List[str]],
               unlink=False,
               trash_bin=False):
        '''
        删除文件或文件夹
        @param uris(str|list): 文件URI
        @param unlink: 仅解除链接
        @param trash_bin: 是否移动至回收站
        '''
        return self.request('delete',
                            '/file',
                            json={
                                'uris': uris_to_list(uris),
                                'unlink': unlink,
                                'trash_bin': trash_bin
                            })

    remove = delete

    def rename(self, uri: str, new_name: str):
        '''
        重命名文件或文件夹
        @param uri: 文件URI
        @param new_name: 新名称
        '''
        return self.request('post',
                            '/file/rename',
                            json={
                                'uri': revise_file_path(uri),
                                'new_name': new_name
                            })

    def copy_or_move(self, uris, dst, copy=False):
        '''
        通过来源文件夹和文件ID复制文件或文件夹
        @param uris: 源文件或文件夹URI列表
        @param dst: 目标目录
        @param copy: 是否为复制操作，默认为False（移动操作）
        '''
        return self.request('post',
                            '/file/move',
                            json={
                                'uris': uris_to_list(uris),
                                'dst': revise_file_path(dst),
                                'copy': copy,
                            })

    def copy(self, uris: Union[str, List[str]], dst: str):
        '''
        通过路径复制文件或文件夹
        @param uris: 源文件或文件夹URI或URI列表
        @param dst: 目标目录
        '''
        return self.copy_or_move(uris, dst, copy=True)

    def move(self, uris: Union[str, List[str]], dst: str):
        '''
        通过路径移动文件或文件夹
        @param uris: 源文件或文件夹URI或URI列表
        @param dst: 目标目录
        '''
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

    def _upload_to_remote_direct(self, local_file: Path, session_id,
                                 chunk_size, upload_urls, credential,
                                 **kwards):
        base_upload_url = upload_urls[0]

        headers = {
            'Content-Type': 'application/octet-stream',
            'Authorization': credential,
        }

        with open(local_file, 'rb') as file:
            block_id = 0
            chunk = file.read(chunk_size)
            while chunk:
                headers['Content-Length'] = str(len(chunk))

                self.request('post',
                             base_upload_url,
                             params={'chunk': block_id},
                             headers=headers,
                             data=chunk)

                block_id += 1
                chunk = file.read(chunk_size)

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

    def _upload_to_oss(
        self,
        local_file: Path,
        sessionID,
        chunkSize,
        expires,
        uploadURLs,
        completeURL,
        **kwards,
    ):
        upload_url = uploadURLs[0]
        file_size = local_file.stat().st_size
        with open(local_file, 'rb') as file:
            for i in range(0, file_size, chunkSize):
                start = i
                end = min(i + chunkSize, file_size) - 1
                request(
                    'put',
                    upload_url,
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'Content-Range': f'bytes {start}-{end}/{file_size}',
                    },
                    data=file.read(chunkSize),
                )
        request('post', completeURL)

    def upload(self, local_file_path, uri):
        '''
        上传文件
        @param local_file_path: 本地文件路径
        @param uri: 文件目标路径（包含文件名）
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

        if policy_type == 'remote' and r.get('upload_urls') and len(
                r['upload_urls']) > 0:
            # Remote 直传模式
            return self._upload_to_remote_direct(
                local_file=local_file,
                **r,
            )
        elif policy_type == 'local' or policy_type == 'remote':
            # Local 或 Relay 模式
            return self._upload_to_local(
                local_file=local_file,
                **r,
            )
        elif policy_type == 'onedrive':
            return self._upload_to_onedrive(
                local_file=local_file,
                **r,
            )
        # elif policy_type == 'oss':
        #     return self._upload_to_oss(
        #         local_file=local_file,
        #         **r,
        #     )
        else:
            raise ValueError(f'存储策略 {policy_type} 暂时不受支持')
