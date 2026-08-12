import yfinance as yf

TICKERS_PADRAO = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", 
    "ABEV3", "MGLU3", "RENT3", "WEGE3", "VBBR3"
]

def calcular_rsi(precos, periodos=14):
    if len(precos) < periodos + 1:
        return 50.0
    
    ganhos, perdas = [], []
    for i in range(1, len(precos)):
        diff = precos[i] - precos[i-1]
        ganhos.append(diff if diff > 0 else 0)
        perdas.append(abs(diff) if diff < 0 else 0)
        
    media_ganhos = sum(ganhos[-periodos:]) / periodos
    media_perdas = sum(perdas[-periodos:]) / periodos
    
    if media_perdas == 0:
        return 100.0
    
    rs = media_ganhos / media_perdas
    return round(100 - (100 / (1 + rs)), 2)

def obter_dados_ativo(ticker):
    try:
        ticker_b3 = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
        ativo = yf.Ticker(ticker_b3)
        
        df = ativo.history(period="60d")
        if df.empty or len(df) < 15:
            return None

        precos_fechamento = df['Close'].dropna().tolist()
        preco_atual = round(float(ativo.fast_info['lastPrice']), 2)
        
        # Suporte e Resistencia simples (Minima e Maxima de 60d)
        suporte = round(min(precos_fechamento), 2)
        resistencia = round(max(precos_fechamento), 2)
        
        var_suporte = round(((preco_atual - suporte) / suporte) * 100, 2)
        var_resistencia = round(((resistencia - preco_atual) / preco_atual) * 100, 2)
        
        # RSI e Tendencia
        rsi = calcular_rsi(precos_fechamento)
        tendencia = "ALTA" if preco_atual > (sum(precos_fechamento[-20:]) / 20) else "BAIXA"
        
        # Ultimas 5 Variaçoes % (Hoje -> Antigo)
        ultimos_6 = precos_fechamento[-6:]
        variacoes_5d = []
        for i in range(len(ultimos_6)-1, 0, -1):
            var_dia = round(((ultimos_6[i] - ultimos_6[i-1]) / ultimos_6[i-1]) * 100, 2)
            variacoes_5d.append(var_dia)
            
        score = round((100 - rsi) * 0.1, 1)

        return {
            'ticker': ticker.upper().replace('.SA', ''),
            'preco': preco_atual,
            'suporte': suporte,
            'var_suporte': var_suporte,
            'resistencia': resistencia,
            'var_resistencia': var_resistencia,
            'rsi': rsi,
            'tendencia': tendencia,
            'variacoes_5d': variacoes_5d,
            'score': score
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
    
    # Atribui o Rank
    for index, item in enumerate(resultados):
        item['rank'] = f"#{index + 1}"
        
    return resultados
