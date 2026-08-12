import requests
import pandas as pd
import numpy as np

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
# BUSCA SEGURA VIA BRAPI (EVITA ERRO 500)
# ===============================

def obter_dados_b3_seguro(ticker):
    """
    Busca cotações na BRAPI de forma segura, tratando qualquer instabilidade
    ou erro interno para nunca derrubar a aplicação no Render.
    """
    simbolo = ticker.replace(".SA", "").upper()
    try:
        # Usando o endpoint de cotação atual com histórico integrado
        url = f"https://brapi.dev/api/v2/stocks/{simbolo}?range=1y&interval=1d"
        response = requests.get(url, timeout=8)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return None
            
        ativo_info = results[0]
        preco_atual = ativo_info.get("regularMarketPrice", 0.0)
        historical = ativo_info.get("historicalDataPrice", [])
        
        if len(historical) < 30:
            return None
            
        precos = [item['close'] for item in historical]
        s_precos = pd.Series(precos[::-1]) # Ordem cronológica
        
        return {
            "preco": preco_atual,
            "precos_series": s_precos,
            "historical": historical
        }
    except Exception as e:
        print(f"Aviso: Erro temporário ao consultar {ticker}: {e}")
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
# SCANNER PRINCIPAL DO APP
# ===============================

def executar_scanner(lista_tickers=None):
    tickers_para_rodar = lista_tickers if lista_tickers else ativos
    resultado = []

    for ativo in tickers_para_rodar:
        try:
            simbolo_limpo = ativo.replace(".SA", "").upper()
            dados_b3 = obter_dados_b3_seguro(simbolo_limpo)
            
            if not dados_b3:
                continue

            preco = dados_b3["preco"]
            precos = dados_b3["precos_series"]
            historical = dados_b3["historical"]
            
            # Calcula as variações dos últimos 5 pregões de forma segura
            variacoes = []
            for i in range(5):
                if i + 1 < len(historical):
                    atual = historical[i]['close']
                    anterior = historical[i+1]['close']
                    pct = ((atual - anterior) / anterior) * 100
                    variacoes.append(round(pct, 2))
                else:
                    variacoes.append(0.0)

            rsi = calcular_rsi(precos)
            altas_seq, quedas_seq = movimentos(precos)
            
            mm200_series = precos.rolling(len(precos)).mean()
            mm200 = float(mm200_series.iloc[-1]) if not pd.isna(mm200_series.iloc[-1]) else preco
            tendencia = "ALTA" if preco > mm200 else "BAIXA"
            
            suporte = float(precos.tail(120).quantile(.15)) if len(precos) >= 120 else float(precos.min())
            resistencia = float(precos.tail(120).quantile(.85)) if len(precos) >= 120 else float(precos.max())

            dist_suporte_pct = round(((preco - suporte) / suporte) * 100, 2) if suporte > 0 else 0.0
            dist_resistencia_pct = round(((resistencia - preco) / preco) * 100, 2) if preco > 0 else 0.0

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
                "UltimasVariacoes": variacoes,
                "Score": score
            })

        except Exception as e:
            print(f"Erro ao processar ativo {ativo}: {e}")

    return sorted(resultado, key=lambda x: x["Score"], reverse=True)
