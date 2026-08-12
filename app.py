from flask import Flask, render_template
import requests
import pandas as pd

app = Flask(__name__)

def buscar_dados_b3_oficial(ticker):
    ticker_limpo = ticker.replace(".SA", "").upper()
    url = f"https://brapi.dev/api/v2/stocks/historical"
    params = {
        "symbols": ticker_limpo,
        "range": "1mo",
        "interval": "1d",
        "sortOrder": "desc"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        results = data.get("results", [])
        if not results:
            return None
            
        historical_prices = results[0].get("historicalDataPrice", [])
        if len(historical_prices) < 5:
            return None
            
        # Extrai os preços brutos de fechamento ('close') oficiais de tela
        fechamentos_brutos = [item["close"] for item in historical_prices[:5]]
        preco_atual = fechamentos_brutos[0]
        
        # Cálculo básico de variação / tendência simples baseada nos últimos preços
        tendencia = "ALTA" if fechamentos_brutos[0] >= fechamentos_brutos[-1] else "BAIXA"
        
        return {
            "Ativo": ticker_limpo + ".SA",
            "Preço": f"{preco_atual:.2f}",
            "Suporte": f"{min(fechamentos_brutos):.2f}",
            "DistSuportePct": "0.0",
            "Resistência": f"{max(fechamentos_brutos):.2f}",
            "DistResistenciaPct": "0.0",
            "RSI": 50.0,
            "Tendência": tendencia,
            "UltimasVariacoes": fechamentos_brutos,
            "QuedasSeq": 0,
            "Score": 50
        }
    except:
        return None

@app.route('/')
def index():
    lista_tickers = [
        "ABEV3", "AXIA3", "B3SA3", "BBAS3",
        "BBDC3", "BPAC11", "CMIG4", "CSMG3",
        "EMBR3", "EQTL3", "ITUB4", "ITSA4",
        "PRIO3", "SBSP3", "SAPR11", "VBBR3"
    ]
    
    acoes_processadas = []
    for ticker in lista_tickers:
        dados = buscar_dados_b3_oficial(ticker)
        if dados:
            acoes_processadas.append(dados)
            
    total = len(acoes_processadas)
    melhor = acoes_processadas[0]["Ativo"] if acoes_processadas else "-"
    
    return render_template('index.html', acoes=acoes_processadas, total=total, melhor=melhor)

if __name__ == "__main__":
    app.run()
