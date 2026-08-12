import requests
import pandas as pd

def buscar_dados_b3_oficial(ticker):
    # Formata o ticker para o padrão da B3 (ex: PETR4)
    ticker_limpo = ticker.replace(".SA", "").upper()
    
    # Endpoint oficial de dados históricos/diários da B3 integrados via API
    url = f"https://brapi.dev/api/v2/stocks/historical"
    params = {
        "symbols": ticker_limpo,
        "range": "1mo",       # Pega o último mês para garantir margem de pregões úteis
        "interval": "1d",
        "sortOrder": "desc"   # Traz do mais recente para o mais antigo (Hoje -> Antigo)
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
        
    # Extrai estritamente os preços brutos de fechamento ('close') de tela oficiais
    # O campo 'close' representa o valor bruto negociado no pregão daquele dia
    fechamentos_brutos = [item["close"] for item in historical_prices[:5]]
    
    # O preço atual (mais recente) é o primeiro da lista
    preco_atual = fechamentos_brutos[0]
    
    return {
        "Ativo": ticker_limpo + ".SA",
        "Preço": f"{preco_atual:.2f}",
        "UltimasVariacoes": fechamentos_brutos, # Lista com os 5 valores brutos em R$ (Hoje -> Antigo)
    }
