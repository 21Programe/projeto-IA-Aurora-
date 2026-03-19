import llama_cpp
import os

print(f"--- Diagnóstico de Hardware Aurora ---")
print(f"Suporte a GPU (CUDA): {llama_cpp.llama_supports_gpu_offload()}")
print(f"Caminho do CUDA no Sistema: {os.environ.get('CUDA_PATH', 'Não encontrado')}")
