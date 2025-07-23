# NVIDIA Earnings Analysis Dashboard

A comprehensive Docker-containerized application for analyzing NVIDIA's earnings call transcripts with AI-powered sentiment analysis, strategic focus extraction, and interactive visualizations.

## Key Features

- Interactive Streamlit dashboard for exploring quarterly earnings data
- Automated web scraping of earnings call transcripts
- AI-powered NLP analysis using Anthropic's Claude API
- Fully containerized with Docker for easy deployment
- Sentiment scoring for management and Q&A sections
- Strategic focus and theme extraction
- Management tone analysis and trending
- Pre-loaded with analyzed data from Q1-Q4 2025

## Quick Start

Run the dashboard with a single command:

```bash
docker run -p 8501:8501 nvidia-analysis
```

Visit http://localhost:8501 to view the dashboard.

## Installation

### Prerequisites

- Docker Desktop installed and running
- (Optional) Anthropic API key for transcript processing

### Build from Source

```bash
git clone <repository-url>
cd nvidia-earnings-analysis
docker build -t nvidia-analysis .
```

### Using Docker Compose

```bash
docker-compose up
```

## Usage Modes

The container supports three operation modes:

### Dashboard Mode (Default)

View the interactive analytics dashboard:

```bash
docker run -p 8501:8501 nvidia-analysis
# or 
docker run -p 8501:8501 nvidia-analysis dashboard
```

### Collection Mode

Scrape new earnings call transcripts from the web:

```bash
docker run -v $(pwd)/data:/app/data nvidia-analysis collect
```

### Processing Mode

Analyze transcripts with AI (requires Anthropic API key):

```bash
export ANTHROPIC_KEY="YOUR KEY HERE"
docker run -e ANTHROPIC_KEY=$ANTHROPIC_KEY -v $(pwd)/data:/app/data nvidia-analysis process
```

### Help

View available commands and options:

```bash
docker run nvidia-analysis help
```

## Configuration

### Using Docker Compose

Create a `.env` file with your configuration:

```bash
ANTHROPIC_KEY=YOUR_KEY_HERE
STREAMLIT_PORT=8501
```

Then run:

```bash
docker-compose up
```

## Dashboard Sections

### Overview
- Key metrics summary
- Total quarters analyzed
- Average confidence scores
- Latest sentiment indicators

### Transcripts
- Full transcript viewer
- Search functionality
- Word count statistics
- Quarter selection dropdown

### Sentiment Analysis
- Management sentiment trends over time
- Q&A sentiment comparison
- Confidence level visualization
- Detailed quarterly breakdowns with reasoning

### Strategic Focuses
- Sunburst chart of focus areas by quarter
- Theme priority analysis
- Mention frequency tracking
- Filterable data table

### Tone Trends
- Management tone scoring (0-100 scale)
- Quarterly tone type classification
- Confidence level tracking
- Historical trend visualization

## Troubleshooting

### Common Error Messages

**"about:blank" in browser**: This is typically a Streamlit configuration issue. The container is configured to handle this automatically.

**"Cannot connect to Docker daemon"**: Docker Desktop needs to be running. Start it from Applications.

**"No such file or directory"**: Ensure you're in the correct directory when building or running commands.

**"API key not found"**: Set the ANTHROPIC_KEY environment variable for processing mode.