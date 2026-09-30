import pandas as pd
import numpy as np
import requests
import os
import yfinance as yf

# Credenciais oficiais do Telegram
TELEGRAM_TOKEN = '8643990886:AAFpiqleSSN7-jT0HaxpfaIY102HWvSwQ3g'
CHAT_ID = '1657742186'

# Lista completa de Criptos (via Binance)
PARES_CRIPTOS = {
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
    "SOL/USDT": "SOLUSDT",
    "XRP/USDT": "XRPUSDT",
    "BNB/USDT": "BNBUSDT"
}

# Lista completa de Forex (via Yahoo Finance)
PARES_MOEDAS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "EUR/JPY": "EURJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/JPY": "USDJPY=X",
    "GBP/JPY": "GBPJPY=X"
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

def buscar_dados_binance(symbol):
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

    # Analisando a última vela fechada (-1) para projetar a entrada na próxima vela de M1
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

    # Zonas de Suporte e Resistência baseadas nos últimos candles
    resistencia_recente = df['high'].iloc[-20:-1].max()
    suporte_recente = df['low'].iloc[-20:-1].min()

    toque_suporte = l <= suporte_recente + 0.0001
    toque_resistencia = h >= resistencia_recente - 0.0001
    
    rejeicao_alta = pavio_inferior >= (corpo * 1.5)
    rejeicao_baixa = pavio_superior >= (corpo * 1.5)

    # Gatilho de Pullback / Rejeição em Suporte (CALL para a próxima vela)
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

    # Gatilho de Pullback / Rejeição em Resistência (PUT para a próxima vela)
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
    # Varrendo Criptos em M1
    for nome_ativo, ticker in PARES_CRIPTOS.items():
        df = buscar_dados_binance(ticker)
        if df is not None:
            identificar_suporte_resistencia_e_pullback(df, nome_ativo)

    # Varrendo Forex em M1
    for nome_ativo, ticker in PARES_MOEDAS.items():
        try:
            import sys
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            dados = yf.download(ticker, interval="1m", period="1d", progress=False)
            sys.stdout.close()
            sys.stdout = old_stdout
            
            if not dados.empty:
                df = pd.DataFrame()
                df['close'] = dados['Close'].squeeze()
                df['open'] = dados['Open'].squeeze()
                df['high'] = dados['High'].squeeze()
                df['low'] = dados['Low'].squeeze()
                identificar_suporte_resistencia_e_pullback(df, nome_ativo)
        except Exception:
            pass
