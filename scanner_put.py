import json
import urllib.request
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
# VARIAÇÕES DINÂMICAS NOMINAIS (B3 / INVESTING)
# ===============================

def obter_variacoes_oficiais_b3(ticker):
    """
    Calcula dinamicamente as variações percentuais nominais da B3
    (sem ajuste retroativo por dividendos), mantendo a mesma precisão do Investing.com.
    """
    try:
        simbolo = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        
        # Puxa os preços brutos nominais negociados em tela
        df = yf.download(simbolo, period="1mo", auto_adjust=False, progress=False)
        
        if df.empty or "Close" not in df:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][simbolo] if simbolo in df['Close'] else df['Close'].iloc[:, 0]
        else:
            close = df['Close']

        close = close.dropna()

        # Variação % bruta sobre o fechamento nominal
        variacoes = close.pct_change() * 100
        
        # Pega os 5 últimos pregões encerrados (do mais recente ao mais antigo)
        var_5d = variacoes.dropna().iloc[:-1].tail(5).iloc[::-1]
        
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

            # Variação B3 dinâmica calculada em tempo real
            ultimas_5_var = obter_variacoes_oficiais_b3(ativo)
            
            if not ultimas_5_var:
                pct = precos.pct_change() * 100
                ultimas_5_var = [round(float(v), 2) for v in pct.dropna().iloc[:-1].tail(5).iloc[::-1].values]

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
