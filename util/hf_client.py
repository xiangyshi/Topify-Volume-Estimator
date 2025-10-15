from typing import List
import numpy as np
import math
import re

STOPWORDS = set([
    'the','a','an','and','or','but','if','while','for','to','of','in','on','at','by','with','as','is','are','was','were','be','been','being','it','this','that'
])

def clean_text(text):
    """Clean text by handling NaN values and ensuring string format"""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return ""
    return str(text).strip()

def tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if t not in STOPWORDS]

def get_embeddings(texts):
    """Get simple normalized bag-of-words vectors (lightweight)."""
    if isinstance(texts, str):
        texts = [texts]
    cleaned_texts = [clean_text(text) for text in texts]
    tokenized = [tokenize(t) for t in cleaned_texts]
    # Build vocabulary
    vocab = {}
    for tokens in tokenized:
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)
            if len(vocab) >= 2000:
                break
        if len(vocab) >= 2000:
            break
    if not vocab:
        return np.zeros((len(texts), 1))
    # Build vectors
    vecs = np.zeros((len(texts), len(vocab)), dtype=float)
    for i, tokens in enumerate(tokenized):
        for t in tokens:
            idx = vocab.get(t)
            if idx is not None:
                vecs[i, idx] += 1.0
        # Normalize
        norm = math.sqrt(float((vecs[i] ** 2).sum()))
        if norm > 0:
            vecs[i] /= norm
    return vecs

def get_similarity(text1, text2):
    """Cosine similarity between two lightweight BoW vectors."""
    embeddings = get_embeddings([text1, text2])
    v1, v2 = embeddings[0], embeddings[1]
    denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)

def get_similarities(source_sentence: str, query_sentences: List[str]):
    """Get similarity between a source sentence and a list of query sentences"""
    all_texts = [source_sentence] + query_sentences
    embeddings = get_embeddings(all_texts)
    
    # Calculate cosine similarities with the first vector
    v0 = embeddings[0]
    v0_norm = np.linalg.norm(v0)
    sims = []
    for i in range(1, len(embeddings)):
        vi = embeddings[i]
        denom = (v0_norm * np.linalg.norm(vi))
        sims.append(float(np.dot(v0, vi) / denom) if denom != 0 else 0.0)
    return sims

# Example usage
if __name__ == "__main__":
    sentences = [
        "faceless video ai",
        "Faceless - Our AI automated content creation tool converts text to video in minutes and posts videos to your TikTok account. Faceless.video is your own content ...", 
        "Free AI Faceless Video Generator - Create faceless video with simple prompts. Our free AI faceless video maker writes scripts, adds media, voiceover, music & SFX, generating an impressive video ...",
        "Videoinu-Faceless video ai generator free - Easily create to engage, 30-minute animated episodes ready for YouTube, captivating young viewers from start to finish."
    ]
    
    similarity = get_similarities(sentences[0], sentences[1:])
    print(similarity)