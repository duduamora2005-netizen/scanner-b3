import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)

# Lista de ativos que você quer monitorar
ATIVOS = [
    "ABEV3", "AXIA3", "B3SA3", "BBAS3", "BBDC3", 
    "BPAC11", "CMIG4", "CSMG3", "EMBR3", "EQTL3", 
    "ITUB4", "ITSA4", "PRIO3", "SBSP3", "PETR4"
]

def calcular_rsi(precos):
    delta = precos.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    media_ganho = ganho.rolling(14).mean()
    media_perda = perda.rolling(14).mean()
    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

@app.route("/")
def index():
    resultados = []
    tickers_b3 = [f"{t}.SA" for t in ATIVOS]
    
    # Baixa dados em lote para evitar bloqueios do Yahoo
    try:
        dados = yf.download(tickers_b3, period="1y", group_by="ticker", progress=False)
    except:
        dados = pd.DataFrame()

    for ticker in ATIVOS:
        ativo_b3 = f"{ticker}.SA"
        # Seleciona o DataFrame do ativo específico
        df = dados[ativo_b3] if len(ATIVOS) > 1 else dados
        
        if df.empty or "Close" not in df.columns:
            continue
            
        precos = df['Close'].dropna()
        if len(precos) < 50:
            continue
            
        preco = float(precos.iloc[-1])
        rsi = calcular_rsi(precos)
        
        # Pega os 5 últimos fechamentos absolutos (R$)
        ultimos_5_fechamentos = [round(float(v), 2) for v in precos.tail(5).iloc[::-1].values]
        
        # Lógica de tendência e score simplificada
        mm200 = float(precos.rolling(200).mean().iloc[-1])
        tendencia = "ALTA" if preco > mm200 else "BAIXA"
        
        suporte = float(precos.tail(120).min())
        resistencia = float(precos.tail(120).max())
        
        score = (35 if tendencia == "ALTA" else 0) + (25 if rsi < 45 else 0)
        
        resultados.append({
            "Ativo": ticker,
            "Preço": round(preco, 2),
            "RSI": round(rsi, 2),
            "Tendência": tendencia,
            "Suporte": round(suporte, 2),
            "Resistência": round(resistencia, 2),
            "DistSuportePct": round(((preco - suporte)/suporte)*100, 2),
            "DistResistenciaPct": round(((resistencia - preco)/preco)*100, 2),
            "UltimasVariacoes": ultimos_5_fechamentos,
            "Score": score
        })

    resultados_ordenados = sorted(resultados, key=lambda x: x["Score"], reverse=True)
    return render_template("index.html", 
                           acoes=resultados_ordenados, 
                           total=len(resultados_ordenados), 
                           melhor=resultados_ordenados[0]["Ativo"] if resultados_ordenados else "-")

if __name__ == "__main__":
    app.run(debug=True)
