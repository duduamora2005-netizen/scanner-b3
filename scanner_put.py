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
            
            # Baixa os dados sem ajuste automático
            dados = yf.download(ativo_b3, period="1mo", auto_adjust=False, progress=False)
            
            if dados.empty:
                continue

            # Se retornado em formato MultiIndex, extrai as colunas brutas
            if isinstance(dados.columns, pd.MultiIndex):
                close_raw = dados['Close'].iloc[:, 0] if 'Close' in dados.columns.get_level_values(0) else dados.iloc[:, 0]
                adj_close = dados['Adj Close'].iloc[:, 0] if 'Adj Close' in dados.columns.get_level_values(0) else close_raw
            else:
                close_raw = dados['Close'] if 'Close' in dados else dados.iloc[:, 0]
                adj_close = dados['Adj Close'] if 'Adj Close' in dados else close_raw

            close_raw = close_raw.dropna()
            adj_close = adj_close.dropna()

            if len(close_raw) < 10:
                continue

            # RECUPERA O FECHAMENTO BRUTO DA B3 (Investing.com)
            # Reverte o fator de proporção de dividendos se o Close e Adj Close forem divergentes
            fator_ajuste = (adj_close / close_raw).iloc[-1]
            precos_brutos = close_raw if fator_ajuste == 0 else close_raw / (adj_close / close_raw)
            
            preco = float(precos_brutos.iloc[-1])
            rsi = calcular_rsi(precos_brutos)
            altas_seq, quedas_seq = movimentos(precos_brutos)
            
            mm200_series = precos_brutos.rolling(len(precos_brutos)).mean()
            mm200 = float(mm200_series.iloc[-1]) if not pd.isna(mm200_series.iloc[-1]) else preco
            
            tendencia = "ALTA" if preco > mm200 else "BAIXA"
            
            suporte = float(precos_brutos.tail(120).quantile(.15)) if len(precos_brutos) >= 120 else float(precos_brutos.min())
            resistencia = float(precos_brutos.tail(120).quantile(.85)) if len(precos_brutos) >= 120 else float(precos_brutos.max())

            dist_suporte_pct = round(((preco - suporte) / suporte) * 100, 2) if suporte > 0 else 0.0
            dist_resistencia_pct = round(((resistencia - preco) / preco) * 100, 2) if preco > 0 else 0.0

            # CÁLCULO DAS ÚLTIMAS VARIAÇÕES % EXATAS DO INVESTING
            # Pega a variação percentual dos preços brutos de fechamento
            pct_bruto = precos_brutos.pct_change() * 100
            
            # Descarta o dia de hoje (em aberto) e pega exatamente os últimos 5 dias encerrados (do mais recente para o mais antigo)
            variacoes_5d = pct_bruto.iloc[:-1].tail(5).iloc[::-1]
            ultimas_5_var = [round(float(v), 2) for v in variacoes_5d.values]

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
