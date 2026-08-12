import yfinance as yf
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

# Sua lista de ativos padrão da B3
ATIVOS = [
    "ABEV3", "AXIA3", "B3SA3", "BBAS3",
    "BBDC3", "BPAC11", "CMIG4", "CSMG3",
    "EMBR3", "EQTL3", "ITUB4", "ITSA4",
    "PRIO3", "SBSP3", "SAPR11", "VBBR3"
]

def obter_variacoes(ticker, dias=5):
    """
    Calcula as últimas variações percentuais usando EXCLUSIVAMENTE
    o preço de fechamento (Close) não ajustado via yfinance.
    """
    try:
        # Pega os dados dos últimos 30 dias para ter margem segura
        df = yf.Ticker(f"{ticker}.SA").history(period="1mo")
        
        if df.empty or len(df) < dias + 1:
            return None
            
        precos = df['Close'].dropna()
        if len(precos) < dias + 1:
            return None
            
        variacoes = precos.pct_change() * 100
        ultimas = variacoes.dropna().tail(dias).iloc[::-1]
        
        return [round(float(x), 2) for x in ultimas]
    except Exception as e:
        print(f"Erro ao buscar {ticker}: {e}")
        return None

@app.route("/")
def index():
    resultados = []

    for ticker in ATIVOS:
        vars_diarias = obter_variacoes(ticker, dias=5)
        if vars_diarias:
            # Conta quantas quedas consecutivas ocorreram no início da lista
            quedas_consecutivas = 0
            for v in vars_diarias:
                if v < 0:
                    quedas_consecutivas += 1
                else:
                    break

            resultados.append({
                "Ativo": ticker,
                "UltimasVariacoes": vars_diarias,
                "QuedasSeq": quedas_consecutivas
            })

    return render_template("index.html", resultados=resultados)

if __name__ == "__main__":
    app.app_context().push()
    app.run(debug=True)
