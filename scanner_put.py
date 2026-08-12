import yfinance as yf

TICKERS_PADRAO = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", 
    "ABEV3", "MGLU3", "RENT3", "WEGE3", "VBBR3"
]

def obter_dados_ativo(ticker):
    try:
        ticker_b3 = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
        ativo = yf.Ticker(ticker_b3)
        
        # Historico de 10 dias para pegar os ultimos 5 fechamentos com seguranca
        df = ativo.history(period="10d")
        fechamentos = df['Close'].dropna().tail(5).tolist()
        
        if len(fechamentos) < 5:
            return None

        preco_atual = round(float(ativo.fast_info['lastPrice']), 2)
        fechamentos_fmt = [round(float(p), 2) for p in fechamentos]
        
        # Calculos analiticos
        variacao = round(((preco_atual - fechamentos_fmt[0]) / fechamentos_fmt[0]) * 100, 2)
        media_5d = round(sum(fechamentos_fmt) / len(fechamentos_fmt), 2)
        
        # Preco de entrada estimado e alvo/stop ficticios para manter estrutura anterior
        preco_entrada = round(preco_atual * 0.98, 2)
        alvo = round(preco_atual * 1.05, 2)
        stop = round(preco_atual * 0.95, 2)
        score = round((preco_atual / media_5d) * 10, 1)

        return {
            'ticker': ticker.upper().replace('.SA', ''),
            'cotacao_atual': preco_atual,
            'entrada': preco_entrada,
            'alvo': alvo,
            'stop': stop,
            'score': score,
            'variacao': variacao,
            'fechamentos_5d': fechamentos_fmt
        }
    except Exception:
        return None

def executar_scanner(lista_tickers=None):
    if not lista_tickers:
        lista_tickers = TICKERS_PADRAO

    resultados = []
    for ticker in lista_tickers:
        dados = obter_dados_ativo(ticker)
        if dados:
            resultados.append(dados)

    resultados = sorted(resultados, key=lambda x: x['score'], reverse=True)
    return resultados
