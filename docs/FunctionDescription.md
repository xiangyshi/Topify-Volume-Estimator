# 🌐 Domain-Amplified ChatGPT Potential Model

The goal is to estimate the **ChatGPT query volume potentially led to a specific domain** for a given keyword:

\[
\hat V_{\text{chat\_to\_domain}}(k, p) = \hat V_{\text{chat\_keyword}}(k) \times \text{Share}_{\text{domain}}(k, p)
\]

---

## 1️⃣ Keyword-level ChatGPT volume

\[
\hat V_{\text{chat\_keyword}}(k) \quad \text{from DataForSEO - AI keyword API}
\]

Represents the latent query volume potential of **keyword \(k\)** in ChatGPT.

**Implementation**: Fetched via `util/dfs_client.py` using DataForSEO's AI keyword search volume endpoint.

---

## 2️⃣ Domain share model

The **share of keyword volume assigned to a specific domain** is computed as a softmax over candidate SERP results:

\[
\text{Share}_{\text{domain}}(k, p) = 
\frac{\exp(\text{logit}_{p})}{\sum_{q \in \text{TopN}(k)} \exp(\text{logit}_q)}
\]

where

\[ \text{logit}_q = \lambda_1 \cdot \text{Vis}_q + \lambda_2 \cdot \text{Sem}_q + \lambda_3 \cdot \text{Auth}_q + \lambda_4 \cdot \text{Feat}_q + \lambda_5 \cdot \log( \text{EstimatedClicks}_q + 1 )
\]

---

## 🔧 Feature Definitions & Implementation

| Feature | Description | Range | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| \( \text{Vis}_q \) | Visibility score derived from absolute SERP rank with exponential decay | [0,1] | `exp(-α * rank_absolute)` | ✅ **Active** |
| \( \text{Sem}_q \) | Semantic match between keyword and page content using TF-IDF similarity | [0,1] | `cosine_similarity(TF-IDF(keyword), TF-IDF(title+description))` | ✅ **Active** |
| \( \text{Auth}_q \) | Domain authority proxy (currently disabled) | [0,1] | Placeholder for future implementation | ❌ **Disabled** |
| \( \text{Feat}_q \) | SERP feature boosts (featured snippets, people also ask) | [0,1] | `in_people_also_ask` + `is_featured_snippet` | ✅ **Active** |
| \( \text{EstimatedClicks}_q \) | Estimated clicks from Google Ads search volume × CTR(rank) | ℝ⁺ | Placeholder for future implementation | ❌ **Disabled** |

### **Current Active Features (3/5)**

**Visibility (Vis)**: 
- **Formula**: `exp(-α * rank_absolute)`
- **Default α**: 0.15
- **Range**: [0, 1] (rank 1 = 1.0, rank 30 ≈ 0.01)
- **Implementation**: `model.py` → `_compute_visibility()`

**Semantic Relevance (Sem)**:
- **Method**: TF-IDF cosine similarity
- **Input**: Keyword vs. (title + description)
- **Range**: [0, 1] (perfect match = 1.0, no match = 0.0)
- **Implementation**: `util/hf_client.py` → `get_similarities()`

**SERP Features (Feat)**:
- **Components**: 
  - `in_people_also_ask`: Boolean (0 or 1)
  - `is_featured_snippet`: Boolean (0 or 1)
- **Range**: [0, 1] (no features = 0, all features = 1)
- **Implementation**: `model.py` → `_compute_feature_score()`

### **Disabled Features (2/5)**

**Authority (Auth)**: Currently disabled due to API limitations and complexity
**Estimated Clicks**: Currently disabled due to data requirements and computational overhead

---

## 📊 Current Model Implementation

### **Logit Computation**
```
logit = λ₁×vis + λ₂×sem + λ₃×auth + λ₄×feat + λ₅×log(est_clicks+1)
```

**Current Active Version**:
```
logit = λ₁×vis + λ₂×sem + λ₄×feat
```

**Default Parameters**:
- λ₁ (Visibility): 1.5
- λ₂ (Semantic): 1.0  
- λ₃ (Authority): 0.0 (disabled)
- λ₄ (Features): 1.0
- λ₅ (Clicks): 0.0 (disabled)

### **Feature Scaling**
All features are normalized using `sklearn.preprocessing.MinMaxScaler` to [0, 1] range before logit computation to prevent bias from different scales.

### **Domain Share Calculation**
\[
\text{Share}_{\text{domain}}(k, p) = 
\frac{\exp(\text{logit}_{p})}{\sum_{q \in \text{TopN}(k)} \exp(\text{logit}_q)}
\]

### **Final Volume**
\[
\boxed{
\hat V_{\text{chat\_to\_domain}}(k, p) = 
\hat V_{\text{chat\_keyword}}(k) \times
\frac{\exp(\lambda_1 \text{Vis}_p + \lambda_2 \text{Sem}_p + \lambda_4 \text{Feat}_p)}{\sum_{q \in \text{TopN}(k)} \exp(\lambda_1 \text{Vis}_q + \lambda_2 \text{Sem}_q + \lambda_4 \text{Feat}_q)}
}
\]

---

