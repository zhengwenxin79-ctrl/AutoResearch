from __future__ import annotations

from urllib.parse import urlencode
from xml.etree import ElementTree

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text


def _text(node: ElementTree.Element | None, path: str) -> str:
    found = node.find(path) if node is not None else None
    return clean_text(found.text if found is not None else "")


def search_pubmed(query: str, limit: int = 10) -> list[PaperRecord]:
    query = (
        query.replace("VLM", '"vision language" OR multimodal')
        .replace("vlm", '"vision language" OR multimodal')
    )
    with get_client() as client:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode(
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": limit,
                "sort": "relevance",
            }
        )
        search_response = client.get(search_url)
        search_response.raise_for_status()
        ids = search_response.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urlencode(
            {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
        )
        fetch_response = client.get(fetch_url)
        fetch_response.raise_for_status()

    root = ElementTree.fromstring(fetch_response.text)
    papers: list[PaperRecord] = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find("MedlineCitation")
        pmid = _text(medline, "PMID")
        article_node = medline.find("Article") if medline is not None else None
        title = _text(article_node, "ArticleTitle")
        abstract_parts = [
            clean_text(node.text)
            for node in article_node.findall(".//AbstractText")
        ] if article_node is not None else []
        journal = article_node.find("Journal") if article_node is not None else None
        venue = _text(journal, "Title")
        year_text = _text(journal, ".//PubDate/Year")
        year = int(year_text) if year_text.isdigit() else None
        authors = []
        for author in article_node.findall(".//Author")[:8] if article_node is not None else []:
            name = clean_text(
                " ".join(
                    part
                    for part in [
                        _text(author, "ForeName"),
                        _text(author, "LastName"),
                    ]
                    if part
                )
            )
            if name:
                authors.append(name)
        doi = ""
        pmcid = ""
        for id_node in article.findall(".//ArticleId"):
            id_type = id_node.attrib.get("IdType", "")
            if id_type == "doi":
                doi = clean_text(id_node.text)
            elif id_type == "pmc":
                pmcid = clean_text(id_node.text)
        papers.append(
            PaperRecord(
                title=title,
                abstract=clean_text(" ".join(abstract_parts)),
                year=year,
                venue=venue,
                authors=authors,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                source="pubmed",
                source_records=["pubmed"],
            )
        )
    return papers
