from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def buscar_dados_yfinance(ticker):
    try:
        ticker_completo = ticker if ticker.endswith(".SA") else ticker + ".SA"
        t = yf.Ticker(ticker_completo)
        df = t.history(period="10d")
        
        if df.empty or len(df) < 5:
            return None
            
        fechamentos = df['Close'].dropna().tail(5).tolist()
        fechamentos = [float(f) for f in fechamentos]
        fechamentos.reverse() # Hoje -> Antigo
        
        # Lógica de cores: compara dia atual com o dia anterior
        variacoes_com_cores = []
        for i in range(len(fechamentos)):
            valor = fechamentos[i]
            cor = "neutro"
            if i < len(fechamentos) - 1:
                if valor > fechamentos[i + 1]:
                    cor = "verde"
                elif valor < fechamentos[i + 1]:
                    cor = "vermelho"
            
            variacoes_com_cores.append({"valor": valor, "cor": cor})
            
        return {
            "Ativo": ticker_completo.upper(),
            "Preço": f"{fechamentos[0]:.2f}",
            "Suporte": f"{min(fechamentos):.2f}",
            "Resistência": f"{max(fechamentos):.2f}",
            "Tendência": "ALTA" if fechamentos[0] >= fechamentos[-1] else "BAIXA",
            "UltimasVariacoes": variacoes_com_cores
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
