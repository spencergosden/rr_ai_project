import json
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import re

load_dotenv()

class NVDAEarningsProcessor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_KEY'))
        self.data_dir = Path("data")
        self.nlp_dir = self.data_dir / "NLP"
        self.nlp_dir.mkdir(parents=True, exist_ok=True)
    
    def load_transcripts(self):
        """Load and parse transcript files"""
        transcripts = []
        for file in (self.data_dir / "transcripts").glob("*.txt"):
            filename = file.stem

            if ' ' in filename:
                first_part = filename.split('_')[0]
                if ' ' in first_part:
                    quarter, year = first_part.split(' ', 1)
                else:
                    quarter, year = "Q1", "2024"
            else:
                quarter, year = "Q1", "2024"
            
            with open(file, 'r', encoding='utf-8') as f:
                transcripts.append({
                    "transcript": f.read(),
                    "quarter": quarter,
                    "year": year,
                    "filename": file.stem
                })
        return sorted(transcripts, key=lambda x: (x['year'], x['quarter']))
    
    def _extract_json(self, text):
        """Extract JSON from Claude response"""
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")
        
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            start = text.find('{')
            if start == -1:
                raise ValueError("No JSON found")
            
            brace_count = 0
            for i, char in enumerate(text[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return json.loads(text[start:i+1])
            raise ValueError("No complete JSON found")
    
    def _call_claude(self, prompt, max_tokens=2000):
        """Make API call to Claude"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._extract_json(response.content[0].text)
    
    def analyze_transcript(self, data):
        """Analyze single transcript"""
        transcript = data['transcript']
        
        prompt = f"""Analyze NVDA {data['quarter']} {data['year']} earnings call.

    First, identify and split the transcript into:
    1. Management presentation/prepared remarks
    2. Q&A session with analysts

    Then analyze each section separately.

    TRANSCRIPT:
    {transcript}

    Return ONLY JSON:
    {{
        "management_sentiment": {{"score": "very positive/positive/neutral/negative/very negative", "confidence": 0.85, "reasoning": "brief explanation", "tone": "word", "tone_score": 85}},
        "qa_sentiment": {{"score": "very positive/positive/neutral/negative/very negative", "confidence": 0.85, "reasoning": "brief explanation"}},
        "strategic_focuses": [{{"theme": "Data Center Growth", "description": "expanding capacity", "mentions": 5, "priority": "high"}}],
        "tone_indicators": {{"confidence": "high/medium/low", "defensive_topics": [], "outlook": "optimistic/cautious/pessimistic"}},
        "key_metrics": [],
        "risks": []
    }}"""
        
        try:
            result = self._call_claude(prompt)
            result.update({"quarter": data['quarter'], "year": data['year']})
            return result
        except Exception as e:
            return {"error": str(e), "quarter": data['quarter'], "year": data['year']}
    
    def compare_quarters(self, results):
        """Generate trend analysis"""
        valid_results = [r for r in results if 'error' not in r]
        if len(valid_results) < 2:
            return {"error": "Insufficient data for comparison"}
        
        prompt = f"""Compare NVDA quarterly trends. Return ONLY JSON:

{json.dumps(valid_results, indent=2)[:8000]}

{{
    "sentiment_trends": {{"management": "improving/declining/stable", "qa": "improving/declining/stable", "inflection_points": []}},
    "strategic_evolution": [],
    "highlights": {{"most_positive": "", "most_defensive": "", "biggest_shift": ""}}
}}"""
        
        try:
            return self._call_claude(prompt, 1500)
        except Exception as e:
            return {"error": f"Comparison failed: {str(e)}"}
    
    def export_to_csv(self, complete_analysis):
        """Export results to CSV files"""
        valid_results = [q for q in complete_analysis['quarterly_results'] if 'error' not in q]
        if not valid_results:
            return 0
        
        # Quarterly summary
        quarterly_data = [{
            'quarter': q.get('quarter', ''),
            'year': q.get('year', ''),
            'mgmt_sentiment_score': q.get('management_sentiment', {}).get('score', ''),
            'mgmt_sentiment_confidence': q.get('management_sentiment', {}).get('confidence', ''),
            'mgmt_reasoning': q.get('management_sentiment', {}).get('reasoning', ''),
            'qa_sentiment_score': q.get('qa_sentiment', {}).get('score', ''),
            'qa_sentiment_confidence': q.get('qa_sentiment', {}).get('confidence', ''),
            'qa_reasoning': q.get('qa_sentiment', {}).get('reasoning', ''),
            'confidence_level': q.get('tone_indicators', {}).get('confidence', ''),
            'outlook': q.get('tone_indicators', {}).get('outlook', ''),
            'num_strategic_focuses': len(q.get('strategic_focuses', [])),
            'num_risks': len(q.get('risks', [])),
            'num_key_metrics': len(q.get('key_metrics', [])),
            'defensive_topics_count': len(q.get('tone_indicators', {}).get('defensive_topics', [])),
            'tone': q.get('management_sentiment', {}).get('tone', ''),
            'tone_score': q.get('management_sentiment', {}).get('tone_score', 0)
        } for q in valid_results]
        
        pd.DataFrame(quarterly_data).to_csv(self.nlp_dir / "nvda_quarterly_summary.csv", index=False)
        
        # Export normalized data
        for name, field in [("strategic_focuses", "strategic_focuses"), ("risks", "risks"), ("key_metrics", "key_metrics")]:
            data = []
            for q in valid_results:
                quarter, year = q.get('quarter', ''), q.get('year', '')
                
                if name == "strategic_focuses":
                    for item in q.get(field, []):
                        data.append({
                            'quarter': quarter, 'year': year,
                            'theme': item.get('theme', ''),
                            'description': item.get('description', ''),
                            'mentions': item.get('mentions', 0),
                            'priority': item.get('priority', '')
                        })
                else:
                    for item in q.get(field, []):
                        data.append({
                            'quarter': quarter, 'year': year,
                            field[:-1]: item 
                        })
            
            if data:
                pd.DataFrame(data).to_csv(self.nlp_dir / f"nvda_{name}.csv", index=False)
        
        return len(quarterly_data)
    
    def debug_transcripts(self):
        """Debug transcript loading"""
        transcripts = self.load_transcripts()
        print(f"\nFound {len(transcripts)} transcripts:")
        for t in transcripts:
            print(f"- {t['filename']}: {t['quarter']} {t['year']}")
    
    def process_all(self):
        """Main processing pipeline"""
        transcripts = self.load_transcripts()
        print(f"Processing {len(transcripts)} transcripts...")
        
        if not transcripts:
            return None
        
        results = []
        for i, transcript in enumerate(transcripts, 1):
            print(f"{i}/{len(transcripts)}: {transcript['quarter']} {transcript['year']}")
            
            result = self.analyze_transcript(transcript)
            results.append(result)
            
            # Save individual analysis
            with open(self.nlp_dir / f"{transcript['filename']}_analysis.json", 'w') as f:
                json.dump(result, f, indent=2)
            
            print("Processed." if 'error' not in result else f"Error: {result['error']}")
        
        # Generate trends and complete analysis
        trends = self.compare_quarters(results)
        complete_analysis = {
            "quarterly_results": results,
            "trend_analysis": trends,
            "summary": {
                "quarters_analyzed": len(results),
                "successful_analyses": len([r for r in results if 'error' not in r]),
                "company": "NVDA"
            }
        }
        
        with open(self.nlp_dir / "nvda_complete_analysis.json", 'w') as f:
            json.dump(complete_analysis, f, indent=2)
        
        csv_count = self.export_to_csv(complete_analysis)
        
        print(f"\nComplete: {complete_analysis['summary']['successful_analyses']}/{len(results)} successful, {csv_count} CSV records")
        return complete_analysis

if __name__ == "__main__":
    processor = NVDAEarningsProcessor()
    processor.process_all()