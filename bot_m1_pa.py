import requests
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, time, timezone, timedelta

# Configurações do Telegram
TELEGRAM_TOKEN = '8643990886:AAFpiqleSSN7-jT0HaxpfaIY102HWvSwQ3g'
CHAT_ID = '1657742186'

# Apenas os 5 ativos solicitados
PARES_CRIPTOS = {
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
    "SOL/USDT": "SOLUSDT",
    "XRP/USDT": "XRPUSDT",
    "ADA/USDT": "ADAUSDT"
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

def analisar_hammer_shooting_star(df, nome_ativo):
    if df is None or df.empty or len(df) < 5:
        return

    # Analisa a última vela fechada (índice -1)
    idx = -1
    o = df['open'].iloc[idx]
    c = df['close'].iloc[idx]
    h = df['high'].iloc[idx]
    l = df['low'].iloc[idx]

    corpo = abs(c - o)
    tamanho_total = h - l
    if tamanho_total == 0:
        return

    pavio_inferior = min(o, c) - l
    pavio_superior = h - max(o, c)

    # Regra do Hammer (Martelo): pavio inferior pelo menos 2x o corpo, pequeno pavio superior
    is_hammer = (pavio_inferior >= (corpo * 2)) and (pavio_superior <= corpo * 0.5) and (corpo > 0)

    # Regra da Shooting Star (Estrela Cadente): pavio superior pelo menos 2x o corpo, pequeno pavio inferior
    is_shooting_star = (pavio_superior >= (corpo * 2)) and (pavio_inferior <= corpo * 0.5) and (corpo > 0)

    if is_hammer:
        sinal = (
            "🎯 *SINAL M1 - HAMMER (CALL)* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🟢 *CALL (COMPRA)*\n\n"
            "🕯️ *Padrão Identificado:* Martelo de Alta (Hammer)\n"
            "🔄 *Gerenciamento:* Entrada Principal + Até 2 Gales (Gale 1 e Gale 2)\n\n"
            "⚡ *Ação:* Abra a ordem de COMPRA para a próxima vela de M1!"
        )
        enviar_telegram(sinal)

    elif is_shooting_star:
        sinal = (
            "🎯 *SINAL M1 - SHOOTING STAR (PUT)* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🔴 *PUT (VENDA)*\n\n"
            "🕯️ *Padrão Identificado:* Estrela Cadente de Baixa (Shooting Star)\n"
            "🔄 *Gerenciamento:* Entrada Principal + Até 2 Gales (Gale 1 e Gale 2)\n\n"
            "⚡ *Ação:* Abra a ordem de VENDA para a próxima vela de M1!"
        )
        enviar_telegram(sinal)

if __name__ == "__main__":
    # Filtro de Horário (08:00 às 22:00 Horário de Brasília / UTC-3)
    fuso_brasil = timezone(timedelta(hours=-3))
    agora_brasil = datetime.now(fuso_brasil).time()

    hora_inicio = time(8, 0)
    hora_fim = time(22, 0)

    if not (hora_inicio <= agora_brasil <= hora_fim):
        print(f"Fora do horário de operação ({agora_brasil}). Robô em pausa.")
        sys.exit(0)

    # Varredura dos 5 ativos na Binance
    for nome_ativo, ticker in PARES_CRIPTOS.items():
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={ticker}&interval=1m&limit=10"
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
                analisar_hammer_shooting_star(df, nome_ativo)
        except Exception as e:
            print(f"Erro ao analisar {nome_ativo}: {e}")
