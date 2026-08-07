import yfinance as yf
import pandas as pd
import numpy as np

# ===============================
# ATIVOS
# ===============================

ativos = [
    "ABEV3.SA",
    "AXIA3.SA",
    "B3SA3.SA",
    "BBAS3.SA",
    "BBDC3.SA",
    "BPAC11.SA",
    "CMIG4.SA",
    "CSMG3.SA",
    "EMBJ3.SA",
    "EQTL3.SA",
    "ITUB4.SA",
    "ITSA4.SA",
    "PRIO3.SA",
    "SBSP3.SA",
    "SAPR11.SA",
    "VBBR3.SA"
]

# ===============================
# RSI
# ===============================

def calcular_rsi(precos):
    delta = precos.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    media_ganho = ganho.rolling(14).mean()
    media_perda = perda.rolling(14).mean()
    rs = media_ganho / media_perda
    rsi = 100 - (100/(1+rs))
    return float(rsi.iloc[-1])

# ===============================
# MOVIMENTO (Quedas Consecutivas)
# ===============================

def movimentos(precos):
    alta_atual = 0
    queda_atual = 0

    for i in range(len(precos) - 1, 0, -1):
        if precos.iloc[i] > precos.iloc[i-1]:
            if queda_atual > 0:
                break
            alta_atual += 1
        elif precos.iloc[i] < precos.iloc[i-1]:
            if alta_atual > 0:
                break
            queda_atual += 1
        else:
            break

    return alta_atual, queda_atual

# ===============================
# SCANNER
# ===============================

def rodar_scanner():
    resultado = []

    for ativo in ativos:
        try:
            dados = yf.download(ativo, period="2y", progress=False)
            
            if dados.empty:
                continue

            precos = dados["Close"]
            
            if isinstance(precos, pd.DataFrame):
                precos = precos.iloc[:,0]

            preco = float(precos.iloc[-1])
            rsi = calcular_rsi(precos)
            altas_seq, quedas_seq = movimentos(precos)
            mm200 = float(precos.rolling(200).mean().iloc[-1])
            
            tendencia = "ALTA" if preco > mm200 else "BAIXA"
            
            suporte = float(precos.tail(120).quantile(.15))
            resistencia = float(precos.tail(120).quantile(.85))

            # Cálculo das Variações % até Suporte e Resistência
            dist_suporte_pct = round(((preco - suporte) / suporte) * 100, 2)
            dist_resistencia_pct = round(((resistencia - preco) / preco) * 100, 2)

            variacoes_pct = (precos.pct_change().dropna().tail(5) * 100).iloc[::-1]
            ultimas_5_var = [round(float(v), 2) for v in variacoes_pct]

            score = 0
            
            if tendencia == "ALTA":
                score += 35
            if rsi < 45:
                score += 25
            if quedas_seq >= 3:
                score += 25
            if preco > suporte:
                score += 15

            resultado.append({
                "Ativo": ativo,
                "Preço": round(preco, 2),
                "RSI": round(rsi, 2),
                "Tendência": tendencia,
                "AltasSeq": altas_seq,
                "QuedasSeq": quedas_seq,
                "Suporte": round(suporte, 2),
                "Resistência": round(resistencia, 2),
                "DistSuportePct": dist_suporte_pct,
                "DistResistenciaPct": dist_resistencia_pct,
                "UltimasVariacoes": ultimas_5_var,
                "Score": score
            })

        except Exception as e:
            print("Erro no ativo:", ativo, e)

    return sorted(resultado, key=lambda x: x["Score"], reverse=True)