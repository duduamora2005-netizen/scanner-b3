import yfinance as yf

# Lista de tickers que você deseja analisar
TICKERS_PADRAO = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", 
    "ABEV3", "MGLU3", "RENT3", "WEGE3", "VBBR3"
]

def obter_ultimos_fechamentos(ticker):
    """
    Consulta exclusivamente o Yahoo Finance e retorna os últimos 5 preços
    oficiais de fechamento em ordem cronológica (do mais antigo para o mais recente).
    """
    try:
        ticker_b3 = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
        ativo = yf.Ticker(ticker_b3)
        
        # Puxa histórico recente (10 dias para cobrir finais de semana e feriados)
        df = ativo.history(period="10d")
        
        # Seleciona apenas os preços de fechamento (Close)
        fechamentos = df['Close'].dropna().tail(5)
        
        if len(fechamentos) < 5:
            return "Não foi encontrado."
        
        # Retorna a lista simples de valores em Reais (R$)
        return [round(float(preco), 2) for preco in fechamentos.tolist()]
    except Exception:
        return "Não foi encontrado."


def executar_scanner(lista_tickers=None):
    if not lista_tickers:
        lista_tickers = TICKERS_PADRAO

    resultados = []

    for ticker in lista_tickers:
        fechamentos = obter_ultimos_fechamentos(ticker)
        
        try:
            ticker_b3 = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
            ativo = yf.Ticker(ticker_b3)
            cotacao_atual = round(ativo.fast_info['lastPrice'], 2)
        except Exception:
            cotacao_atual = "N/D"

        resultados.append({
            'ticker': ticker.upper().replace('.SA', ''),
            'cotacao_atual': cotacao_atual,
            'fechamentos_5d': fechamentos
        })

    return resultados

if __name__ == '__main__':
    print(executar_scanner())
