import pandas as pd
import numpy as np
import yfinance as yf

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
# CÁLCULO DAS ÚLTIMAS VARIAÇÕES
# ===============================

def obter_variacoes_close(precos, quantidade=5):
    """
    Calcula as últimas variações percentuais usando EXCLUSIVAMENTE
    o preço de fechamento (Close) não ajustado.

    Fórmula:
    ((Close atual / Close anterior) - 1) * 100

    Retorna da variação mais recente para a mais antiga.
    """

    try:
        precos = precos.dropna()

        if len(precos) < quantidade + 1:
            return None

        variacoes = precos.pct_change() * 100

        ultimas = (
            variacoes
            .dropna()
            .tail(quantidade)
            .iloc[::-1]
        )

        return [round(float(v), 2) for v in ultimas]

    except Exception:
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
# MOVIMENTOS CONSECUTIVOS
# ===============================

def movimentos(precos):

    alta_atual = 0
    queda_atual = 0

    try:
        valores = precos.values

        for i in range(len(valores) - 1, 0, -1):

            if valores[i] > valores[i - 1]:

                if queda_atual > 0:
                    break

                alta_atual += 1

            elif valores[i] < valores[i - 1]:

                if alta_atual > 0:
                    break

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

            simbolo_limpo = ativo.replace(".SA", "").upper()
            ativo_b3 = f"{simbolo_limpo}.SA"

            # ==========================================
            # YAHOO FINANCE
            # ==========================================
            # IMPORTANTE:
            # auto_adjust=False mantém o Close original,
            # sem ajuste retroativo por dividendos/JCP.
            # ==========================================

            tk = yf.Ticker(ativo_b3)

            dados = tk.history(
                period="1y",
                auto_adjust=False
            )

            if dados.empty or "Close" not in dados.columns:
                continue

            # ==========================================
            # CLOSE NÃO AJUSTADO
            # ==========================================

            precos = dados["Close"].dropna()

            if len(precos) < 10:
                continue

            preco = float(precos.iloc[-1])

            # ==========================================
            # ÚLTIMAS 5 VARIAÇÕES
            # ==========================================

            ultimas_5_var = obter_variacoes_close(
                precos,
                quantidade=5
            )

            # ==========================================
            # RSI
            # ==========================================

            rsi = calcular_rsi(precos)

            # ==========================================
            # MOVIMENTOS
            # ==========================================

            altas_seq, quedas_seq = movimentos(precos)

            # ==========================================
            # MÉDIA MÓVEL
            # ==========================================

            mm200_series = precos.rolling(200).mean()

            mm200 = (
                float(mm200_series.iloc[-1])
                if not pd.isna(mm200_series.iloc[-1])
                else preco
            )

            tendencia = (
                "ALTA"
                if preco > mm200
                else "BAIXA"
            )

            # ==========================================
            # SUPORTE E RESISTÊNCIA
            # ==========================================

            if len(precos) >= 120:

                suporte = float(
                    precos.tail(120).quantile(.15)
                )

                resistencia = float(
                    precos.tail(120).quantile(.85)
                )

            else:

                suporte = float(precos.min())
                resistencia = float(precos.max())

            # ==========================================
            # DISTÂNCIAS
            # ==========================================

            dist_suporte_pct = (
                round(
                    ((preco - suporte) / suporte) * 100,
                    2
                )
                if suporte > 0
                else 0.0
            )

            dist_resistencia_pct = (
                round(
                    ((resistencia - preco) / preco) * 100,
                    2
                )
                if preco > 0
                else 0.0
            )

            # ==========================================
            # SCORE
            # ==========================================

            score = 0

            if tendencia == "ALTA":
                score += 35

            if rsi < 45:
                score += 25

            if quedas_seq >= 3:
                score += 25

            if preco > suporte:
                score += 15

            # ==========================================
            # RESULTADO
            # ==========================================

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

            print(
                f"Erro no ativo {ativo}: {e}"
            )

    return sorted(
        resultado,
        key=lambda x: x["Score"],
        reverse=True
    )
