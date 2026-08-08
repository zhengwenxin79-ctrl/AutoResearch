# AutoResearch Deployment

这份文档记录 AutoResearch 当前最小公网展示方案。目标不是先做复杂在线任务系统，而是先让师兄能通过公网 URL 看到已经生成的 Dashboard、MOC、Gap 证据链和研究机会。

## 推荐结构

```text
https://autoresearch.sugarclaw.top
        ↓
阿里云 ECS / Nginx
        ↓
127.0.0.1:8766
        ↓
/opt/AutoResearch/autoresearch_server.py
        ↓
outputs/<run-slug>/dashboard.html
```

如果后面接 Pro 6000，可以让 Pro 6000 负责跑 `autoresearch search`，然后把输出目录同步到 ECS 的 `/opt/AutoResearch/outputs/`。ECS 只负责展示和反向代理。

## 本地启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

AUTORESEARCH_PORT=8766 python autoresearch_server.py
```

打开：

```text
http://127.0.0.1:8766/
```

默认首页会跳到：

```text
/runs/gui-agent-benchmark-real-world-workflow/dashboard.html#mainline
```

如果这个输出目录不存在，就会显示 run 列表和缺失提示。

## 环境变量

- `HOST`：绑定地址。默认 `127.0.0.1`，适合放在 Nginx 后面。
- `PORT` 或 `AUTORESEARCH_PORT`：服务端口。默认 `8766`。
- `AUTORESEARCH_OUTPUT_DIR`：输出目录。默认 `outputs`。
- `AUTORESEARCH_DEFAULT_RUN`：默认展示的 run。默认 `gui-agent-benchmark-real-world-workflow`。
- `APP_DIR`：服务器项目目录。部署脚本默认 `/opt/AutoResearch`。
- `BRANCH`：部署分支。默认 `main`。

## 服务器部署

在 ECS 上准备项目目录：

```bash
cd /opt
git clone https://github.com/zhengwenxin79-ctrl/AutoResearch.git AutoResearch
cd /opt/AutoResearch
```

启动或更新服务：

```bash
chmod +x deploy.sh
AUTORESEARCH_PORT=8766 ./deploy.sh
```

服务默认只监听本机：

```text
http://127.0.0.1:8766
```

## 生成或同步 Dashboard 输出

`outputs/` 不提交到 Git，所以服务器上需要有实际 run 输出。两种方式二选一。

### 方式 A：服务器自己跑一次

适合轻量 demo：

```bash
cd /opt/AutoResearch
source .venv/bin/activate

autoresearch search "GUI agent benchmark real-world workflow" \
  --profile gui-agent \
  --limit 12 \
  --per-query-limit 3 \
  --full-text-limit 0
```

然后重启展示服务：

```bash
./deploy.sh
```

### 方式 B：从本地同步已有输出

适合本地或 Pro 6000 已经跑好结果后展示：

```bash
rsync -av \
  outputs/gui-agent-benchmark-real-world-workflow/ \
  USER@39.103.75.192:/opt/AutoResearch/outputs/gui-agent-benchmark-real-world-workflow/
```

把 `USER` 换成服务器用户名。

## Nginx 反向代理

如果使用子域名：

```nginx
server {
    listen 80;
    server_name autoresearch.sugarclaw.top;

    location / {
        proxy_pass http://127.0.0.1:8766;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

如果已有 HTTPS 证书，可以把同样的 `location /` 放到 443 server block 里。没有证书时可以之后用 `certbot` 申请。

## 需要你提供的信息

真正部署到 ECS 时，我需要：

- SSH 用户名和端口，例如 `root@39.103.75.192` 或 `ubuntu@39.103.75.192`
- 本机能用的 SSH key 路径，或者确认你这里可以直接 `ssh USER@39.103.75.192`
- `autoresearch.sugarclaw.top` 的 DNS 是否已经 A 记录到 `39.103.75.192`
- ECS 安全组是否开放 `80` 和 `443`
- 是否已经完成备案；如果没有，国内服务器用域名访问可能会受影响

## 当前边界

- 现在的 Web Server 是只读展示服务。
- 它不会在线触发 `autoresearch search`。
- 它适合给师兄看 Dashboard，不适合作为多人任务队列。
- 后续如果要在线输入研究方向并跑任务，可以在这个服务上继续加小型 job 系统。
