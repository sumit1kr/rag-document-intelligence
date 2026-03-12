# rag-doc-analyzer

A robust Document Q&A Assistant that uses Large Language Models (LLMs) to process natural language queries and retrieve relevant information from large unstructured documents such as policy documents, contracts, and emails.

## 🚀 Features

### Document Processing
- **PDF Files**: Full text extraction with PyPDF2 and PyMuPDF fallback
- **Word Documents**: Support for .docx and .doc files
- **Email Files**: Processing of .eml and .msg files
- **Text Files**: Plain text file support
- **Images**: OCR support for PNG, JPG, JPEG files
- **Multi-format**: Process multiple file types simultaneously

### Query Processing
- **Natural Language**: Handle vague, incomplete, or plain English queries
- **Enhanced Parsing**: Extract age, gender, procedure, location, policy duration, medical conditions, urgency
- **Query Validation**: Validate queries and provide suggestions for improvement
- **Semantic Expansion**: Expand queries with synonyms and related terms for better retrieval
- **Query Disambiguation**: Resolve ambiguities and provide clarifications
- **Multi-Hop Reasoning**: Chain multiple reasoning steps for comprehensive analysis
- **Semantic Search**: Use vector embeddings for intelligent document retrieval
- **Decision Extraction**: Automatically extract approval/rejection status and amounts

### Output & Analysis
- **Structured JSON**: Consistent, interpretable responses with clause mapping
- **Evidence Mapping**: Link decisions to specific document clauses with relevance scoring
- **Clause Extraction**: Automatic identification of policy sections and decision impacts
- **Decision Confidence**: Calculate confidence scores based on evidence strength
- **Audit Trail**: Track decision factors and reasoning
- **Multi-tab Interface**: Answer, Decision Summary, and Debug views with JSON output

## 📋 Supported File Types

| Format | Extension | Description |
|--------|-----------|-------------|
| PDF | `.pdf` | Policy documents, contracts, reports |
| Word | `.docx`, `.doc` | Microsoft Word documents |
| Email | `.eml`, `.msg` | Email messages and Outlook files |
| Text | `.txt` | Plain text documents |
| Images | `.png`, `.jpg`, `.jpeg` | Scanned documents with OCR |

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/blackpanther093/rag-doc-analyzer
   cd hackrx-rag-doc-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the `myenv` directory with:
   ```
   PINECONE_API_KEY=your_pinecone_key
   GROQ_API_KEY=your_groq_key
   HUGGINGFACE_API_KEY=your_huggingface_key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

## 🎯 Usage

1. **Upload Documents**: Select PDF, Word, email, or text files
2. **Enable OCR**: For image files if needed
3. **Process & Index**: Extract and index document content
4. **Ask Questions**: Use natural language queries like "46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
5. **Review Results**: Check the Answer, Decision Summary, and Debug tabs

## 🔧 Architecture

- **File Processing**: Multi-format document extraction
- **Text Processing**: Cleaning, chunking, and normalization
- **Vector Storage**: Pinecone for semantic search
- **Query Interpretation**: spaCy + regex for structured parsing
- **LLM Integration**: Groq's Llama 3.3-70B for reasoning
- **Web Interface**: Gradio for beautiful, responsive UI

## 📊 Sample Queries

- "46M, knee surgery, Pune, 3-month policy"
- "Female patient, 35 years old, cataract surgery in Mumbai"
- "Angioplasty procedure for 50-year-old male"
- "IVF treatment coverage for 28-year-old female"

## 🎨 Sample Response

```json
{
  "query": {
    "original": "46-year-old male, knee surgery in Pune, 3-month-old insurance policy",
    "parsed": {
      "original_query": "46-year-old male, knee surgery in Pune, 3-month-old insurance policy",
      "query_type": "insurance_claim",
      "extracted_entities": {}
    }
  },
  "decision": {
    "status": "Approved",
    "amount": "₹50000",
    "confidence": 0.85
  },
  "justification": "Based on the policy documents, knee surgery is covered for patients aged 18-65...",
  "evidence": {
    "clauses": [
      {
        "clause_id": "3.2",
        "clause_text": "Section 3.2: Knee surgery is covered under the policy for patients aged 18-65...",
        "clause_type": "approval",
        "decision_impact": "positive",
        "relevance_score": 0.95,
        "decision_relevance": "high",
        "evidence_strength": "strong",
        "summary": "Section 3.2: Knee surgery is covered under the policy for patients aged 18-65..."
      }
    ],
    "total_clauses": 4,
    "supporting_clauses": 2,
    "opposing_clauses": 0
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00",
    "model_used": "llama-3.3-70b-versatile"
  }
}
```

## 🔍 Testing

### File Processing Test
Run the test script to verify file processing:
```bash
python test_file_processing.py
```

### Structured Response Test
Run the test script to verify structured JSON response functionality:
```bash
python test_structured_response.py
```

### Enhanced Query Processing Test
Run the test script to verify enhanced query processing and multi-hop reasoning:
```bash
python test_enhanced_query_processing.py
```

## 📝 License

This project is licensed under the MIT License.
