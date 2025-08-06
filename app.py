import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(show_spinner=False)
def build_sku_to_url_map():
    sitemap_url = "https://www.frigidaire.com/sitemap.xml"
    resp = requests.get(sitemap_url)
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


def scrape_product_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    def safe_select(selector):
        el = soup.select_one(selector)
        return el.text.strip() if el else "N/A"

    return {
        "Title": safe_select("h1"),
        "Price": safe_select(".price-value"),
        "Original Price": safe_select(".price-strike-through"),
        "Rating": safe_select(".bvseo-ratingValue"),
        "Image URL": soup.select_one("img.primary-image")['src'] if soup.select_one("img.primary-image") else "N/A",
        "URL": url
    }

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
        with st.spinner("Scraping product data..."):
            data = scrape_product_page(product_url)

        if not data:
            st.error("Failed to scrape product page.")
        else:
            st.subheader(data["Title"])
            st.image(data["Image URL"], width=350)
            st.write(f"**Price:** {data['Price']}")
            st.write(f"**Original Price:** {data['Original Price']}")
            st.write(f"**Rating:** {data['Rating']}")
            st.markdown(f"[View on Frigidaire]({data['URL']})")
