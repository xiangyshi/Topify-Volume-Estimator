# 🤖 ChatGPT Volume Estimator

A comprehensive tool for estimating ChatGPT query volume potential using SERP data analysis and machine learning models. Features both web UI and CLI interfaces for flexible analysis workflows.

## 📁 Project Structure

```
topify/
├── 📁 data/
│   └── 📁 api_responses/          # DataForSEO API response files (cached)
├── 📁 docs/                       # Documentation
│   ├── README.md                  # This file
│   ├── README_WebUI.md           # Web UI documentation
│   └── FunctionDescription.md    # Model theory and equations
├── 📁 templates/                  # Web UI templates
│   └── index.html                 # Main web interface
├── 📁 static/                     # Web UI assets
│   ├── styles.css                 # CSS styling
│   └── scripts.js                 # JavaScript functionality
├── 📁 util/                       # Utility modules
│   ├── dfs_client.py             # DataForSEO API client
│   ├── hf_client.py              # Text similarity (TF-IDF)
│   └── response_parser.py        # API response parsing
├── 📁 constants/                  # Configuration
│   └── endpoints.py              # API endpoints
├── api_driver.py                 # CLI for API data fetching
├── main.py                       # CLI for volume estimation
├── model.py                      # Core ML model
├── web_server.py                 # Flask web server
├── start.py                      # Production startup script
├── render.yaml                   # Render.com deployment config
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── model.ipynb                   # Jupyter notebook for analysis
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get DataForSEO API Token
1. Sign up at [DataForSEO](https://app.dataforseo.com/api-dashboard)
2. Get your API token from the dashboard
3. Use it in the web UI or CLI

### 3. Choose Your Interface

#### **Web UI (Recommended)**
```bash
python web_server.py
# Open http://localhost:5000
# Enter keyword, domain, and API token
# Adjust parameters and analyze
```

#### **Command Line**
```bash
# Fetch data with API token
python api_driver.py "faceless video ai" "videoinu.com" --token "YOUR_TOKEN"

# Analyze data
python main.py data/api_responses/api_responses_faceless_video_ai_videoinu_com_*.json
```

## 🌐 Web Interface Features

### **Interactive Analysis**
- **Real-time Parameter Tuning**: Adjust weights with sliders
- **View Mode Toggle**: Switch between normal and aggregated views
- **Target Domain Highlighting**: Visual emphasis on query domain
- **API Token Input**: Secure token handling from frontend
- **Responsive Design**: Works on desktop and mobile

### **Data Visualization**
- **Top Performing Domains**: Ranked by AI potential volume
- **Target Domain Summary**: Aggregated statistics for query domain
- **Parameter Impact**: See how weights affect results
- **Export Results**: Copy data for further analysis

## 🎯 Core Features

### **Smart Data Management**
- **Intelligent Caching**: Reuses existing data to avoid duplicate API calls
- **Failure Recovery**: Deletes invalid cache files and refetches data
- **Unique Filenames**: Timestamped files prevent data overwrites
- **Data Validation**: Ensures cached data is valid before use

### **Advanced Volume Estimation Model**
- **5 Feature Components**:
  - **Visibility**: Rank-based visibility scoring with decay
  - **Semantic Relevance**: TF-IDF text similarity
  - **Authority**: Domain authority proxy (currently disabled)
  - **SERP Features**: Featured snippets, people also ask
  - **Estimated Clicks**: Click-through rate modeling (currently disabled)

### **Production Ready**
- **Memory Optimized**: Uses lightweight TF-IDF instead of heavy ML models
- **Error Handling**: Comprehensive error handling and user feedback
- **Deployment Ready**: Configured for Render.com deployment
- **Scalable Architecture**: Modular design for easy extension

## 📊 Model Architecture

### **Logit Computation**
```
logit = λ₁×vis + λ₂×sem + λ₃×auth + λ₄×feat + λ₅×log(est_clicks+1)
```

### **Domain Share Calculation**
```
domain_share = softmax(logit)
```

### **AI Potential Volume**
```
ai_potential_volume = domain_share × ai_search_volume
```

## 🔧 Configuration

### **Default Parameters**
- **Lambda Weights**: `[1.5, 1.0, 0.0, 1.0, 0.0]` (Authority & Clicks disabled)
- **Alpha (Visibility Decay)**: `0.15`
- **Feature Scaling**: MinMaxScaler to `[0, 1]` range
- **Memory Limit**: Optimized for 512MB (Render.com free tier)

### **Customizable Settings**
- **Web UI**: Interactive sliders for active parameters
- **CLI**: Command-line arguments for batch processing
- **API**: Configurable endpoints and retry logic

## 📈 Usage Examples

### **Web UI Analysis**
1. Enter keyword: "faceless video ai"
2. Enter domain: "videoinu.com"
3. Enter DataForSEO API token
4. Adjust parameter weights (Visibility, Semantic, Features)
5. Click "Analyze" to see results
6. Toggle between Normal and Aggregated views

### **CLI Batch Processing**
```bash
# Fetch multiple datasets
python api_driver.py "ai video generator" "runway.com" --token "YOUR_TOKEN"
python api_driver.py "video editing ai" "pictory.ai" --token "YOUR_TOKEN"

