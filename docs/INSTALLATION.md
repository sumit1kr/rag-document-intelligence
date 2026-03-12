# Installation Guide

## System Requirements

### Hardware Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **Network**: Stable internet connection for API calls

### Software Requirements
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **npm/pnpm**: Latest version
- **Git**: For repository cloning

## Step-by-Step Installation

### 1. Environment Setup

#### Clone Repository
\`\`\`bash
git clone <repository-url>
cd hackrx-rag-doc-qa
\`\`\`

#### Create Virtual Environment
\`\`\`bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
\`\`\`

### 2. Python Dependencies

#### Install Core Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

#### Install Optional Dependencies
\`\`\`bash
# For enhanced OCR support
pip install pytesseract

# For advanced NLP features
python -m spacy download en_core_web_sm
\`\`\`

### 3. Node.js Dependencies

#### Install Frontend Dependencies
\`\`\`bash
npm install
# or
pnpm install
\`\`\`

### 4. API Keys Configuration

#### Required API Keys
1. **Groq API Key**: For LLM processing
   - Sign up at [Groq Console](https://console.groq.com)
   - Create API key in dashboard

2. **Pinecone API Key**: For vector database
   - Sign up at [Pinecone](https://www.pinecone.io)
   - Create index and get API key

3. **HuggingFace API Key**: For embeddings
   - Sign up at [HuggingFace](https://huggingface.co)
   - Create access token in settings

#### Environment Variables Setup
Create `.env` file in project root:
\`\`\`bash
# API Keys
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Pinecone Configuration
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_index_name

# Optional: Custom configurations
MODEL_TEMPERATURE=0.1
MAX_TOKENS=4000
CACHE_TTL=3600
\`\`\`

### 5. Database Setup (Optional)

#### Pinecone Index Creation
\`\`\`python
import pinecone

# Initialize Pinecone
pinecone.init(
    api_key="your_api_key",
    environment="your_environment"
)

# Create index
pinecone.create_index(
    name="hackrx-doc-qa",
    dimension=384,  # For sentence-transformers
    metric="cosine"
)
\`\`\`

### 6. System Initialization

#### Initialize Application State
\`\`\`bash
python -c "from src.utils.app_state import app_state; app_state.initialize()"
\`\`\`

#### Verify Installation
\`\`\`bash
python tests/test_comprehensive_features.py
\`\`\`

### 7. Configuration Verification

#### Test API Connections
\`\`\`bash
python -c "
from src.api.setup_api import APIKeyManager
config = APIKeyManager.load_and_validate()
print('Configuration loaded successfully!')
"
\`\`\`

## Platform-Specific Instructions

### Windows Installation

#### Prerequisites
\`\`\`bash
# Install Python from python.org
# Install Node.js from nodejs.org
# Install Git from git-scm.com

# Install Visual C++ Build Tools (for some Python packages)
# Download from Microsoft Visual Studio website
\`\`\`

#### Tesseract OCR (Optional)
\`\`\`bash
# Download Tesseract installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Add to PATH environment variable
# Default location: C:\Program Files\Tesseract-OCR
\`\`\`

### macOS Installation

#### Prerequisites using Homebrew
\`\`\`bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python node git tesseract
\`\`\`

### Linux Installation

#### Ubuntu/Debian
\`\`\`bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install python3 python3-pip nodejs npm git tesseract-ocr

# Install Python virtual environment
sudo apt install python3-venv
\`\`\`

#### CentOS/RHEL
\`\`\`bash
# Install EPEL repository
sudo yum install epel-release

# Install dependencies
sudo yum install python3 python3-pip nodejs npm git tesseract

# Install development tools
sudo yum groupinstall "Development Tools"
\`\`\`

## Troubleshooting

### Common Issues

#### 1. Import Errors
\`\`\`bash
# If you get import errors, ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
\`\`\`

#### 2. API Key Issues
\`\`\`bash
# Verify API keys are set
python -c "import os; print('GROQ_API_KEY:', bool(os.getenv('GROQ_API_KEY')))"

# Test API connections
python tests/test_webhook.py
\`\`\`

#### 3. Memory Issues
\`\`\`bash
# If you encounter memory issues, reduce batch size
# Edit config/models/model_config.json:
{
  "max_tokens": 2000,
  "batch_size": 5
}
\`\`\`

#### 4. Port Conflicts
\`\`\`bash
# If port 7860 is in use, specify different port
python app.py --server-port 8080

# For API server
python -c "api.run(port=5001)"
\`\`\`

### Performance Optimization

#### 1. Enable Caching
\`\`\`python
# Ensure cache is enabled in config
cache_config = {
    "enabled": True,
    "ttl": 3600,
    "max_size": 1000
}
\`\`\`

#### 2. Optimize Model Settings
\`\`\`json
{
  "temperature": 0.1,
  "max_tokens": 2000,
  "top_p": 0.9
}
\`\`\`

## Verification Steps

### 1. Test Core Functionality
\`\`\`bash
python tests/test_enhanced_query_processing.py
\`\`\`

### 2. Test File Processing
\`\`\`bash
python tests/test_file_processing.py
\`\`\`

### 3. Test API Endpoints
\`\`\`bash
python tests/test_webhook.py
\`\`\`

### 4. Test Web Interface
\`\`\`bash
python app.py
# Open http://localhost:7860 in browser
\`\`\`

## Next Steps

After successful installation:

1. **Read the User Guide**: `docs/USER_GUIDE.md`
2. **Review API Documentation**: `docs/API.md`
3. **Check Configuration Options**: `docs/CONFIGURATION.md`
4. **Explore Examples**: `examples/` directory

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in the application
3. Create an issue in the repository
4. Check existing issues for solutions

---

**Installation complete! You're ready to use the HackRX RAG Document Q&A System.**
