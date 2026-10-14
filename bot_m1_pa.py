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

def analisar_estrategia_reversao(df, nome_ativo):
    # Precisamos de pelo menos 5 velas para analisar o padrão na penúltima e a vela seguinte fechada
    if df is None or df.empty or len(df) < 5:
        return

    # Vela de Sinal (penúltima vela fechada: índice -2)
    idx_sinal = -2
    o_sinal = df['open'].iloc[idx_sinal]
    c_sinal = df['close'].iloc[idx_sinal]
    h_sinal = df['high'].iloc[idx_sinal]
    l_sinal = df['low'].iloc[idx_sinal]

    corpo_sinal = abs(c_sinal - o_sinal)
    tamanho_total_sinal = h_sinal - l_sinal
    if tamanho_total_sinal == 0:
        return

    pavio_inferior = min(o_sinal, c_sinal) - l_sinal
    pavio_superior = h_sinal - max(o_sinal, c_sinal)

    # Identifica os padrões na penúltima vela
    is_hammer = (pavio_inferior >= (corpo_sinal * 2)) and (pavio_superior <= corpo_sinal * 0.5) and (corpo_sinal > 0)
    is_shooting_star = (pavio_superior >= (corpo_sinal * 2)) and (pavio_inferior <= corpo_sinal * 0.5) and (corpo_sinal > 0)

    if not is_hammer and not is_shooting_star:
        return

    # Vela de Confirmação/Espera (última vela fechada: índice -1)
    idx_conf = -1
    o_conf = df['open'].iloc[idx_conf]
    c_conf = df['close'].iloc[idx_conf]

    vela_vermelha = c_conf < o_conf
    vela_verde = c_conf > o_conf

    # Se apareceu Hammer e a vela seguinte foi vermelha -> Entrar comprado (CALL)
    if is_hammer and vela_vermelha:
        sinal = (
            "🎯 *SINAL M1 - HAMMER + CONFIRMAÇÃO (CALL)* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🟢 *CALL (COMPRA)*\n\n"
            "🕯️ *Lógica Aplicada:*\n"
            "• Padrão Hammer Identificado\n"
            "• Vela de Confirmação Fechou Vermelha\n"
            "• Entrada Oposta (Reversão)\n"
            "🔄 *Gerenciamento:* Entrada Principal + Até 2 Gales\n\n"
            "⚡ *Ação:* Abra a ordem de COMPRA para a próxima vela!"
        )
        enviar_telegram(sinal)

    # Se apareceu Shooting Star e a vela seguinte foi verde -> Entrar vendido (PUT)
    elif is_shooting_star and vela_verde:
        sinal = (
            "🎯 *SINAL M1 - SHOOTING STAR + CONFIRMAÇÃO (PUT)* 🎯\n\n"
            f"📊 *Ativo:* {nome_ativo}\n"
            "⏰ *Tempo Gráfico:* M1 (Expiração 1 Minuto)\n"
            "📈 *Direção:* 🔴 *PUT (VENDA)*\n\n"
            "🕯️ *Lógica Aplicada:*\n"
            "• Padrão Shooting Star Identificado\n"
            "• Vela de Confirmação Fechou Verde\n"
            "• Entrada Oposta (Reversão)\n"
            "🔄 *Gerenciamento:* Entrada Principal + Até 2 Gales\n\n"
            "⚡ *Ação:* Abra a ordem de VENDA para a próxima vela!"
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
                analisar_estrategia_reversao(df, nome_ativo)
        except Exception as e:
            print(f"Erro ao analisar {nome_ativo}: {e}")