# Analyze with custom parameters
python main.py data/api_responses/api_responses_ai_video_generator_runway_com_*.json \
    --weights 2.0 1.5 0.0 1.2 0.0 \
    --alpha 0.2 \
    --top 15
```

## 🚀 Deployment

### **Render.com Deployment**
1. **Push to GitHub**: Repository is ready for deployment
2. **Connect to Render**: Link your GitHub repository
3. **Configure Service**: Use `render.yaml` for automatic setup
4. **Set Environment Variables**: 
   - `FLASK_ENV=production`
   - `PORT=10000` (auto-set by Render)

### **Local Production**
```bash
# Use production startup script
python start.py
```

## 🛠️ Development

### **Module Overview**

#### **`web_server.py`** - Flask Web Server
- **Routes**: `/` (main page), `/analyze` (API endpoint)
- **Features**: Data validation, caching, error handling
- **Production**: Configured for Render.com deployment

#### **`model.py`** - Core ML Model
- **Class**: `ChatGPTVolumeEstimator`
- **Features**: Feature engineering, scaling, logit computation
- **Methods**: `fit_transform()`, `transform()`, parameter management

#### **`api_driver.py`** - Data Collection
- **Purpose**: Fetch data from DataForSEO API
- **Features**: Unique filenames, error handling, validation
- **CLI**: Command-line interface for batch processing

#### **`util/dfs_client.py`** - API Client
- **Purpose**: Generic DataForSEO API client
- **Features**: Async requests, error handling, retry logic
- **Methods**: `make_request()`, `fetch_keyword_analysis()`

#### **`util/hf_client.py`** - Text Similarity
- **Purpose**: TF-IDF based text similarity
- **Features**: Memory efficient, NaN handling
- **Methods**: `get_similarities()`, `get_similarity()`

#### **`util/response_parser.py`** - Data Parsing
- **Purpose**: Parse DataForSEO API responses
- **Features**: Error handling, data validation
- **Methods**: `parse_api_responses_from_dict()`

### **Adding New Features**
1. **Model Components**: Extend `ChatGPTVolumeEstimator` class
2. **API Endpoints**: Add to `constants/endpoints.py`
3. **Web UI**: Modify `templates/index.html` and `static/scripts.js`
4. **Data Processing**: Update `util/response_parser.py`

### **Testing**
```bash
# Test API client
python -c "from util.dfs_client import DataForSEOClient; print('API client OK')"

# Test model
python -c "from model import ChatGPTVolumeEstimator; print('Model OK')"

# Test web server
python web_server.py
```

## 📋 Data Format

### **Input Data Structure**
```json
[
  {
    "endpoint": "ai_keyword_search_volume",
    "data": { "tasks": [...] }
  },
  {
    "endpoint": "serp_google_organic_live_advanced", 
    "data": { "tasks": [...] }
  }
]
```

### **Output Results**
```json
{
  "keyword": "faceless video ai",
  "domain": "videoinu.com",
  "total_volume": 850.0,
  "top_share": 0.298,
  "results": [
    {
      "domain": "faceless.video",
      "rank_absolute": 1,
      "logit": 3.12,
      "domain_share": 0.298,
      "ai_potential_volume": 445.2
    }
  ],
  "normal_results": [...],
  "target_domain_stats": {...}
}
```

## 🔍 Troubleshooting

### **Common Issues**
- **API Errors**: Check DataForSEO credentials and account status
- **Memory Issues**: System optimized for 512MB limit
- **Import Errors**: Ensure all dependencies are installed
- **File Not Found**: Check data file paths in `data/api_responses/`
- **NaN Errors**: System handles missing data gracefully

### **Performance Tips**
- **Use Cached Data**: Web UI automatically reuses existing files
- **Batch Processing**: Use CLI for multiple keyword-domain combinations
- **Parameter Tuning**: Start with default weights, adjust based on results
- **Memory Optimization**: Uses lightweight TF-IDF instead of heavy ML models

## 📚 Additional Resources

- **Web UI Guide**: See `docs/README_WebUI.md`
- **Model Theory**: See `docs/FunctionDescription.md`
- **API Documentation**: DataForSEO API docs
- **Jupyter Analysis**: `model.ipynb` for detailed analysis

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Make changes**: Follow existing code style
4. **Test thoroughly**: Ensure all functionality works
5. **Submit pull request**: Include description of changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for AI-powered SEO analysis**