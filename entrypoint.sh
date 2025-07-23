#!/bin/bash

# NVIDIA Earnings Analysis Container Entrypoint
# Smart startup script for different operation modes

set -e

# Function to display usage
show_help() {
    echo "NVIDIA Earnings Analysis Docker Container"
    echo ""
    echo "Usage: docker run [options] nvidia-analysis [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dashboard     Start the Streamlit dashboard (default)"
    echo "  collect       Run transcript collection"
    echo "  process       Run transcript processing (requires ANTHROPIC_KEY)"
    echo "  bash          Start bash shell"
    echo "  help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ANTHROPIC_KEY    Required for transcript processing"
    echo "  STREAMLIT_PORT   Dashboard port (default: 8501)"
    echo ""
    echo "Examples:"
    echo "  docker run -p 8501:8501 nvidia-analysis"
    echo "  docker run -e ANTHROPIC_KEY=sk-... nvidia-analysis process"
    echo "  docker run nvidia-analysis collect"
}

# Function to validate environment for processing
validate_processing_env() {
    if [ -z "$ANTHROPIC_KEY" ]; then
        echo "Error: ANTHROPIC_KEY environment variable is required for processing mode"
        echo "   Set it with: docker run -e ANTHROPIC_KEY=your_key_here nvidia-analysis process"
        exit 1
    fi
}

# Function to check if data directory exists and has content
check_data_directory() {
    if [ ! -d "data" ]; then
        echo "Warning: data directory not found. Creating..."
        mkdir -p data/transcripts data/NLP
    fi
    
    if [ ! "$(ls -A data/transcripts 2>/dev/null)" ]; then
        echo "No transcript files found in data/transcripts/"
        echo "Run 'collect' mode first to gather transcript data"
    fi
}

# Main execution logic
main() {
    local command=${1:-dashboard}
    
    echo "Starting NVIDIA Earnings Analysis Container..."
    echo "Mode: $command"
    
    case "$command" in
        "dashboard"|"")
            echo "Starting Streamlit dashboard on port $STREAMLIT_PORT..."
            check_data_directory
            exec streamlit run Frontend.py \
                --server.port=$STREAMLIT_PORT \
                --server.address=0.0.0.0 \
                --server.headless=true \
                --browser.serverAddress=localhost \
                --server.enableCORS=false \
                --server.enableXsrfProtection=false
            ;;
        
        "collect")
            echo "Starting transcript collection..."
            check_data_directory
            exec python Transcript_Collection.py
            ;;
        
        "process")
            echo "Starting transcript processing with AI..."
            validate_processing_env
            check_data_directory
            exec python Transcript_Processing.py
            ;;
        
        "bash")
            echo "Starting bash shell..."
            exec bash
            ;;
        
        "help"|"--help"|"-h")
            show_help
            exit 0
            ;;
        
        *)
            echo "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Handle signals gracefully
trap 'echo "Shutting down gracefully..."; exit 0' SIGTERM SIGINT

# Run main function with all arguments
main "$@"