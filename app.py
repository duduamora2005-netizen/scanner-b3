from flask import Flask, render_template
from scanner_put import executar_scanner

app = Flask(__name__)

@app.route("/")
def index():
    acoes_dados = executar_scanner()
    
    total_acoes = len(acoes_dados)
    melhor_ticker = acoes_dados[0]["Ativo"].replace(".SA", "") if acoes_dados else "-"

    return render_template(
        "index.html", 
        acoes=acoes_dados, 
        total=total_acoes, 
        melhor=melhor_ticker
    )
