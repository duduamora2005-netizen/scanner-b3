from flask import Flask, render_template
import scanner_put

app = Flask(__name__)

@app.route('/')
def home():
    # Executa a busca de opções do seu script scanner_put.py
    dados = scanner_put.executar_scanner() 
    return render_template('index.html', dados=dados)

if __name__ == '__main__':
    app.run()
