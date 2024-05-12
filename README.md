# Cloudreve SDK

本项目为 [Cloudreve](https://github.com/cloudreve/Cloudreve) 社区版的 Python SDK。

- 开源地址：https://github.com/yxzlwz/cloudreve-sdk
- PyPI：https://pypi.org/project/cloudreve/
- API文档：https://cloudreve.apifox.cn/

## 示例

```python
from cloudreve import Cloudreve

# 初始化
conn = Cloudreve('https://cloud.yixiangzhilv.com')

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
```

## 联系我们

- Email：yxzlwz@gmail.com
- TG 群：https://t.me/+XW2ok10N8DExMDU1
