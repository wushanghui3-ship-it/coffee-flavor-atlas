# Coffee Flavor Atlas（Vue 新版）

旧版单文件网页已归档到 `legacy/index.html`。新版使用 `frontend` 中的 Vue 源码；Python 后端只提供新版构建结果及数据库 API。原 SQLite 数据文件仍在 `data/coffee_atlas.db`，不会因切换版本被清空。

## 一键启动（Windows PowerShell）

在本目录运行：

```powershell
.\start.ps1
```

打开终端打印的地址，默认是 http://127.0.0.1:4183/ 。端口被占用时会使用下一个空闲端口，请以实际输出为准。脚本会构建 Vue 前端、启动 Python 后端，在同一个地址提供网页和数据库接口。使用期间保持终端开启，按 Ctrl+C 停止。如果执行策略阻止脚本，请运行 `powershell -ExecutionPolicy Bypass -File .\start.ps1`。

## 开发模式（热更新）

保持 `start.ps1` 在第一个终端运行，再打开第二个终端：

```powershell
cd frontend
npm run dev
```

打开 http://127.0.0.1:5183/ 。开发服务会将 `/api` 转发到 `4183`；如果 `5183` 已被占用，会明确报错，不会自动跳到别的端口。

旧服务 `4173` 若仍在运行，请到它原来的终端按 Ctrl+C 停止。旧版归档文件只有手动打开 `legacy/index.html` 才会显示。

## 样本图片

管理员登录后，在“个人账户 → 研究员后台 → 维护样本”中为新建或已有样本添加、替换、移除图片。支持 JPG、PNG、WebP，单文件不超过 6 MB、2000 万像素；服务端验证后压缩为最长边 1600 像素的 WebP，不保存原始图片元数据。

图片文件存放在 `data/uploads/samples/`，SQLite 的 `coffee_sample.image_url` 保存对应地址。备份时需要同时备份数据库和上传目录。旧数据库会自动添加图片字段，不清空样本、账户或评论。没有图片的样本显示占位，不使用与样本无关的照片冒充。

后端新增 Pillow 依赖（Codex 自带 Python 已包含）。使用自己的 Python 时先运行 `python -m pip install -r requirements.txt`。

## 页面与验证

`#home` 为展示首页，风味关键词进入 `#discover` 选豆页；`#flavors` 中轮盘、候选样本和对比共用筛选状态。连续实线连接已记录的相邻风味；虚线跨过未录入的风味，不表示缺失位置有测量值。

前端测试：在 `frontend` 运行 `npm test`。图片接口测试：在项目目录运行 `python -m unittest discover -s tests -v`，使用临时数据库，不改动项目数据。

首页摄影资源来自 [Unsplash](https://images.unsplash.com/photo-1447933601403-0c6688de566e)，本地文件为 `frontend/public/images/coffee-hero.jpg`。

## Render 部署

项目根目录已提供 `render.yaml`，在 Render 创建 Blueprint 时选择本项目仓库即可自动读取构建、启动和健康检查配置。

部署前在 Render 环境变量中设置 `ADMIN_PASSWORD`。该变量会在服务启动时更新管理员账户 `admin` 的密码；不要继续使用本地默认密码。`HOST`、`COOKIE_SECURE` 已在 Blueprint 中配置，登录 Cookie 会在 HTTPS 下启用 `Secure`。

当前 Blueprint 使用免费 Web Service，SQLite 数据库和管理员上传的图片写在实例文件系统中。免费实例重启或重新部署后不保证保留这些写入数据，适合导师演示。需要长期保存评论、样本、图片时，应升级到带 Persistent Disk 的实例，并把 `COFFEE_ATLAS_DATA_DIR` 设置为磁盘挂载目录，或迁移到 PostgreSQL 与对象存储。
