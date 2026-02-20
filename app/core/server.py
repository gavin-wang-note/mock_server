from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import config

# 创建全局应用实例
app = FastAPI(
    title="Mock Server",
    description="企业级 Python Mock Server",
    version="V1.0.0"
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加根路径处理
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock Server</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }
            h1 {
                color: #333;
            }
            .links {
                margin-top: 30px;
            }
            .link-item {
                display: inline-block;
                margin: 10px;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                color: white;
                font-weight: bold;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .link-item:nth-child(1) {
                background-color: #4a90e2;
            }
            .link-item:nth-child(2) {
                background-color: #50e3c2;
            }
            .link-item:nth-child(3) {
                background-color: #9013fe;
            }
            .link-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <h1>Mock Server</h1>
        <p>企业级 Python Mock Server</p>
        <div class="links">
            <a href="/admin" class="link-item">管理界面</a>
            <a href="/health" class="link-item">健康检查</a>
            <a href="/docs" class="link-item">API文档</a>
        </div>
    </body>
    </html>
    """

# 添加favicon.ico路由
@app.get("/favicon.ico")
async def favicon():
    """返回favicon图标"""
    # 使用内置的favicon图标（从htmlcov目录复制一个）
    try:
        return FileResponse("htmlcov/favicon_32_cb_c827f16f.png")
    except:
        # 如果文件不存在，返回一个空的204响应
        from fastapi.responses import Response
        return Response(status_code=204)

# 注册路由
from app.api import mock, admin, health

# 注册健康检查路由
app.include_router(health.router, tags=["health"])

# 注册管理API路由
if config.admin.enable_api:
    app.include_router(admin.router, tags=["admin"])

# 注册Mock API路由（通配符路由放在最后）
app.include_router(mock.router, tags=["mock"])


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    return app


def run_server():
    """启动服务器"""
    import uvicorn
    
    # 配置服务器参数
    uvicorn_config = {
        "app": app,  # 直接使用创建的app实例
        "host": config.server.host,
        "port": config.server.port,
        "reload": False,
        "workers": 1
    }
    
    # 如果启用HTTPS
    if config.server.enable_https and config.server.https_cert and config.server.https_key:
        uvicorn_config["ssl_certfile"] = config.server.https_cert
        uvicorn_config["ssl_keyfile"] = config.server.https_key
    
    # 启动服务器
    uvicorn.run(**uvicorn_config)
