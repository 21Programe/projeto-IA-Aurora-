import cv2
import pytesseract
import pyautogui
import numpy as np
import time
import threading
import tkinter as tk
import re
import unicodedata
from pytesseract import Output
from queue import Empty
from seguranca.barramento_eventos import fila_alertas

# =========================================================
# CONFIGURAÇÃO
# =========================================================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PALAVRAS_PERIGOSAS = {
    "encrypted",
    "bitcoin",
    "decrypt",
    "pague",
    "resgate",
    "urgente",
    "recadastramento",
    "vencido",
}

FRASES_PERIGOSAS = {
    "senha expirada",
    "arquivo criptografado",
    "seus arquivos foram criptografados",
    "pagamento em bitcoin",
    "clique aqui para atualizar",
    "acao necessaria imediata",
    "sua conta foi bloqueada",
}

IDIOMAS_OCR = "por+eng"
OCR_CONFIG = "--oem 3 --psm 6"
OCR_CONFIANCA_MIN = 45

INTERVALO_CAPTURA = 3
COOLDOWN_ALERTA = 20
MAX_RADARES_ATIVOS = 3

# Opcional: limitar região da tela para ganhar desempenho
# Exemplo: REGIAO_CAPTURA = (0, 0, 1600, 900)
REGIAO_CAPTURA = None

# Controle interno
ultimo_alerta = {}
radar_lock = threading.Lock()
radares_ativos = 0


# =========================================================
# UTILITÁRIOS
# =========================================================
def normalizar_texto(txt: str) -> str:
    txt = txt.lower().strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    txt = re.sub(r"\s+", " ", txt)
    txt = re.sub(r"[^\w\s\-.:/]", "", txt)
    return txt


def agora_epoch() -> float:
    return time.time()


def em_cooldown(chave: str) -> bool:
    ts = ultimo_alerta.get(chave)
    if ts is None:
        return False
    return (agora_epoch() - ts) < COOLDOWN_ALERTA


def registrar_alerta(chave: str):
    ultimo_alerta[chave] = agora_epoch()


def expandir_caixa(x, y, w, h, margem=12):
    return max(0, x - margem), max(0, y - margem), w + margem * 2, h + margem * 2


