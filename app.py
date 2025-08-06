import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(show_spinner=False, ttl=3600)
def build_sku_to_url_map():
    try:
        sitemap_url = "https://www.frigidaire.com/sitemap.xml"
        resp = requests.get(sitemap_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        st.error(f"Failed to load sitemap: {e}")
        return {}

    urls = []
    root = ElementTree.fromstring(resp.content)
    for url_elem in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        if "/en/p/" in loc:
            urls.append(loc)

    sku_url_map = {}
    for url in urls:
        sku = url.strip("/").split("/")[-1].upper()
        sku_url_map[sku] = url

    return sku_url_map

def get_msrp_from_product_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "Failed to load page"

    soup = BeautifulSoup(resp.text, "html.parser")
    msrp_tag = soup.find("span", class_="Utility-TextStrike-Through-Price")
    if msrp_tag:
        return msrp_tag.get_text(strip=True)
    else:
        return "MSRP not found"

# Streamlit App UI
st.title("Frigidaire SKU Lookup")
st.caption("Enter any Frigidaire SKU (e.g., FGID2479SF, GRMC2273CF-C1)")

sku_input = st.text_input("SKU", max_chars=30).strip().upper()

if sku_input:
    with st.spinner("Looking up SKU..."):
        sku_map = build_sku_to_url_map()
        product_url = sku_map.get(sku_input)

    if not product_url:
        st.error("SKU not found in sitemap.")
    else:
        with st.spinner("Getting MSRP..."):
            msrp = get_msrp_from_product_page(product_url)
        st.success(f"MSRP for {sku_input}: {msrp}")
        st.markdown(f"[View Product Page]({product_url})")
