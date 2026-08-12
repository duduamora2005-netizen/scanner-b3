from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def buscar_dados_yfinance(ticker):
    try:
        ticker_completo = ticker if ticker.endswith(".SA") else ticker + ".SA"
        t = yf.Ticker(ticker_completo)
        
        # Busca 12 dias para garantir que tenhamos pelo menos 6 pregões úteis
        df = t.history(period="12d")
        if df.empty or len(df) < 6:
            return None
            
        # Pega os últimos 6 valores de fechamento
        dados = df['Close'].dropna().tail(6).tolist()
        dados = [float(f) for f in dados]
        dados.reverse() # [Hoje(0), 1, 2, 3, 4, Base(5)]
        
        variacoes_com_cores = []
        # Processa apenas os 5 valores que você quer exibir
        for i in range(5):
            valor = dados[i]
            valor_anterior = dados[i + 1] # O 5º valor compara com o 6º
            
            if valor > valor_anterior:
                cor = "verde"
            elif valor < valor_anterior:
                cor = "vermelho"
            else:
                cor = "neutro"
            
            variacoes_com_cores.append({"valor": valor, "cor": cor})
            
        return {
            "Ativo": ticker_completo.upper(),
            "Preço": f"{dados[0]:.2f}",
            "Suporte": f"{min(dados[:5]):.2f}",
            "Resistência": f"{max(dados[:5]):.2f}",
            "RSI": 50.0,
            "Tendência": "ALTA" if dados[0] >= dados[4] else "BAIXA",
            "UltimasVariacoes": variacoes_com_cores,
            "Score": 50
        }
    except:
        return None

@app.route('/')
def index():
    lista = ["ABEV3", "AXIA3", "B3SA3", "BBAS3", "BBDC3", "BPAC11", "CMIG4", "CSMG3", 
             "EMBR3", "EQTL3", "ITUB4", "ITSA4", "PRIO3", "SBSP3", "SAPR11", "VBBR3"]
    acoes = [d for ticker in lista if (d := buscar_dados_yfinance(ticker))]
    return render_template('index.html', acoes=acoes, total=len(acoes), melhor=acoes[0]["Ativo"] if acoes else "-")

if __name__ == "__main__":
    app.run()
