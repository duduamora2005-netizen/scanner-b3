import yfinance as yf
import pandas as pd

# Lista padrão de ativos da B3 para escanear
TICKERS_PADRAO = [
    "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", 
    "ABEV3", "MGLU3", "RENT3", "WEGE3", "B3SA3"
]

def obter_ultimos_fechamentos(ticker):
    """
    Consulte exclusivamente o Yahoo Finance. Para cada ticker informado, 
    retorne os últimos cinco preços oficiais de fechamento em ordem cronológica 
    (do mais antigo para o mais recente). Não calcule médias, variações ou indicadores. 
    Não estime valores. Se um dado não estiver disponível, informe que não foi encontrado.
    """
    try:
        # Garante o sufixo .SA para ações da B3 no Yahoo Finance
        ticker_b3 = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
        
        ativo = yf.Ticker(ticker_b3)
        
        # Puxa histórico recente (10d para cobrir finais de semana e feriados)
        df = ativo.history(period="10d")
        
        # Filtra apenas a coluna de fechamento (Close) e remove nulos
        fechamentos = df['Close'].dropna().tail(5)
        
        if len(fechamentos) < 5:
            return "Não foi encontrado."
        
        # Retorna os 5 valores arredondados para 2 casas decimais em ordem cronológica
        return [round(preco, 2) for preco in fechamentos.tolist()]

    except Exception:
        return "Não foi encontrado."


def executar_scanner(lista_tickers=None):
    """
    Executa a varredura dos tickers e gera a lista de dados estruturada para a interface Flask.
    """
    if not lista_tickers:
        lista_tickers = TICKERS_PADRAO

    resultados = []

    for ticker in lista_tickers:
        fechamentos = obter_ultimos_fechamentos(ticker)
        
        # Tenta buscar a cotação atual rápida do ativo
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
    # Teste de execução no terminal
    print("Rodando o scanner...")
    dados = executar_scanner()
    for item in dados:
        print(f"Ticker: {item['ticker']} | Atual: {item['cotacao_atual']} | Últimos 5 Fechamentos: {item['fechamentos_5d']}")
