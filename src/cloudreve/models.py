from pathlib import Path

from requests import Session, request
from urllib.parse import quote_plus


def generate_src(file_id, is_dir) -> dict:
    src = {
        'items': [],
        'dirs': [],
    }
    if is_dir:
        src['dirs'].append(file_id)
    else:
        src['items'].append(file_id)
    return src


def revise_file_path(file_path: str) -> str:
    if file_path[0] != '/':
        file_path = '/' + file_path

    while file_path.endswith('/'):
        file_path = file_path[:-1]

    return file_path


class Cloudreve:
    session: Session
    user: dict

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
        if not base_url.endswith('/api/v3'):
            base_url += '/api/v3'
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

        r = self.request('POST',
                         '/user/session',
                         json={
                             'userName': email,
                             'Password': password,
                             'captchaCode': ''
                         })
        self.user = r

    def list(self, path='/'):
        '''
        列出目录下的文件
        @param path: 目录路径
        @return: 文件列表
            - parent: 目录文件夹ID
            - objects: 文件列表
            - policy: 文件存储策略
        '''

        return self.request('get', '/directory' + quote_plus(path, safe=[]))

    def get_id(self, file_path: str, return_type=False):
        '''
        根据文件路径获取文件ID
        @param file_path: 文件路径
        @param return_type: 是否返回文件类型
        @return: 文件ID, (文件类型)
        '''

        file_path = revise_file_path(file_path)

        dir = file_path[:file_path.rfind('/')]
        name = file_path[file_path.rfind('/') + 1:]

        file_list = self.list(dir)

        for file in file_list['objects']:
            if file['name'] == name:
                if return_type:
                    return file['id'], file['type']
                return file['id']

        raise Exception('File not found')

    def get_property(self, file_id, is_dir=False, trace_root=False):
        '''
        获取文件属性
        @param file_id: 文件ID
        @param is_dir: 是否为文件夹
        @param trace_root: 是否跟踪根目录
        @return: 文件属性
            - created_at: 创建时间
            - updated_at: 修改时间
            - policy: 存储策略名称
            - size: 文件（夹）大小
            - child_folder_num: 子文件夹数
            - child_file_num: 子文件数
            - path: 文件路径（仅在trace_root=True时有效）
        '''

        return self.request('get',
                            f'/object/property/{file_id}',
                            params={
                                'is_folder': is_dir,
                                'trace_root': trace_root,
                            })

    def get_download_url(self, file_id) -> str:
        '''
        获取文件临时下载链接
        @param file_id: 文件ID
        @return: 下载链接
        '''

        return self.request('put', f'/file/download/{file_id}')

    def download(self, file_id, save_path):
        '''
        下载文件至本地
        @param file_id: 文件ID
        @param save_path: 保存路径
        '''

        download_url = self.get_download_url(file_id)

        r = self.session.get(download_url, stream=True)

        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def get_source_url(self, file_id, url_only=True):
        '''
        获取文件直链
        @param file_id: 文件ID，可传递列表
        @param url_only: 若为True则只返回直链，若为False则返回包含url和name的字典。
        @return: 直链列表，若url_only=True，则列表项为字符串；否则返回包含url和name的字典列表。
        请注意：由于Cloudreve API设计问题，传入的文件ID为列表时，返回的数据无序且不包含文件ID。因此请勿在同时获取多个直链时启用url_only。
        '''

        is_list = type(file_id) == list

        items = file_id if is_list else [file_id]

        r = self.request('post', '/file/source', json={'items': items})

        res = []

        if url_only:
            assert len(
                r
            ) == 1, '由于Cloudreve API设计问题，传入的文件ID为列表时，返回的数据无序且不包含文件ID。因此请勿在同时获取多个直链时启用url_only。'
            for i in r:
                res.append(i['url'])
        else:
            for i in r:
                res.append({'url': i['url'], 'name': i['name']})

        if is_list:
            return res
        else:
            return res[0]

    def get_share_url(self,
                      id,
                      is_dir=False,
                      preview=True,
                      downloads=-1,
                      expire=0,
                      password=''):
        '''
        获取文件分享链接
        @param id: 文件或文件夹ID
        @param is_dir: 是否为文件夹
        @param preview: 是否允许预览
        @param downloads: 下载次数限制（默认不限制）
        @param expire: 过期时间（自现在开始的秒数）
        @param password: 密码
        '''

        assert downloads <= 0 or expire > 0, '由于Cloudreve限制，启用下载次数限制需同时启用过期时间，否则分享将立即过期'

        r = self.request('post',
                         '/share',
                         json={
                             'id': id,
                             'is_dir': is_dir,
                             'preview': preview,
                             'downloads': downloads,
                             'expire': expire,
                             'password': password,
                         })

        return r

    def delete(self, file_id, is_dir=False, force=False, unlink=False):
        '''
        删除文件或文件夹
        @param file_id: 文件ID
        @param is_dir: 是否为文件夹
        @param force: 强制删除文件
        @param unlink: 仅解除链接
        '''

        body = {
            'force': force,
            'unlink': unlink,
        }
        body.update(generate_src(file_id, is_dir))

        self.request('delete', '/object', json=body)

    def rename(self, file_id, new_name, is_dir=False):
        '''
        重命名文件或文件夹
        @param file_id: 文件ID
        @param new_name: 新名称
        @param is_dir: 是否为文件夹
        '''

        body = {
            'action': 'rename',
            'src': generate_src(file_id, is_dir),
            'new_name': new_name,
        }

        self.request('post', '/object/rename', json=body)

    def _copy(self, src_dir, file_id, dst_dir, is_dir=False):
        '''
        通过来源文件夹和文件ID复制文件或文件夹
        @param src_dir: 来源文件夹
        @param file_id: 文件ID
        @param dst_dir: 目标目录
        @param is_dir: 操作的文件是否为文件夹
        '''

        body = {
            'src_dir': src_dir,
            'src': generate_src(file_id, is_dir),
            'dst': dst_dir,
        }

        self.request('post', '/object/copy', json=body)

    def copy(self, file_path, dst_dir):
        '''
        通过路径复制文件或文件夹
        @param file_path: 源文件或文件夹路径
        @param dst_dir: 目标目录
        '''

        file_path = revise_file_path(file_path)

        src_dir = file_path[:file_path.rfind('/')]
        src_file_id, file_type = self.get_id(file_path, True)

        self._copy(src_dir, src_file_id, dst_dir, file_type == 'dir')

    def _move(self, src_dir, file_id, dst_dir, is_dir=False):
        '''
        通过来源文件夹和文件ID移动文件或文件夹
        @param src_dir: 来源文件夹
        @param file_id: 文件ID
        @param dst_dir: 目标目录
        @param is_dir: 操作的文件是否为文件夹
        '''

        body = {
            'action': 'move',
            'src_dir': src_dir,
            'src': generate_src(file_id, is_dir),
            'dst': dst_dir,
        }

        self.request('patch', '/object', json=body)

    def move(self, file_path, dst_dir):
        '''
        通过路径移动文件或文件夹
        @param file_path: 源文件或文件夹路径
        @param dst_dir: 目标目录
        '''

        file_path = revise_file_path(file_path)

        src_dir = file_path[:file_path.rfind('/')]
        src_file_id, file_type = self.get_id(file_path, True)

        self._move(src_dir, src_file_id, dst_dir, file_type == 'dir')

    def create_dir(self, dir_path):
        '''
        创建文件夹
        @param dir_path: 文件夹路径
        '''

        dir_path = revise_file_path(dir_path)

        self.request('put', '/directory', json={'path': dir_path})

    def upload_to_local(self, local_file: Path, sessionID, chunkSize, expires):
        with open(local_file, 'rb') as file:
            file_data = file.read()
            self.request(
                'post',
                f'/file/upload/{sessionID}/0',
                headers={
                    'Content-Type': 'application/octet-stream',
                },
                data=file_data,
            )

    def upload_to_onedrive(self, local_file: Path, sessionID, chunkSize,
                           expires, uploadURLs):
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
        self.request('post', f'/callback/onedrive/finish/{sessionID}', json={})

    def upload(self,
               file_path,
               local_file_path,
               policy_id=None,
               policy_type=None):
        '''
        上传文件通用方法
        @param file_path: 文件目标路径
        @param local_file_path: 本地文件路径
        @param policy_id: 存储策略ID（可选）
        @param policy_type: 存储策略类型（可选）
        当且仅当存储策略ID和类型同时存在时参数生效，否则程序将通过list方法获取存储策略信息
        '''

        local_file = Path(local_file_path)
        if not local_file.is_file():
            raise FileNotFoundError(f'{local_file_path} is not a file')

        dir = file_path[:file_path.rfind('/')] or '/'
        name = file_path[file_path.rfind('/') + 1:]

        if not (policy_id and policy_type):
            policy = self.list(dir)['policy']
            policy_id, policy_type = policy['id'], policy['type']

        body = {
            'path': dir,
            'name': name,
            'size': local_file.stat().st_size,
            'last_modified': int(local_file.stat().st_mtime * 1000),
            'policy_id': policy_id,
            'mime_type': '',
        }

        r = self.request('put', '/file/upload', json=body)

        if policy_type == 'local':
            return self.upload_to_local(
                local_file=local_file,
                **r,
            )
        elif policy_type == 'onedrive':
            return self.upload_to_onedrive(
                local_file=local_file,
                **r,
            )
        else:
            raise ValueError(f'存储策略 {policy_type} 暂时不受支持，若有需求请在GitHub留言')
