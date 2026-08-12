import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)

ATIVOS = [
    "ABEV3", "B3SA3", "BBAS3", "BBDC3", 
    "CMIG4", "ITUB4", "ITSA4", "PRIO3", "SBSP3", "PETR4"
]

def inicializar_mt5():
    if not mt5.initialize():
        print("Falha ao inicializar o MetaTrader 5. Verifique se ele está aberto.")
        mt5.shutdown()
        return False
    return True

def calcular_rsi(precos):
    try:
        delta = precos.diff()
        ganho = delta.clip(lower=0)
        perda = -delta.clip(upper=0)
        media_ganho = ganho.rolling(14).mean()
        media_perda = perda.rolling(14).mean()
        rs = media_ganho / media_perda
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return float(val) if not pd.isna(val) else 50.0
    except Exception:
        return 50.0

def movimentos(precos):
    alta_atual = 0
    queda_atual = 0
    try:
        valores = precos.values
        for i in range(len(valores) - 1, 0, -1):
            if valores[i] > valores[i-1]:
                if queda_atual > 0: break
                alta_atual += 1
            elif valores[i] < valores[i-1]:
                if alta_atual > 0: break
                queda_atual += 1
            else:
                break
    except Exception:
        pass
    return alta_atual, queda_atual

@app.route("/")
def index():
    resultados = []

    if not inicializar_mt5():
        return "Erro: O MetaTrader 5 precisa estar aberto no computador."

    for ticker in ATIVOS:
        try:
            rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 0, 300)
            
            if rates is None or len(rates) == 0:
                continue

            df = pd.DataFrame(rates)
            precos = df['close'].dropna()
            
            if len(precos) < 50:
                continue

            preco = float(precos.iloc[-1])
            rsi = calcular_rsi(precos)
            altas_seq, quedas_seq = movimentos(precos)

            # Pega os 5 últimos preços de fechamento brutos (absolutos em Reais)
            ultimos_5_fechamentos = [round(float(v), 2) for v in precos.tail(5).iloc[::-1].values]
            if len(ultimos_5_fechamentos) < 5:
                ultimos_5_fechamentos = [0.0, 0.0, 0.0, 0.0, 0.0]

            mm200_series = precos.rolling(len(precos)).mean()
            mm200 = float(mm200_series.iloc[-1]) if not pd.isna(mm200_series.iloc[-1]) else preco
            tendencia = "ALTA" if preco > mm200 else "BAIXA"

            suporte = float(precos.tail(120).quantile(.15)) if len(precos) >= 120 else float(precos.min())
            resistencia = float(precos.tail(120).quantile(.85)) if len(precos) >= 120 else float(precos.max())

            dist_suporte_pct = round(((preco - suporte) / suporte) * 100, 2) if suporte > 0 else 0.0
            dist_resistencia_pct = round(((resistencia - preco) / preco) * 100, 2) if preco > 0 else 0.0

            score = 0
            if tendencia == "ALTA": score += 35
            if rsi < 45: score += 25
            if quedas_seq >= 3: score += 25
            if preco > suporte: score += 15

            resultados.append({
                "Ativo": ticker,
                "Preço": round(preco, 2),
                "RSI": round(rsi, 2),
                "Tendência": tendencia,
                "AltasSeq": altas_seq,
                "QuedasSeq": quedas_seq,
                "Suporte": round(suporte, 2),
                "Resistência": round(resistencia, 2),
                "DistSuportePct": dist_suporte_pct,
                "DistResistenciaPct": dist_resistencia_pct,
                "UltimasVariacoes": ultimos_5_fechamentos, # Agora contém os valores absolutos
                "Score": score
            })
        except Exception as e:
            print(f"Erro ao processar o ativo {ticker} no MT5: {e}")

    mt5.shutdown()

    resultados_ordenados = sorted(resultados, key=lambda x: x["Score"], reverse=True)
    
    total_acoes = len(resultados_ordenados)
    melhor_ativo = resultados_ordenados[0]["Ativo"] if total_acoes > 0 else "-"

    return render_template(
        "index.html", 
        acoes=resultados_ordenados, 
        total=total_acoes, 
        melhor=melhor_ativo
    )

if __name__ == "__main__":
    app.run(debug=True)
