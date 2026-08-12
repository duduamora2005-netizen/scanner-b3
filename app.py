import json
import subprocess
from flask import Flask, render_template

app = Flask(__name__)


def obter_dados_acao(ticker):
    # Executa o script do B3Analysis passando o ticker desejado
    resultado = subprocess.run(
        ["python", "scripts/fetch_stock.py", ticker],
        capture_output=True,
        text=True,
    )

    # Converte o retorno em formato JSON para um dicionário Python
    try:
        dados = json.loads(resultado.stdout)
        return dados
    except json.JSONDecodeError:
        return None


@app.route("/analise/<ticker>")
def analisar(ticker):
    # 1. Pega os dados usando o B3Analysis
    dados = obter_dados_acao(ticker)

    if not dados:
        return "Erro ao carregar dados da ação", 400

    # 2. Sua lógica de Score / Filtros do seu Scanner B3
    # Exemplo: aplicando seu cálculo com os dados obtidos
    pe = dados.get("pe_ttm", 0)
    ey = dados.get("earnings_yield", 0)

    score_customizado = 0
    if ey > 0.15:  # Se Earnings Yield for maior que 15%
        score_customizado += 50
    if pe < 6:  # Se P/L for menor que 6
        score_customizado += 50

    # 3. Envia os dados e o score calculado para a interface web
    return render_template(
        "dashboard.html", dados=dados, score=score_customizado
    )


if __name__ == "__main__":
    app.run(debug=True)
