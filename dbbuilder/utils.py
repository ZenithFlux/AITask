from bs4 import BeautifulSoup


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, features="html.parser")

    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text
