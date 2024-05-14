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

- 本项目上传功能目前只适配了 **本机存储** 和 **OneDrive存储** ，有别的需求可以提PR。

## 示例

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
```

## 联系我们

- Email：yxzlwz@gmail.com
- TG 群：https://t.me/+XW2ok10N8DExMDU1
