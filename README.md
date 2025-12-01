# Cloudreve SDK

本项目为**第三方制作**的 [Cloudreve](https://github.com/cloudreve/Cloudreve) V3 和 V4 社区版的 Python SDK。

- 开源地址：https://github.com/yxzlwz/cloudreve-sdk
- PyPI：https://pypi.org/project/cloudreve/
- API文档（我们维护 V3 版本；官方提供了 V4 版本的 API 文档）：https://cloudreve.apifox.cn/

## 安装

```bash
pip3 install cloudreve
```

## 适配情况

| 功能                 | V3 适配情况 | V4 适配情况   |
| -------------------- | ----------- | ------------- |
| 登录                 | ✅           | ✅             |
| 列目录               | ✅           | ✅             |
| 获取文件ID           | ✅           | 不需要        |
| 删除文件             | ✅           | ✅             |
| 获取文件属性         | ✅           | ✅             |
| 获取下载URL          | ✅           | ✅             |
| 下载文件             | ✅           | ✅             |
| 创建目录             | ✅           | ✅             |
| 复制文件             | ✅           | ✅             |
| 重命名文件           | ✅           | ✅             |
| 移动文件             | ✅           | ✅             |
| 获取文件直链         | ✅           | ✅             |
| 获取分享链接         | ✅           | ✅             |
| 上传文件（本地存储） | ✅           | ✅             |
| 上传文件（OneDrive） | ✅           | ✅             |
| 上传文件（OSS）      | 待测试      | 待测试        |
| 上传文件（从机模式） | ❌           | ✅（未经测试） |

说明：

- V4 版本使用 URI 来标识文件和目录，不再需要文件ID。
- “待测试”表示该功能已实现，但由于缺乏测试环境，暂未进行测试，也没有公开使用。如果你使用该存储方案搭建 Cloudreve V4，并且愿意协助测试该功能，请您联系我。

## 示例（V3）

- 每个方法都写了详细注释，可以直接阅读源码了解
- 除少数特殊说明的接口外，几乎所有对文件的操作都需要使用由**字母和数字**组成的文件ID作为参数

```python
from cloudreve import Cloudreve

# 初始化
conn = Cloudreve('http://127.0.0.1:5212')

# 登录
conn.login('admin@cloudreve.org', '123456')

# 列目录
conn.list("/")

# 获取文件ID
file_id = conn.get_id('/hello.py')

# 删除文件
conn.delete(file_id, is_dir=False)

# 获取文件属性
data = conn.get_property(file_id)
print(data)

# 获取临时下载URL
url = conn.get_download_url(file_id)

# 下载文件到本地
conn.download(file_id, 'hello_world.py')

# 创建目录
conn.create_dir('/python')

# 复制文件
conn.copy('/hello.py', '/python')

# 重命名文件
conn.rename(file_id, 'world.py')

# 移动文件
conn.move('/world.py', '/python')

# 上传文件
conn.upload('/my_file_backup.py', 'D:/my_file.py')

# 获取文件直链（永久有效）
# 直接返回直链
source_link_str = conn.get_source_url(file_id)
# 返回直链和文件名组成的字典
source_link_dict = conn.get_source_url(file_id, url_only=False)
# 同时获取多个文件，由于Cloudreve API实现问题，此时url_only参数必须为False，返回无序列表
list_of_source_link_dicts = conn.get_source_url([file_id], url_only=False)

# 获取分享链接
# 普通分享文件
share_link_str1 = conn.get_share_url(file_id)
# 禁止预览，下载次数限制为10次，过期时间为一天，密码为123456
share_link_str2 = conn.get_share_url(file_id, preview=False, downloads=10, expire=86400, password='123456')
# 分享文件夹
share_link_str3 = conn.get_share_url('IdOfDir', is_dir=True)
```

## 示例（V4）

- 原则上，Cloudreve V4 使用以 `cloudreve://` 开头的 URI 来标识文件和目录，但你可以在使用本 SDK 时，直接使用以 `/` 开头的路径，程序会自动转换为 URI。
- Cloudreve V4 的 List 接口有分页选项，具体请参考 [List files - Cloudreve API Docs](https://cloudrevev4.apifox.cn/list-files-300233178e0)

```python
from cloudreve import CloudreveV4

# 初始化
conn = CloudreveV4('http://127.0.0.1:5212')

# 登录
conn.login('admin@cloudreve.org', '123456')

# 列目录
conn.list("/")

uri = '/hello.txt'

# 获取文件属性
data = conn.get_info(uri)
print(data)

# 删除文件
conn.delete(uri)

# 下载文件到本地
conn.download(url, './hello_world.txt')

# 创建目录
conn.create_folder('/python')

# 复制文件
conn.copy('/hello.txt', '/python')

# 重命名文件
conn.rename(uri, 'world.txt')

# 移动文件
conn.move('/world.py', '/python')

# 上传文件
conn.upload('D:/my_file.py', '/my_file_backup.py')

# 创建文件
conn.create_file('/new_file.txt')

# 更新文件
conn.update_file_content('/new_file.txt', 'This is the content of the new file.')

# 获取文件直链（永久有效）
# 简单获取（返回字符串）
source_link_str = conn.get_source_url(uri)
# 获取多个文件（返回由字典组成的列表）
list_of_source_link_dict = conn.get_source_url([uri1, uri2])

# 获取分享链接
# 普通分享文件
share_link_str1 = conn.get_share_url(uri)
# 下载次数限制为10次，过期时间为一天，密码为123456
share_link_str2 = conn.get_share_url(uri, downloads=10, expire=86400, password='123456')
```

## 联系我们

- Email：i@yxzl.dev
- TG 群：https://t.me/+XW2ok10N8DExMDU1

## 感谢

- [@TeoZler](https://github.com/TeoZler) 协助测试 Cloudreve V4 OneDrive 上传
- [@PTPAAA](https://github.com/PTPAAA) 提供 Cloudreve V4 [从机模式上传代码](https://github.com/PTPAAA/cloudreve-sdk/commit/130b5e9f5777a439fd82a4755bfff7a5968bf57f)
