import requests
import pandas as pd

# ===============================
# ATIVOS (Padrão B3 sem .SA)
# ===============================

ativos = [
    "ABEV3", "B3SA3", "BBAS3", "BBDC3", 
    "BPAC11", "CMIG4", "CSMG3", "EMBR3", 
    "EQTL3", "ITUB4", "ITSA4", "PRIO3", 
    "SBSP3", "SAPR11", "VBBR3"
]

# ===============================
# BUSCAR VARIAÇÕES DIRETAMENTE DA B3
# ===============================

def obter_variacoes_b3_oficial(ticker):
    """
    Busca os dados históricos recentes direto da B3 através da API da BRAPI,
    retornando exatamente os percentuais de fechamento de pregão.
    """
    simbolo = ticker.replace(".SA", "").upper()
    try:
        # Endpoint oficial de histórico diário da B3
        url = f"https://brapi.dev/api/v2/stocks/historical?symbols={simbolo}&range=1mo&interval=1d&sortOrder=desc"
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return None
            
        historical = results[0].get("historicalDataPrice", [])
        
        if len(historical) < 6:
            return None
            
        # Calcula a variação percentual dia a dia com base nos fechamentos reais
        variacoes = []
        #historical vem ordenado do mais recente para o mais antigo (desc)
        for i in range(5):
            atual = historical[i]['close']
            anterior = historical[i+1]['close']
            pct = ((atual - anterior) / anterior) * 100
            variacoes.append(round(pct, 2))
            
        return variacoes
    except Exception as e:
        print(f"Erro ao buscar B3 para {ticker}: {e}")
        return None

# ===============================
# TESTE RÁPIDO DO SCANNER
# ===============================

def executar_scanner_b3():
    resultado = []
    for ativo in ativos:
        variacoes = obter_variacoes_b3_oficial(ativo)
        if variacoes:
            resultado.append({
                "Ativo": ativo,
                "UltimasVariacoes": variacoes
            })
    return resultado
