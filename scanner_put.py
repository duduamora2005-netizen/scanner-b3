import pandas as pd
import numpy as np
import yfinance as yf

# ---------------------------------------------------------
# ATIVOS
# ---------------------------------------------------------

ATIVOS = [
    "ABEV3", "AXTA3", "B3SA3", "BBAS3",
    "BBSE3", "BRAP4", "CMIG4", "CSAN3",
    "ITUB4", "ITUB3", "ITSA4", "PETR3", 
    "GGBR4", "VALE3", "WEGE3"
]

# ---------------------------------------------------------
# CÁLCULO DAS ÚLTIMAS VARIAÇÕES
# ---------------------------------------------------------

def obter_variacoes(ticker, quantidade=5):
    """
    Calcula as últimas variações percentuais usando EXCLUSIVAMENTE
    o preço de fechamento (Close) não ajustado.
    
    Fórmula:
    ((Close atual / Close anterior) - 1) * 100
    
    Retorna da variação mais recente para a mais antiga.
    """
    try:
        # Busca o histórico recente da B3 via yfinance
        df = yf.Ticker(f"{ticker}.SA").history(period="1mo")
        
        if df.empty or len(df) < quantidade + 1:
            return None
            
        precos = df['Close'].dropna()
        
        if len(precos) < quantidade + 1:
            return None
            
        variacoes = precos.pct_change() * 100
        
        ultimas = (
            variacoes
            .dropna()
            .tail(quantidade)
            .iloc[::-1]
        )
        
        return [round(float(v), 2) for v in ultimas]
        
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
        return None

def executar_scanner():
    print("=== EXECUTANDO SCANNER B3 (PUT) ==-\n")
    resultados = []
    
    for ticker in ATIVOS:
        vars_diarias = obter_variacoes(ticker, quantidade=5)
        if vars_diarias:
            # Conta quantas quedas consecutivas ocorreram no topo da lista
            quedas = 0
            for v in vars_diarias:
                if v < 0:
                    quedas += 1
                else:
                    break
                    
            resultados.append({
                "ticker": ticker,
                "variacoes": vars_diarias,
                "quedas_consecutivas": quedas
            })
            print(f"Ativo: {ticker} | Variações: {vars_diarias} | Quedas: {quedas}")
            
    return resultados

if __name__ == "__main__":
    executar_scanner()
