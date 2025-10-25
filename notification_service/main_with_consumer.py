#!/usr/bin/env python3
"""
Notification Service - Com Event Bus Consumer
Plataforma VOD
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis.asyncio as redis

from config.settings import settings
from events.consumer import event_consumer

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Variável global para Redis
redis_client = None
consumer_task = None


async def connect_redis():
    """
    Conecta ao Redis
    """
    global redis_client
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Conectado ao Redis")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Redis: {e}")
        return False


async def start_event_consumer():
    """
    Inicia o Event Bus Consumer em background
    """
    global consumer_task
    try:
        logger.info("🚀 Iniciando Event Bus Consumer...")
        consumer_task = asyncio.create_task(event_consumer.start_consuming())
        logger.info("✅ Event Bus Consumer iniciado")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Event Bus Consumer: {e}")


async def stop_event_consumer():
    """
    Para o Event Bus Consumer
    """
    global consumer_task
    try:
        if consumer_task:
            await event_consumer.stop_consuming()
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Event Bus Consumer parado")
    except Exception as e:
        logger.error(f"❌ Erro ao parar Event Bus Consumer: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    """
    # Startup
    logger.info("🚀 Iniciando Notification Service...")
    
    # Conectar ao Redis
    redis_connected = await connect_redis()
    if not redis_connected:
        logger.warning("⚠️ Redis não conectado - algumas funcionalidades podem não funcionar")
    
    # Iniciar Event Bus Consumer
    await start_event_consumer()
    
    logger.info("✅ Notification Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Encerrando Notification Service...")
    
    # Parar Event Bus Consumer
    await stop_event_consumer()
    
    # Fechar conexão Redis
    global redis_client
    if redis_client:
        await redis_client.close()
    
    logger.info("👋 Notification Service encerrado")


# Criar aplicação FastAPI
app = FastAPI(
    title="VOD Notification Service",
    description="Serviço de Notificações da Plataforma VOD",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Endpoint raiz
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "message": "VOD Notification Service está funcionando!"
    }


@app.get("/health")
async def health_check():
    """
    Verifica a saúde do serviço
    """
    global redis_client
    
    # Verificar Redis
    redis_status = "disconnected"
    if redis_client:
        try:
            await redis_client.ping()
            redis_status = "connected"
        except:
            redis_status = "error"
    
    # Verificar Event Consumer
    consumer_health = await event_consumer.health_check()
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "event_consumer": consumer_health,
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/info")
async def service_info():
    """
    Informações do serviço
    """
    return {
        "service": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "redis": {
            "status": "connected" if redis_client else "disconnected",
            "host": settings.redis_host,
            "port": settings.redis_port,
            "db": settings.redis_db
        },
        "email": {
            "smtp_host": settings.email_smtp_host,
            "smtp_port": settings.email_smtp_port,
            "from_email": settings.email_from_email
        },
        "event_bus": {
            "enabled": settings.event_bus_enabled,
            "redis_host": settings.event_bus_redis_host,
            "redis_port": settings.event_bus_redis_port,
            "channel_prefix": settings.event_bus_channel_prefix
        }
    }


@app.get("/consumer/status")
async def consumer_status():
    """
    Status do Event Bus Consumer
    """
    return await event_consumer.health_check()


@app.post("/test/email")
async def test_email(email: str):
    """
    Testa envio de email
    """
    # TODO: Implementar teste de email
    return {
        "message": f"Teste de email para {email} (não implementado ainda)",
        "status": "pending"
    }


@app.post("/test/event")
async def test_event():
    """
    Testa publicação de evento
    """
    global redis_client
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis não conectado")
    
    try:
        import time
        test_event = {
            "type": "test",
            "message": "Evento de teste do Notification Service",
            "timestamp": time.time()
        }
        
        # Publica no canal de teste
        channel = "notifications.test"
        subscribers = await redis_client.publish(channel, str(test_event).replace("'", '"'))
        
        return {
            "message": "Evento de teste publicado",
            "channel": channel,
            "subscribers": subscribers,
            "event": test_event
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar evento: {str(e)}")


@app.post("/test/user-event")
async def test_user_event():
    """
    Testa evento de usuário
    """
    global redis_client
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis não conectado")
    
    try:
        import json
        import time
        
        # Simula evento de usuário registrado
        user_event = {
            "event_type": "user.registered",
            "event_id": "test_123",
            "user_id": 999,
            "timestamp": "2025-01-20T09:00:00Z",
            "source": "user_service",
            "data": {
                "email": "teste@exemplo.com",
                "full_name": "Usuário Teste",
                "language_preference": "pt-BR",
                "timezone": "America/Sao_Paulo"
            }
        }
        
        # Publica no canal de usuário
        channel = "notifications.user.registered"
        subscribers = await redis_client.publish(channel, json.dumps(user_event))
        
        return {
            "message": "Evento de usuário publicado",
            "channel": channel,
            "subscribers": subscribers,
            "event": user_event
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar evento: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main_with_consumer:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )