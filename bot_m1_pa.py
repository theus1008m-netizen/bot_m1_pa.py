import pandas as pd
import numpy as np
import ta
import requests

# === SUAS NOVAS CREDENCIAIS DO SEGUNDO TELEGRAM ===
TELEGRAM_TOKEN = 'COLE_SEU_NOVO_TOKEN_AQUI'
CHAT_ID = 'COLE_SEU_CHAT_ID_AQUI'

# Pares focados para M1 (alta liquidez)
PARES_M1 = {
    "EUR/USD": "EURUSDT",
    "GBP/USD": "GBPUSDT",
    "AUD/USD": "AUDUSDT"
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def buscar_dados_m1(symbol):
    # Buscando velas de 1 minuto na Binance para alta velocidade
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=1m&limit=100"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not isinstance(data, list):
            return None
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except Exception:
        return None

def identificar_suporte_resistencia_e_pullback(df, nome_ativo):
    if df is None or df.empty or len(df) < 50:
        return

    # Analisando a última vela fechada (-1) para projetar a próxima (M1)
    idx = -1
    o = df['open'].iloc[idx]
    c = df['close'].iloc[idx]
    h = df['high'].iloc[idx]
    l = df['low'].iloc[idx]

    corpo = abs(c - o)
    tamanho_total = h - l
    if tamanho_total == 0:
        tamanho_total = 0.00001

    pavio_inferior = min(o, c) - l
    pavio_superior = h - max(o, c)

    # Topos e Fundos locais recentes (Simulando Zonas de Suporte e Resistência de Curto Prazo)
     resistencia_recente = df['high'].iloc[-20:-1].max()
     suporte_recente = df['low'].iloc[-20:-1].min()

    # Padrões de Price Action M1
    toque_suporte = l <= suporte_recente + 0.0001
    toque_resistencia = h >= resistencia_recente - 0.0001
    
    # Rejeição (Pavio forte respeitando a zona)
    rejeicao_alta = pavio_inferior >= (corpo * 1.5) # Pavio 1.5x maior que o corpo em suporte
    rejeicao_baixa = pavio_superior >= (corpo * 1.5) # Pavio 1.5x maior que o corpo em resistência

    # Gatilho de Pullback / Rejeição em Suporte (CALL)
    if toque_suporte and rejeicao_alta and c > o:
        sinal = (
            "🎯 *SINAL M1 - PRICE ACTION (CALL)* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🟢 *CALL (COMPRA)*\n\n"
            "🕯️ *Padrão Identificado:*\n"
            "• Toque em Zona de Suporte Recente\n"
            "• Rejeição Forte (Pavio Inferior)\n"
            "• Pullback Confirmado\n\n"
            "⚡ *Ação:* Abra a ordem de COMPRA para a próxima vela de M1!"
        )
        enviar_telegram(sinal)

    # Gatilho de Pullback / Rejeição em Resistência (PUT)
    if toque_resistencia and rejeicao_baixa and c < o:
        sinal = (
            "🎯 *SINAL M1 - PRICE ACTION (PUT)* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🔴 *PUT (VENDA)*\n\n"
            "🕯️ *Padrão Identificado:*\n"
            "• Toque em Zona de Resistência Recente\n"
            "• Rejeição Forte (Pavio Superior)\n"
            "• Pullback Confirmado\n\n"
            "⚡ *Ação:* Abra a ordem de VENDA para a próxima vela de M1!"
        )
        enviar_telegram(sinal)

if __name__ == "__main__":
    for nome_ativo, ticker in PARES_M1.items():
        df = buscar_dados_m1(ticker)
        if df is not None:
            identificar_suporte_resistencia_e_pullback(df, nome_ativo)
