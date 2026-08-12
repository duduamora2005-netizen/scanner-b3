from flask import Flask, render_template
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def buscar_dados_yfinance(ticker):
    try:
        # Garante o sufixo .SA para a B3
        ticker_completo = ticker if ticker.endswith(".SA") else ticker + ".SA"
        
        # Puxa os dados diários do último mês
        df = yf.download(ticker_completo, period="1mo", interval="1d", progress=False)
        
        if df.empty or len(df) < 5:
            return None
            
        # Trata o DataFrame do yfinance para extrair os últimos fechamentos
        fechamentos = df['Close'].dropna().tail(5).tolist()
        
        # Se vier em formato de Series aninhada do pandas, converte para float simples
        fechamentos_brutos = [float(f) for f in fechamentos]
        
        if len(fechamentos_brutos) < 5:
            return None
            
        # Inverte para mostrar de hoje -> antigo (conforme o seu layout)
        fechamentos_brutos.reverse()
        
        preco_atual = fechamentos_brutos[0]
        tendencia = "ALTA" if fechamentos_brutos[0] >= fechamentos_brutos[-1] else "BAIXA"
        
        return {
            "Ativo": ticker_completo.upper(),
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
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
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
        dados = buscar_dados_yfinance(ticker)
        if dados:
            acoes_processadas.append(dados)
            
    total = len(acoes_processadas)
    melhor = acoes_processadas[0]["Ativo"] if acoes_processadas else "-"
    
    return render_template('index.html', acoes=acoes_processadas, total=total, melhor=melhor)

if __name__ == "__main__":
    app.run()
