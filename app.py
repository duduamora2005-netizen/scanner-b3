from flask import Flask, render_template
import requests
import pandas as pd

# O Gunicorn procura por isso aqui:
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
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        return None
        
    data = response.json()
    results = data.get("results", [])
    
    if not results:
        return None
        
    historical_prices = results[0].get("historicalDataPrice", [])
    
    if len(historical_prices) < 5:
        return None
        
    fechamentos_brutos = [item["close"] for item in historical_prices[:5]]
    preco_atual = fechamentos_brutos[0]
    
    return {
        "Ativo": ticker_limpo + ".SA",
        "Preço": f"{preco_atual:.2f}",
        "UltimasVariacoes": fechamentos_brutos,
    }

# Rota principal (ajuste conforme a sua lógica atual)
@app.route('/')
def index():
    # Aqui você deve chamar a função para os seus ativos e passar para o template
    # Exemplo:
    # acoes_data = [buscar_dados_b3_oficial('PETR4'), ...]
    return render_template('index.html', acoes=[]) 

if __name__ == "__main__":
    app.run()
