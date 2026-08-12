import urllib.request
import json
import yfinance as yf
import pandas as pd
import numpy as np

# ===============================
# ATIVOS
# ===============================

ativos = [
    "ABEV3.SA",
    "AXIA3.SA",
    "B3SA3.SA",
    "BBAS3.SA",
    "BBDC3.SA",
    "BPAC11.SA",
    "CMIG4.SA",
    "CSMG3.SA",
    "EMBR3.SA",
    "EQTL3.SA",
    "ITUB4.SA",
    "ITSA4.SA",
    "PRIO3.SA",
    "SBSP3.SA",
    "SAPR11.SA",
    "VBBR3.SA"
]

# ===============================
# BUSCA VARIAÇÕES OFICIAIS DA B3 (SEM YAHOO)
# ===============================

def obter_variacoes_reais_b3(ticker):
    """
    Busca o histórico de fechamentos reais da B3 via API pública
    para não depender dos dados com falha do Yahoo Finance.
    """
    try:
        simbolo = ticker.replace(".SA", "").upper()
        url = f"https://brapi.dev/api/quote/{simbolo}?range=1mo&interval=1d"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            history = data['results'][0]['historicalDataPrice']
            
            # Converte em DataFrame
            df = pd.DataFrame(history)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Pega o preço de fechamento seco (close)
            df['var_pct'] = df['close'].pct_change() * 100
            
            # Remove o dia de hoje (em aberto) e pega os últimos 5 dias fechados
            var_5d = df['var_pct'].dropna().iloc[:-1].tail(5).iloc[::-1]
            return [round(float(v), 2) for v in var_5d.values]
    except Exception as e:
        return None

# ===============================
# RSI
# ===============================

def calcular_rsi(precos):
    try:
        delta = precos.diff()
        ganho = delta.clip(lower=0)
        perda = -delta.clip(upper=0)
        media_ganho = ganho.rolling(14).mean()
        media_perda = perda.rolling(14).mean()
        rs = media_ganho / media_perda
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return float(val) if not pd.isna(val) else 50.0
    except Exception:
        return 50.0

# ===============================
# MOVIMENTO (Quedas Consecutivas)
# ===============================

def movimentos(precos):
    alta_atual = 0
    queda_atual = 0

    try:
        valores = precos.values
        for i in range(len(valores) - 1, 0, -1):
            if valores[i] > valores[i-1]:
                if queda_atual > 0:
                    break
                alta_atual += 1
            elif valores[i] < valores[i-1]:
                if alta_atual > 0:
                    break
                queda_atual += 1
            else:
                break
    except Exception:
        pass

    return alta_atual, queda_atual

# ===============================
# SCANNER
# ===============================

def executar_scanner(lista_tickers=None):
    tickers_para_rodar = lista_tickers if lista_tickers else ativos
    resultado = []

    for ativo in tickers_para_rodar:
        try:
            ativo_b3 = ativo if ativo.endswith('.SA') else f"{ativo}.SA"
            
            # Download indicador geral via yfinance
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

            # BUSCA AS VARIAÇÕES % DIRETAS DA B3
            ultimas_5_var = obter_variacoes_reais_b3(ativo)
            
            # FALLBACK SE A API DA B3 ESTIVER INDISPONÍVEL
            if not ultimas_5_var or len(ultimas_5_var) < 5:
                pct = precos.pct_change().dropna()
                ultimas_5_var = [round(float(v), 2) for v in pct.iloc[:-1].tail(5).iloc[::-1].values]

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
