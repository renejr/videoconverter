"""
Aplicação principal do User Service
Sistema de Identidade e Transações - Domínio A

Este é o ponto de entrada da aplicação FastAPI
para o serviço de gerenciamento de usuários.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from contextlib import asynccontextmanager

from config.settings import settings
from database.connection import engine, Base
from api.v1.router import api_router
from api.exceptions import register_exception_handlers

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    
    Args:
        app: Instância da aplicação FastAPI
    """
    # Startup
    logger.info("Iniciando User Service...")
    
    # Criar tabelas do banco de dados
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas do banco de dados criadas/verificadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas do banco de dados: {e}")
        raise
    
    logger.info("User Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    logger.info("Finalizando User Service...")


def create_application() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI
    
    Returns:
        FastAPI: Instância configurada da aplicação
    """
    # Criar aplicação FastAPI
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API para gerenciamento de usuários, autenticação e transações",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware de hosts confiáveis (apenas em produção)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )
    
    # Registrar handlers de exceção
    register_exception_handlers(app)
    
    # Incluir routers da API
    app.include_router(api_router, prefix="/api")
    
    # Endpoint raiz
    @app.get("/", tags=["root"])
    async def root():
        """
        Endpoint raiz da aplicação
        
        Returns:
            dict: Informações básicas da API
        """
        return {
            "message": "User Service API",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "Documentação disponível apenas em desenvolvimento",
            "health": "/api/v1/health"
        }
    
    # Middleware para logging de requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        Middleware para logging de todas as requisições
        
        Args:
            request: Objeto Request
            call_next: Próximo middleware/endpoint
            
        Returns:
            Response: Resposta da requisição
        """
        start_time = time.time()
        
        # Log da requisição
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host} - "
            f"User-Agent: {request.headers.get('user-agent', 'Unknown')}"
        )
        
        # Processar requisição
        response = await call_next(request)
        
        # Log da resposta
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.4f}s"
        )
        
        return response
    
    return app


# Criar instância da aplicação
app = create_application()


if __name__ == "__main__":
    """
    Executa a aplicação diretamente
    """
    import time
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
        access_log=settings.debug
    )