## 🏗️ Architecture & Implementation

### **Core Classes**

**`ChatGPTVolumeEstimator`** (`model.py`):
- **Purpose**: Main model class with sklearn-like API
- **Methods**: 
  - `fit_transform()`: Fit scaler and compute logits
  - `transform()`: Apply fitted scaler to new data
  - `get_feature_importance()`: Return feature weights
  - `set_lambdas()`: Update parameter weights

**`DataForSEOClient`** (`util/dfs_client.py`):
- **Purpose**: Generic API client for DataForSEO endpoints
- **Methods**:
  - `make_request()`: Generic API call method
  - `fetch_keyword_analysis()`: Comprehensive data collection

**`TextSimilarityClient`** (`util/hf_client.py`):
- **Purpose**: TF-IDF based text similarity computation
- **Methods**:
  - `get_similarities()`: Compute similarities for multiple texts
  - `get_similarity()`: Compute similarity between two texts

### **Data Flow**

1. **Data Collection**: `api_driver.py` → `dfs_client.py` → DataForSEO API
2. **Data Parsing**: `response_parser.py` → Extract SERP and keyword data
3. **Feature Engineering**: `model.py` → Compute visibility, semantic, features
4. **Scaling**: `MinMaxScaler` → Normalize features to [0, 1]
5. **Logit Computation**: Weighted sum of scaled features
6. **Domain Share**: Softmax over all logits
7. **Volume Estimation**: Domain share × AI keyword volume

### **Web Interface Integration**

**Frontend** (`templates/index.html`, `static/scripts.js`):
- **Parameter Input**: Real-time weight adjustment
- **View Toggle**: Normal vs. aggregated results
- **Data Visualization**: Tables, metrics, target domain highlighting

**Backend** (`web_server.py`):
- **API Endpoints**: `/analyze` for data processing
- **Caching**: Smart file management and validation
- **Error Handling**: Comprehensive error reporting

---

## 🔧 Configuration & Tuning

### **Parameter Tuning Guidelines**

**Visibility Weight (λ₁)**:
- **High (2.0+)**: Prioritizes top-ranking results
- **Low (0.5-)**: Reduces rank importance
- **Default (1.5)**: Balanced rank consideration

**Semantic Weight (λ₂)**:
- **High (2.0+)**: Emphasizes content relevance
- **Low (0.5-)**: Reduces content importance
- **Default (1.0)**: Balanced content consideration

**Features Weight (λ₄)**:
- **High (2.0+)**: Prioritizes SERP features
- **Low (0.5-)**: Reduces feature importance
- **Default (1.0)**: Balanced feature consideration

**Alpha (α)**:
- **High (0.3+)**: Slower rank decay
- **Low (0.05-)**: Faster rank decay
- **Default (0.15)**: Moderate decay rate

### **Model Validation**

**Cross-Validation**: Use multiple keyword-domain pairs for validation
**Parameter Sensitivity**: Test different weight combinations
**Feature Importance**: Analyze which features contribute most
**Domain Aggregation**: Handle multiple appearances of same domain

---

## 🚀 Future Enhancements

### **Planned Feature Additions**

**Authority Feature**:
- **Data Source**: Domain backlink data, referring domains
- **Implementation**: Domain authority scoring algorithm
- **API Integration**: Additional DataForSEO endpoints

**Estimated Clicks Feature**:
- **Data Source**: Google Ads search volume, CTR curves
- **Implementation**: Rank-based CTR estimation
- **Computation**: Volume × CTR(rank) calculation

**Advanced Features**:
- **Temperature Parameter**: Softmax temperature control
- **Feature Interactions**: Cross-feature combinations
- **Time Decay**: Temporal relevance scoring
- **User Behavior**: Click-through rate modeling

### **Model Improvements**

**Machine Learning Integration**:
- **Supervised Learning**: Train on labeled data
- **Feature Selection**: Automated feature importance
- **Hyperparameter Optimization**: Grid search for optimal parameters
- **Ensemble Methods**: Multiple model combinations

**Data Enhancements**:
- **Historical Data**: Time-series analysis
- **Competitor Analysis**: Multi-domain comparisons
- **Geographic Targeting**: Location-specific analysis
- **Device Targeting**: Mobile vs. desktop analysis

---

## 📈 Performance Considerations

### **Current Optimizations**

**Memory Efficiency**:
- **TF-IDF**: Lightweight text similarity (vs. heavy ML models)
- **Caching**: Smart file management and reuse
- **Scaling**: MinMaxScaler for feature normalization

**API Efficiency**:
- **Async Processing**: Non-blocking API calls
- **Error Handling**: Automatic retry and recovery
- **Rate Limiting**: Built-in API call management

**Deployment Ready**:
- **512MB Limit**: Optimized for Render.com free tier
- **Python 3.11**: Compatible runtime specification
- **Production Config**: Environment variable handling

### **Scalability**

**Horizontal Scaling**: Stateless design allows multiple instances
**Vertical Scaling**: Memory-efficient algorithms
**Caching Strategy**: Intelligent data reuse
**Error Recovery**: Robust failure handling

---

**Built for production deployment with performance and scalability in mind**