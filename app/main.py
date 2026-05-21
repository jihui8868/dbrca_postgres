from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import rca_router

settings = get_settings()
# from app.core.database import close_db, init_db

# 项目根目录下的 static/(与 app/ 同级)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
# IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # lifespan 本身必须是 async(FastAPI 框架要求),内部调用同步函数即可
    # init_db()
    yield
    # close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        # 关闭内置 docs / redoc(它们默认从公网 CDN 拉资源),改用本地静态资源
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载本地静态目录(用于离线 swagger / redoc 资源)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    # app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

    # 离线 Swagger UI:/docs
    @app.get("/docs", include_in_schema=False)
    def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    # 离线 ReDoc:/redoc
    @app.get("/redoc", include_in_schema=False)
    def custom_redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )

    # 挂载RCA路由
    app.include_router(rca_router)

    return app


app = create_app()

@app.get("/")
def home():
    return "欢迎使用数据库智能诊断系统"

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=settings.PROJECT_NAME)
    parser.add_argument("--cli",     action="store_true", help="启动终端对话模式 (跳过 FastAPI)")
    parser.add_argument("--debug",   action="store_true", help="CLI 模式下显示详细事件")
    parser.add_argument("--session", default=None,        help="CLI 模式下指定 session_id")
    parser.add_argument("--input",   default=None, metavar="TEXT", help="CLI 单次非交互输入后退出")
    parser.add_argument("--host",    default="0.0.0.0",  help="FastAPI 监听地址 (默认 0.0.0.0)")
    parser.add_argument("--port",    default=7777, type=int, help="FastAPI 监听端口 (默认 7777)")
    args = parser.parse_args()

    if args.cli:
        import uuid
        from app.cli.agent_chat import repl, run_once

        session_id = args.session or uuid.uuid4().hex[:8]
        if args.input:
            run_once(session_id=session_id, debug=args.debug, user_input=args.input)
        else:
            repl(session_id=session_id, debug=args.debug)
    else:
        import uvicorn

        # 注意:不要使用 6000 / 6665~6669 等端口,Chrome / Firefox 把它们列为
        # unsafe port,浏览器会直接拒绝访问并返回 ERR_UNSAFE_PORT。
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
