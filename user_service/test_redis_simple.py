"""
Teste Simples de Conexão Redis
"""

import asyncio
import redis.asyncio as redis


async def test_redis_connection():
    """
    Testa conexão simples com Redis
    """
    print("🔄 Testando conexão com Redis...")
    
    try:
        # Conectar ao Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Testar ping
        response = await r.ping()
        print(f"✅ Redis respondeu: {response}")
        
        # Testar set/get
        await r.set('test_key', 'test_value')
        value = await r.get('test_key')
        print(f"✅ Teste set/get: {value.decode()}")
        
        # Limpar teste
        await r.delete('test_key')
        
        # Fechar conexão
        await r.close()
        
        print("✅ Conexão com Redis funcionando perfeitamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com Redis: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_redis_connection())
    exit(0 if success else 1)