def intersecao(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    x1 = max(ax, bx)
    y1 = max(ay, by)
    x2 = min(ax + aw, bx + bw)
    y2 = min(ay + ah, by + bh)

    if x2 <= x1 or y2 <= y1:
        return 0
    return (x2 - x1) * (y2 - y1)


def unir_caixas(caixas):
    if not caixas:
        return None

    x1 = min(c[0] for c in caixas)
    y1 = min(c[1] for c in caixas)
    x2 = max(c[0] + c[2] for c in caixas)
    y2 = max(c[1] + c[3] for c in caixas)
    return (x1, y1, x2 - x1, y2 - y1)


# =========================================================
# OVERLAY VISUAL
# =========================================================
def desenhar_radar_na_tela(x, y, w, h, texto_alerta="ALERTA"):
    def _desenhar():
        global radares_ativos

        with radar_lock:
            if radares_ativos >= MAX_RADARES_ATIVOS:
                return
            radares_ativos += 1

        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-transparentcolor", "white")

            x2, y2, w2, h2 = expandir_caixa(x, y, w, h, margem=10)
            root.geometry(f"{w2}x{h2}+{x2}+{y2}")

            canvas = tk.Canvas(root, width=w2, height=h2, bg="white", highlightthickness=0)
            canvas.pack()

            # Moldura
            canvas.create_rectangle(2, 2, w2 - 2, h2 - 2, outline="red", width=4)

            # Etiqueta
            canvas.create_rectangle(4, 4, min(210, w2 - 4), 28, fill="red", outline="red")
            canvas.create_text(10, 16, anchor="w", text=texto_alerta[:28], fill="white", font=("Arial", 10, "bold"))

            root.after(3500, root.destroy)
            root.mainloop()
        finally:
            with radar_lock:
                radares_ativos -= 1

    threading.Thread(target=_desenhar, daemon=True).start()


# =========================================================
# PRÉ-PROCESSAMENTO
# =========================================================
def preprocessar_imagem(frame_bgr: np.ndarray) -> np.ndarray:
    """
    Melhora contraste para OCR:
    - grayscale
    - redução de ruído
    - threshold adaptativo
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # realce local
    gray = cv2.equalizeHist(gray)

    binarizada = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )
    return binarizada


# =========================================================
# OCR + ANÁLISE
# =========================================================
def extrair_dados_ocr(imagem_processada: np.ndarray):
    dados = pytesseract.image_to_data(
        imagem_processada,
        lang=IDIOMAS_OCR,
        config=OCR_CONFIG,
        output_type=Output.DICT
    )
    return dados


def montar_tokens(dados, offset_x=0, offset_y=0):
    tokens = []
    n = len(dados["text"])

    for i in range(n):
        bruto = str(dados["text"][i] or "").strip()
        if not bruto:
            continue

        try:
            conf = float(dados["conf"][i])
        except Exception:
            conf = -1

        if conf < OCR_CONFIANCA_MIN:
            continue

        txt = normalizar_texto(bruto)
        if not txt:
            continue

        x = int(dados["left"][i]) + offset_x
        y = int(dados["top"][i]) + offset_y
        w = int(dados["width"][i])
        h = int(dados["height"][i])

        tokens.append({
            "text": txt,
            "raw": bruto,
            "conf": conf,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "line_num": dados.get("line_num", [0] * n)[i],
            "block_num": dados.get("block_num", [0] * n)[i],
            "par_num": dados.get("par_num", [0] * n)[i],
        })

    return tokens


def detectar_palavras_perigosas(tokens):
    achados = []

    for tk_ in tokens:
        for perigo in PALAVRAS_PERIGOSAS:
            if perigo in tk_["text"]:
                achados.append({
                    "tipo": "palavra",
                    "termo": perigo,
                    "texto": tk_["raw"],
                    "caixa": (tk_["x"], tk_["y"], tk_["w"], tk_["h"]),
                    "conf": tk_["conf"],
                })

    return achados


def detectar_frases_perigosas(tokens):
    """
    Agrupa por bloco/parágrafo/linha e tenta detectar frases.
    """
    grupos = {}

    for tk_ in tokens:
        chave = (tk_["block_num"], tk_["par_num"], tk_["line_num"])
        grupos.setdefault(chave, []).append(tk_)

    achados = []

    for _, grupo in grupos.items():
        grupo = sorted(grupo, key=lambda t: (t["y"], t["x"]))
        linha_texto = normalizar_texto(" ".join(t["text"] for t in grupo))

        for frase in FRASES_PERIGOSAS:
            if frase in linha_texto:
                caixa = unir_caixas([(t["x"], t["y"], t["w"], t["h"]) for t in grupo])
                conf_media = sum(t["conf"] for t in grupo) / max(1, len(grupo))

                achados.append({
                    "tipo": "frase",
                    "termo": frase,
                    "texto": linha_texto,
                    "caixa": caixa,
                    "conf": conf_media,
                })

    return achados


def escolher_melhor_achado(achados):
    if not achados:
        return None

    prioridade_tipo = {"frase": 2, "palavra": 1}
    return sorted(
        achados,
        key=lambda a: (prioridade_tipo.get(a["tipo"], 0), a["conf"]),
        reverse=True
    )[0]


# =========================================================
# ALERTA
# =========================================================
def emitir_alerta_visual(achado):
    termo = achado["termo"]
    caixa = achado["caixa"]
    x, y, w, h = caixa

    chave = f"{achado['tipo']}::{termo}::{x//80}:{y//80}"
    if em_cooldown(chave):
        return False

    registrar_alerta(chave)

    desenhar_radar_na_tela(x, y, w, h, texto_alerta=f"RISCO: {termo}")

    alerta = {
        "tipo": "ALERTA_VISAO",
        "nivel": "ALTO" if achado["tipo"] == "frase" else "MÉDIO",
        "processo": "Monitor_de_Tela",
        "pid": 0,
        "porta_suspeita": "N/A",
        "estado": "VISUAL",
        "usuario": os_usuario(),
        "executavel": "Interface_Visual",
        "mensagem": (
            f"Alerta visual: {achado['tipo']} suspeita detectada "
            f"('{termo}') com confiança {achado['conf']:.1f}."
        ),
        "coordenadas": {"x": x, "y": y, "w": w, "h": h},
        "texto_detectado": achado["texto"],
        "termo": termo,
        "confianca": round(float(achado["conf"]), 2),
    }

    fila_alertas.put(alerta)
    print(f"[VISÃO] 🎯 Detectado: {termo} em X:{x} Y:{y} conf:{achado['conf']:.1f}")
    return True


def os_usuario():
    import os
    return os.path.basename(os.path.expanduser("~"))


# =========================================================
# CAPTURA
# =========================================================
def capturar_tela():
    """
    PyAutoGUI retorna imagem PIL; convertemos para numpy/OpenCV. :contentReference[oaicite:1]{index=1}
    """
    if REGIAO_CAPTURA:
        left, top, width, height = REGIAO_CAPTURA
        img = pyautogui.screenshot(region=(left, top, width, height))
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame, left, top

    img = pyautogui.screenshot()
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame, 0, 0


# =========================================================
# LOOP PRINCIPAL
# =========================================================
def rotina_visao_protetora():
    print("[VISÃO] Olhos de Águia defensivos ativados.")

    while True:
        try:
            frame_bgr, offset_x, offset_y = capturar_tela()
            processada = preprocessar_imagem(frame_bgr)
            dados = extrair_dados_ocr(processada)
            tokens = montar_tokens(dados, offset_x=offset_x, offset_y=offset_y)

            if not tokens:
                time.sleep(INTERVALO_CAPTURA)
                continue

            achados = []
            achados.extend(detectar_palavras_perigosas(tokens))
            achados.extend(detectar_frases_perigosas(tokens))

            melhor = escolher_melhor_achado(achados)
            if melhor:
                emitir_alerta_visual(melhor)

            time.sleep(INTERVALO_CAPTURA)

        except Exception as e:
            print(f"[VISÃO] Erro na análise de tela: {e}")
            time.sleep(5)


if __name__ == "__main__":
    rotina_visao_protetora()