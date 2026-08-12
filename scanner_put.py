import requests
import pandas as pd
import yfinance as yf

def obter_variacoes_investing_b3(ticker):
    """
    Busca histórico direto via API B3 sem ajustes retroativos de dividendos
    """
    try:
        # Formata o ticker para o padrão nominal
        simbolo = ticker.replace(".SA", "").upper()
        url = f"https://brapi.dev/api/quote/{simbolo}?range=1mo&interval=1d"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            dados = response.json()
            results = dados.get('results', [])[0]
            historical = results.get('historicalDataPrice', [])
            
            # Converte em DataFrame
            df_hist = pd.DataFrame(historical)
            
            # Pega a coluna 'close' nominal
            close_series = df_hist['close']
            
            # Calcula pct_change
            pct = close_series.pct_change() * 100
            
            # Pega as últimas 5 variações encerradas (exclui o pregão de hoje)
            var_5 = (pct.iloc[:-1].tail(5) * -1 if False else pct.iloc[:-1].tail(5)).iloc[::-1]
            return [round(float(v), 2) for v in var_5.values]
    except Exception:
        pass
    return None

def executar_scanner(lista_tickers=None):
    tickers_para_rodar = lista_tickers if lista_tickers else ativos
    resultado = []

    for ativo in tickers_para_rodar:
        try:
            ativo_b3 = ativo if ativo.endswith('.SA') else f"{ativo}.SA"
            
            tk = yf.Ticker(ativo_b3)
            dados = tk.history(period="2y")
            
            if dados.empty or "Close" not in dados:
                continue

            precos = dados["Close"].dropna()
            if len(precos) < 200:
                continue

            preco = float(precos.iloc[-1])
            rsi = calcular_rsi(precos)
            altas_seq, quedas_seq = movimentos(precos)
            
            mm200_series = precos.rolling(200).mean()
            mm200 = float(mm200_series.iloc[-1]) if not pd.isna(mm200_series.iloc[-1]) else preco
            
            tendencia = "ALTA" if preco > mm200 else "BAIXA"
            
            suporte = float(precos.tail(120).quantile(.15))
            resistencia = float(precos.tail(120).quantile(.85))

            dist_suporte_pct = round(((preco - suporte) / suporte) * 100, 2) if suporte > 0 else 0.0
            dist_resistencia_pct = round(((resistencia - preco) / preco) * 100, 2) if preco > 0 else 0.0

            # Tenta buscar as variações oficiais da B3 sem ajuste por API
            ultimas_5_var = obter_variacoes_investing_b3(ativo)
            
            # Fallback caso a API falhe
            if not ultimas_5_var or len(ultimas_5_var) < 5:
                variacoes_pct = (precos.pct_change().dropna().tail(6).iloc[:-1] * 100).iloc[::-1]
                ultimas_5_var = [round(float(v), 2) for v in variacoes_pct.values]

            score = 0
            if tendencia == "ALTA":
                score += 35
            if rsi < 45:
                score += 25
            if quedas_seq >= 3:
                score += 25
            if preco > suporte:
                score += 15

            resultado.append({
                "Ativo": ativo,
                "Preço": round(preco, 2),
                "RSI": round(rsi, 2),
                "Tendência": tendencia,
                "AltasSeq": altas_seq,
                "QuedasSeq": quedas_seq,
                "Suporte": round(suporte, 2),
                "Resistência": round(resistencia, 2),
                "DistSuportePct": dist_suporte_pct,
                "DistResistenciaPct": dist_resistencia_pct,
                "UltimasVariacoes": ultimas_5_var,
                "Score": score
            })

        except Exception as e:
            print(f"Erro ao processar ativo {ativo}: {e}")

    return sorted(resultado, key=lambda x: x["Score"], reverse=True)
