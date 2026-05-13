# serv00 部署说明

这份文档适用于把当前源码仓库直接部署到 serv00 的 `Python` 网站，运行方式为 Passenger。

如果你想用半自动脚本部署，仓库里已经带了一个模板脚本：

```sh
sh scripts/deploy-serv00.sh
```

你可以直接修改脚本里的占位符，也可以在运行时通过环境变量传入参数。

## 1. 先准备 serv00 网站

在 serv00 面板里先确认这些条件：

1. 账号已经开启 `Binexec`
2. 新建的是 `Python` 类型网站
3. Python 版本优先选 `3.12`
4. 网站根目录指向：

```text
/usr/home/LOGIN/domains/DOMAIN/public_python
```

当前仓库已经自带 Passenger 入口文件：

- `passenger_wsgi.py`
- `wsgi.py`

## 2. 上传项目代码

把整个仓库上传到：

```text
/usr/home/LOGIN/domains/DOMAIN/public_python
```

如果 serv00 自动生成了默认首页，可以先删掉：

```sh
rm -f /usr/home/LOGIN/domains/DOMAIN/public_python/public/index.html
```

## 3. 创建虚拟环境

```sh
mkdir -p /usr/home/LOGIN/.virtualenvs
cd /usr/home/LOGIN/.virtualenvs
virtualenv chatgpt2api-312 -p /usr/local/bin/python3.12
source /usr/home/LOGIN/.virtualenvs/chatgpt2api-312/bin/activate
```

## 4. 安装依赖

先进入项目目录：

```sh
cd /usr/home/LOGIN/domains/DOMAIN/public_python
```

如果后面有编译型依赖报错，建议先加这些保守编译参数：

```sh
export CFLAGS="-I/usr/local/include"
export CXXFLAGS="-I/usr/local/include"
export CC=gcc
export CXX=g++
export MAX_CONCURRENCY=1
export CPUCOUNT=1
export MAKEFLAGS="-j1"
export CMAKE_BUILD_PARALLEL_LEVEL=1
```

然后安装：

```sh
pip install --upgrade pip setuptools wheel
pip install -r requirements-freebsd.txt
```

## 5. 生成运行配置

```sh
cp config.json.example config.json
```

至少要把 `config.json` 里的认证密钥改掉，例如：

```json
{
  "auth-key": "换成你自己的高强度随机密钥"
}
```

## 6. 配置环境变量

在 serv00 里，Passenger 读取的是 `~/.bash_profile`，不是 `~/.bashrc`。

示例：

```sh
cat >> ~/.bash_profile <<'EOF'
export CHATGPT2API_AUTH_KEY="换成你自己的高强度随机密钥"
export STORAGE_BACKEND="json"
EOF
```

如果你后面想改成数据库存储，也可以继续加，比如：

```sh
export STORAGE_BACKEND="sqlite"
export DATABASE_URL="sqlite:////usr/home/LOGIN/domains/DOMAIN/public_python/data/accounts.db"
```

写完后重新加载一次：

```sh
source ~/.bash_profile
```

## 7. 把网站 Python 解释器指向虚拟环境

在 serv00 面板里，把网站的 `Python binary` 设置成：

```text
/usr/home/LOGIN/.virtualenvs/chatgpt2api-312/bin/python
```

如果你是用命令行创建的网站，也要确保最终用的是这个虚拟环境里的 Python。

## 8. 重启 Passenger

```sh
devil www DOMAIN restart
```

也可以顺手把 Passenger 进程数先固定成 1：

```sh
devil www options DOMAIN processes 1
```

第一次部署建议先用 `1` 个进程，稳定后再考虑增加。

## 9. 检查日志和连通性

Passenger 主日志一般在：

```text
/usr/home/LOGIN/domains/DOMAIN/logs/error.log
```

常用检查命令：

```sh
tail -n 200 /usr/home/LOGIN/domains/DOMAIN/logs/error.log
```

```sh
curl -I https://DOMAIN/health
```

```sh
curl https://DOMAIN/version
```

## 10. 关于前端页面

这个仓库即使没有前端构建产物，也可以先把后端跑起来。

如果 `web_dist/` 不存在：

- `/health` 仍然可用
- `/version` 仍然可用
- `/v1/...` API 仍然可用
- `/` 会显示一个简化兜底页面，而不是完整前端界面

如果你想启用完整 Web UI，需要你另外构建前端，并把生成结果放到 `web_dist/`。

如果你还想让部分静态文件直接由 serv00 提供而不经过 Python，那么静态目录是：

```text
/usr/home/LOGIN/domains/DOMAIN/public_python/public
```

## 11. 建议的首次上线流程

第一次部署建议按这个顺序做：

1. 先用 `json` 存储
2. Passenger 进程数先设为 `1`
3. 先确认 `https://DOMAIN/health` 返回正常
4. 再确认 `https://DOMAIN/version` 能拿到版本号
5. 最后再用你的 Bearer Token 测试 `GET /v1/models`

## 12. 常见问题

如果 `pip install` 失败，尤其是编译失败：

- 保持 `MAX_CONCURRENCY=1` 和 `MAKEFLAGS=-j1`
- 确保是在虚拟环境里安装
- 重启后查看 `logs/error.log`

如果网站返回 `502`：

- 确认网站类型是 `Python`，不是 `Proxy`
- 确认 `Python binary` 指向的是虚拟环境 Python
- 确认 `passenger_wsgi.py` 的确在 `public_python` 根目录
- 查看 `logs/error.log`

如果应用已经启动，但首页看起来很简单：

- 这通常说明 Passenger 已经工作了
- 缺的是前端静态构建产物
- API 一般仍然能正常使用

## 13. 部署脚本

仓库自带脚本：

```text
scripts/deploy-serv00.sh
```

你可以这样运行：

```sh
cd /usr/home/LOGIN/domains/DOMAIN/public_python
LOGIN=LOGIN DOMAIN=DOMAIN AUTH_KEY='你的密钥' sh scripts/deploy-serv00.sh
```

这个脚本会自动完成这些事：

- 创建或复用虚拟环境
- 安装 `requirements-freebsd.txt`
- 如果没有 `config.json`，就从 `config.json.example` 自动生成
- 在 `~/.bash_profile` 里写入受控的 `chatgpt2api serv00` 环境变量块
- 重启 Passenger 网站
