import requests
import pandas as pd
import numpy as np
import yfinance as yf
import sys
import os
from datetime import datetime, time, timezone, timedelta

# Configurações do Telegram
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
    "GBP/JPY": "GBPJPY=X",
    "USD/CAD": "USDCAD=X",
    "USD/CHF": "USDCHF=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X"
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
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

def calcular_poc_e_fibonacci(df):
    if df is None or df.empty or len(df) < 20:
        return None, None, None, None

    # Baseado nas últimas 20 velas
    swing_high = df['high'].iloc[-20:].max()
    swing_low = df['low'].iloc[-20:].min()
    
    diff = swing_high - swing_low
    fib_618 = swing_high - (diff * 0.618)
    fib_500 = swing_high - (diff * 0.500)
    fib_382 = swing_high - (diff * 0.382)

    if 'volume' in df.columns:
        idx_max_vol = df['volume'].iloc[-20:].idxmax()
        poc_price = df['close'].loc[idx_max_vol]
    else:
        poc_price = df['close'].iloc[-20:].median()

    return poc_price, fib_618, fib_500, fib_382

def analisar_fibonacci_poc(df, nome_ativo):
    poc, fib_618, fib_500, fib_382 = calcular_poc_e_fibonacci(df)
    if poc is None:
        return

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
    rejeicao_alta = pavio_inferior >= (corpo * 1.5)
    rejeicao_baixa = pavio_superior >= (corpo * 1.5)

    tol = 0.0015

    # Confluência de Suporte (CALL)
    toque_fib_suporte = (abs(l - fib_618) <= tol) or (abs(l - fib_500) <= tol)
    perto_poc = abs(l - poc) <= tol

    if toque_fib_suporte and perto_poc and rejeicao_alta and c > o:
        sinal = (
            "🎯 *SINAL M1 - FIBO + POC (20 VELAS) [CALL]* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🟢 *CALL (COMPRA)*\n\n"
            "🕯️ *Confluência Identificada (Últimas 20 Velas):*\n"
            "• Retração em Zona de Fibonacci (50% / 61.8%)\n"
            "• Confluência com a POC de Volume Recente\n"
            "• Rejeição Forte Detectada (Pavio Inferior)\n\n"
            "⚡ *Ação:* Abra a ordem de COMPRA para a próxima vela de M1!"
        )
        enviar_telegram(sinal)

    # Confluência de Resistência (PUT)
    toque_fib_resistencia = (abs(h - fib_382) <= tol) or (abs(h - fib_500) <= tol)
    perto_poc_res = abs(h - poc) <= tol

    if toque_fib_resistencia and perto_poc_res and rejeicao_baixa and c < o:
        sinal = (
            "🎯 *SINAL M1 - FIBO + POC (20 VELAS) [PUT]* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🔴 *PUT (VENDA)*\n\n"
            "🕯️ *Confluência Identificada (Últimas 20 Velas):*\n"
            "• Retração em Zona de Fibonacci\n"
            "• Confluência com a POC de Volume Recente\n"
            "• Rejeição Forte Detectada (Pavio Superior)\n\n"
            "⚡ *Ação:* Abra a ordem de VENDA para a próxima vela de M1!"
        )
        enviar_telegram(sinal)

if __name__ == "__main__":
    # Ajuste de Fuso Horário (Brasil - Brasília: UTC-3) ou horário do servidor GitHub (UTC)
    # Como o GitHub roda em UTC, ajustamos para o horário do Brasil (UTC-3)
    fuso_brasil = timezone(timedelta(hours=-3))
    agora_brasil = datetime.now(fuso_brasil).time()

    hora_inicio = time(8, 0)   # 08:00
    hora_fim = time(22, 0)     # 22:00

    # Verifica se está dentro do horário permitido
    if not (hora_inicio <= agora_brasil <= hora_fim):
        print(f"Fora do horário de operação ({agora_brasil}). Robô em pausa.")
        sys.exit(0)

    # Analisa Criptos
    for nome_ativo, ticker in PARES_CRIPTOS.items():
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={ticker}&interval=1m&limit=50"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if isinstance(data, list):
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['volume'] = df['volume'].astype(float)
                analisar_fibonacci_poc(df, nome_ativo)
        except Exception:
            pass

    # Analisa Forex
    for nome_ativo, ticker in PARES_MOEDAS.items():
        try:
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            dados = yf.download(ticker, interval="1m", period="1d", progress=False)
            sys.stdout.close()
            sys.stdout = os.sys.__stdout__
            if not dados.empty:
                df = pd.DataFrame()
                df['close'] = dados['Close'].squeeze()
                df['open'] = dados['Open'].squeeze()
                df['high'] = dados['High'].squeeze()
                df['low'] = dados['Low'].squeeze()
                analisar_fibonacci_poc(df, nome_ativo)
        except Exception:
            pass
