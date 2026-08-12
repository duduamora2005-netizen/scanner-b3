from flask import Flask, render_template
from scanner_put import executar_scanner

app = Flask(__name__)

@app.route("/")
def index():
    try:
        acoes_dados = executar_scanner()
        total_acoes = len(acoes_dados)
        melhor_ticker = acoes_dados[0]["Ativo"].replace(".SA", "") if total_acoes > 0 else "-"

        return render_template(
            "index.html", 
            acoes=acoes_dados, 
            total=total_acoes, 
            melhor=melhor_ticker
        )
    except Exception as e:
        print("Erro na rota principal:", e)
        return render_template(
            "index.html", 
            acoes=[], 
            total=0, 
            melhor="-"
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
