# Cloudreve SDK

本项目为 [Cloudreve](https://github.com/cloudreve/Cloudreve) 社区版的 Python SDK。

- 开源地址：https://github.com/yxzlwz/cloudreve-sdk
- PyPI：https://pypi.org/project/cloudreve/
- API文档：https://cloudreve.apifox.cn/

## 安装

```bash
pip3 install cloudreve
```

## 使用前说明

- 本项目上传功能目前只适配了**本机存储**和**OneDrive存储**，有别的需求可以提PR。
- 鉴于Cloudreve V3的诸多问题和已知V4不开源的消息，本人有意向重新维护一个多用户开源网盘项目，目前正在规划中，有意者欢迎通过页面底部联系方式与我交流！

## 示例

- 每个方法都写了详细注释，可以直接阅读源码了解
- 除少数特殊说明的接口外，几乎所有对文件的操作都需要使用由**字母和数字**组成的文件ID作为参数

```python
from cloudreve import Cloudreve

# 初始化
conn = Cloudreve('http://127.0.0.1:5212')

# 登录
conn.login('admin@cloudreve.org', '123456')

# 获取文件ID
file_id = conn.get_id('/hello.py')

# 获取文件属性
data = conn.get_property(file_id)
print(data)

# 获取临时下载URL
url = conn.get_download_url(file_id, 'hello_world.py', True)

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

## 联系我们

- Email：yxzlwz@gmail.com
- TG 群：https://t.me/+XW2ok10N8DExMDU1
