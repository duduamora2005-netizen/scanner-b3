from flask import Flask, render_template
from scanner_put import rodar_scanner

app = Flask(__name__)

@app.route('/')
def index():
    # Executa a função do scanner
    acoes = rodar_scanner()
    
    # Pega o ticker do ativo com maior Score
    melhor_opcao = acoes[0]["Ativo"].replace(".SA", "") if acoes else "N/A"
    
    return render_template(
        'index.html', 
        acoes=acoes, 
        total=len(acoes), 
        melhor=melhor_opcao
    )

if __name__ == '__main__':
    app.run(debug=True)