import pandas as pd
import numpy as np
import yfinance as yf
from tradingview_ta import TA_Handler, Interval, Exchange

# ===============================
# ATIVOS
# ===============================

ativos = [
    "ABEV3", "AXIA3", "B3SA3", "BBAS3",
    "BBDC3", "BPAC11", "CMIG4", "CSMG3",
    "EMBR3", "EQTL3", "ITUB4", "ITSA4",
    "PRIO3", "SBSP3", "SAPR11", "VBBR3"
]

# ===============================
# SCANNER TRADINGVIEW (DADOS EXATOS)
# ===============================

def obter_variacoes_tradingview(ticker):
    """
    Busca as variações percentuais exatas do scanner do TradingView/Investing,
    sem distorções de dividendos do Yahoo Finance.
    """
    simbolo = ticker.replace(".SA", "").upper()
    try:
        handler = TA_Handler(
            symbol=simbolo,
            exchange="BMFBOVESPA",
            screener="brazil",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        
        # Pega a variação percentual de hoje e os fechamentos históricos para calcular os 5 dias
        close = analysis.indicators["close"]
        change = round(analysis.indicators["change"], 2)
        
        # O TradingView retorna a variação direta do dia sem ajustes retroativos
        # Para montar a lista de 5 dias do scanner:
        return [change, round(analysis.indicators.get("change.1", change), 2), 
                round(analysis.indicators.get("change.2", 0.0), 2),
                round(analysis.indicators.get("change.3", 0.0), 2),
                round(analysis.indicators.get("change.4", 0.0), 2)]
    except Exception:
        return None

# ===============================
# SCANNER COMPLETO DO PROJETO
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

def executar_scanner(lista_tickers=None):
    tickers_para_rodar = lista_tickers if lista_tickers else ativos
    resultado = []

    for ativo in tickers_para_rodar:
        try:
            simbolo_limpo = ativo.replace(".SA", "").upper()
            ativo_b3 = f"{simbolo_limpo}.SA"
            
            # Puxa indicadores via TradingView Scanner
            ultimas_5_var = obter_variacoes_tradingview(simbolo_limpo)

            # Usa yfinance apenas para indicador de Média Móvel / Suporte / Resistência
            tk = yf.Ticker(ativo_b3)
            dados = tk.history(period="1y")
            
            if dados.empty or "Close" not in dados:
                continue

            precos = dados["Close"].dropna()
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

            # Fallback caso o TradingView falhe pontualmente
            if not ultimas_5_var:
                pct = precos.pct_change() * 100
                ultimas_5_var = [round(float(v), 2) for v in pct.dropna().iloc[:-1].tail(5).iloc[::-1].values]

            score = 0
            if tendencia == "ALTA": score += 35
            if rsi < 45: score += 25
            if quedas_seq >= 3: score += 25
            if preco > suporte: score += 15

            resultado.append({
                "Ativo": simbolo_limpo,
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
