import urllib.request
import json
import pandas as pd
import numpy as np
import yfinance as yf

# ===============================
# ATIVOS
# ===============================

ativos = [
    "ABEV3.SA", "AXIA3.SA", "B3SA3.SA", "BBAS3.SA",
    "BBDC3.SA", "BPAC11.SA", "CMIG4.SA", "CSMG3.SA",
    "EMBR3.SA", "EQTL3.SA", "ITUB4.SA", "ITSA4.SA",
    "PRIO3.SA", "SBSP3.SA", "SAPR11.SA", "VBBR3.SA"
]

# ===============================
# VARIAÇÕES OFICIAIS B3
# ===============================

def obter_variacoes_oficiais_b3(ticker):
    """
    Busca as variações percentuais oficiais sem o pulo de datas do Yahoo Finance.
    """
    try:
        simbolo = ticker.replace(".SA", "").upper()
        url = f"https://brapi.dev/api/quote/{simbolo}?range=1mo&interval=1d"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            history = data['results'][0]['historicalDataPrice']
            
            df = pd.DataFrame(history)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Variação % bruta sobre o fechamento da B3
            df['var_pct'] = df['close'].pct_change() * 100
            
            # Pega os 5 últimos pregões encerrados (do mais recente para o mais antigo)
            var_5d = df['var_pct'].dropna().iloc[:-1].tail(5).iloc[::-1]
            return [round(float(v), 2) for v in var_5d.values]
    except Exception:
        return None

# ===============================
# INDICADORES TÉCNICOS
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

def movimentos(precos):
    alta_atual = 0
    queda_atual = 0
    try:
        valores = precos.values
        for i in range(len(valores) - 1, 0, -1):
            if valores[i] > valores[i-1]:
                if queda_atual > 0: break
                alta_atual += 1
            elif valores[i] < valores[i-1]:
                if alta_atual > 0: break
                queda_atual += 1
            else:
                break
    except Exception:
        pass
    return alta_atual, queda_atual

# ===============================
# SCANNER COMPLETO
# ===============================

def executar_scanner(lista_tickers=None):
    tickers_para_rodar = lista_tickers if lista_tickers else ativos
    resultado = []

    for ativo in tickers_para_rodar:
        try:
            ativo_b3 = ativo if ativo.endswith('.SA') else f"{ativo}.SA"
            
            tk = yf.Ticker(ativo_b3)
            dados = tk.history(period="1y")
            
            if dados.empty or "Close" not in dados:
                continue

            precos = dados["Close"].dropna()
            if len(precos) < 50:
                continue

            preco = float(precos.iloc[-1])
            rsi = calcular_rsi(precos)
            altas_seq, quedas_seq = movimentos(precos)
            
            mm200_series = precos.rolling(len(precos)).mean()
            mm200 = float(mm200_series.iloc[-1]) if not pd.isna(mm200_series.iloc[-1]) else preco
            tendencia = "ALTA" if preco > mm200 else "BAIXA"
            
            suporte = float(precos.tail(120).quantile(.15)) if len(precos) >= 120 else float(precos.min())
            resistencia = float(precos.tail(120).quantile(.85)) if len(precos) >= 120 else float(precos.max())

            dist_suporte_pct = round(((preco - suporte) / suporte) * 100, 2) if suporte > 0 else 0.0
            dist_resistencia_pct = round(((resistencia - preco) / preco) * 100, 2) if preco > 0 else 0.0

            # Variação real B3
            ultimas_5_var = obter_variacoes_oficiais_b3(ativo)
            
            # Fallback caso a API externa falhe
            if not ultimas_5_var or len(ultimas_5_var) < 5:
                datas_inteiras = pd.date_range(start=precos.index.min(), end=precos.index.max(), freq='B')
                precos_corrigidos = precos.reindex(datas_inteiras).ffill()
                pct = precos_corrigidos.pct_change() * 100
                pct = pct[pct.index.isin(precos.index)].dropna()
                ultimas_5_var = [round(float(v), 2) for v in pct.iloc[:-1].tail(5).iloc[::-1].values]

            score = 0
            if tendencia == "ALTA": score += 35
            if rsi < 45: score += 25
            if quedas_seq >= 3: score += 25
            if preco > suporte: score += 15

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
            print(f"Erro no ativo {ativo}: {e}")

    return sorted(resultado, key=lambda x: x["Score"], reverse=True)
