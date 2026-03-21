import queue

# Esta é a "Caixa de Correios" central da Aurora.
# maxsize=0 significa que ela aguenta pacotes infinitos sem travar a memória.
fila_alertas = queue.Queue(maxsize=0)

print("[BARRAMENTO] Fila de eventos de segurança inicializada na RAM.")