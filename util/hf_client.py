from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Use TF-IDF for lightweight text similarity (no heavy ML models)
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

def clean_text(text):
    """Clean text by handling NaN values and ensuring string format"""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return ""
    return str(text).strip()

def get_embeddings(texts):
    """Get TF-IDF embeddings for a list of texts"""
    if isinstance(texts, str):
        texts = [texts]
    
    # Clean all texts to handle NaN values
    cleaned_texts = [clean_text(text) for text in texts]
    
    # Filter out empty texts
    non_empty_texts = [text for text in cleaned_texts if text]
    
    if not non_empty_texts:
        # Return zero vector if no valid texts
        return np.zeros((len(texts), 1000))
    
    return vectorizer.fit_transform(non_empty_texts).toarray()

def get_similarity(text1, text2):
    """Get similarity between two texts using TF-IDF"""
    embeddings = get_embeddings([text1, text2])
    
    # Handle case where embeddings might be zero vectors
    if np.all(embeddings[0] == 0) or np.all(embeddings[1] == 0):
        return 0.0
    
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(similarity)

def get_similarities(source_sentence: str, query_sentences: List[str]):
    """Get similarity between a source sentence and a list of query sentences"""
    all_texts = [source_sentence] + query_sentences
    embeddings = get_embeddings(all_texts)
    
    # Calculate similarities with the first text (source_sentence)
    similarities = []
    for i in range(1, len(embeddings)):
        if np.all(embeddings[0] == 0) or np.all(embeddings[i] == 0):
            similarities.append(0.0)
        else:
            sim = cosine_similarity([embeddings[0]], [embeddings[i]])[0][0]
            similarities.append(float(sim))
    
    return similarities

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