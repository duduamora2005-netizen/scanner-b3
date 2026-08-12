from flask import Flask, render_template
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def buscar_dados_yfinance(ticker):
    try:
        ticker_completo = ticker if ticker.endswith(".SA") else ticker + ".SA"
        
        # Usar Ticker individual evita o bloqueio comum do yf.download em massa
        t = yf.Ticker(ticker_completo)
        df = t.history(period="10d")
        
        if df.empty or len(df) < 5:
            return None
            
        # Pega os últimos 5 fechamentos brutos de forma segura
        fechamentos_brutos = df['Close'].dropna().tail(5).tolist()
        
        if len(fechamentos_brutos) < 5:
            return None
            
        # Converte para float puro e inverte para (Hoje -> Antigo)
        fechamentos_brutos = [float(f) for f in fechamentos_brutos]
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
        print(f"Erro ao processar {ticker}: {e}")
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
