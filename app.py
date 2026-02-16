import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime
import urllib.parse

# Configuração da página
st.set_page_config(page_title="Monitor B3", layout="wide")

@st.cache_data(ttl=300)
def get_google_finance_data(ticker, exchange='BVMF'):
    url = f"https://www.google.com/finance/quote/{ticker}:{exchange}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {"ticker": ticker, "price": None, "change_pct": "0.00"}
        element = soup.find(attrs={"data-last-price": True})
        if element:
            data["price"] = float(element['data-last-price'])
        for span in soup.find_all(["span", "div"]):
            text = span.text.strip()
            if "%" in text and ("+" in text or "-" in text):
                match = re.search(r'([+-]\d+[\.,]\d+)%', text)
                if match:
                    data["change_pct"] = match.group(1).replace(',', '.')
                    break
        return data
    except Exception as e:
        return {"ticker": ticker, "price": None, "change_pct": "0.00", "error": str(e)}

if 'watchlist_data' not in st.session_state:
    st.session_state.watchlist_data = {"PETR4": 40.0, "VALE3": 90.0, "MXRF11": 10.5}

st.title("📈 Monitor de Preços & Margem")

# Sidebar
st.sidebar.header("Configurações")
phone = st.sidebar.text_input("WhatsApp (DDD)", placeholder="11999999999")
st.sidebar.markdown("---")
st.sidebar.subheader("Ativo")
ntick = st.sidebar.text_input("Ticker").upper().strip()
nteto = st.sidebar.number_input("Teto (R$)", min_value=0.0, step=0.1)
if st.sidebar.button("Salvar"):
    if ntick:
        st.session_state.watchlist_data[ntick] = nteto
        st.rerun()

st.sidebar.markdown("---")
for t, teto in list(st.session_state.watchlist_data.items()):
    c1, c2 = st.sidebar.columns([3, 1])
    c1.write(f"{t}: R${teto:.2f}")
    if c2.button("❌", key=f"d_{t}"):
        del st.session_state.watchlist_data[t]
        st.rerun()

# Main
if st.session_state.watchlist_data:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

    display_list = []
    for ticker, teto in st.session_state.watchlist_data.items():
        res = get_google_finance_data(ticker)
        if res.get("price"):
            p = res["price"]
            m = ((teto - p) / teto * 100) if teto > 0 else 0
            display_list.append({"Ticker": ticker, "Preço": p, "Teto": teto, "Margem": m, "Var": res["change_pct"]})
        else:
            st.warning(f"Não foi possível obter dados de {ticker}")

    if display_list:
        cols = st.columns(3)
        for i, d in enumerate(display_list):
            with cols[i % 3]:
                st.metric(f"{d['Ticker']} (Teto R${d['Teto']:.2f})", f"R$ {d['Preço']:.2f}", f"{d['Margem']:.2f}% Margem")
        
        st.markdown("### Resumo")
        st.table(pd.DataFrame(display_list))

        msg = f"*📊 Monitor ({datetime.now().strftime('%H:%M')})*\n\n"
        for d in display_list:
            msg += f"*{d['Ticker']}*: R$ {d['Preço']:.2f} | Margem: {d['Margem']:.2f}%\n"
        
        url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
        st.link_button("📲 WhatsApp", url)
else:
    st.info("Adicione ativos na lateral.")
