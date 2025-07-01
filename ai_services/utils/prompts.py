# ai_services/utils/prompts.py
from typing import List


class PromptTemplates:
    """Advanced prompt engineering templates for document analysis"""

    def get_summary_prompt(self, content: str) -> str:
        """Generate comprehensive summary prompt with structured output"""

        return f"""
        You are an expert document analyst. Your task is to create a comprehensive, well-structured summary of the provided text.

        **INSTRUCTIONS:**
        1. Read the entire document carefully
        2. Identify the main themes, key arguments, and important details
        3. Create a summary that captures the essence while being concise
        4. Structure your response as JSON with the specified format
        5. Make the summary actionable and insightful

        **REQUIREMENTS:**
        - Summary should be 150-300 words
        - Include the most critical information
        - Maintain the original tone and intent
        - Be objective and factual
        - Make it accessible to someone who hasn't read the original

        **OUTPUT FORMAT:**
        Return your response as valid JSON:
        {{
            "summary": "Your comprehensive summary here...",
            "main_theme": "Primary theme or topic",
            "tone": "formal/informal/academic/conversational",
            "key_takeaway": "Most important single point"
        }}

        **DOCUMENT TO ANALYZE:**
        {content[:4000]}...

        **RESPONSE:**
        """

    def get_key_points_prompt(self, content: str) -> str:
        """Extract key points with advanced structuring"""

        return f"""
        You are a professional content curator. Extract the most important and actionable key points from this document.

        **ANALYSIS FRAMEWORK:**
        1. Identify core concepts and main arguments
        2. Find supporting evidence and examples
        3. Extract actionable insights
        4. Prioritize by importance and relevance
        5. Ensure each point is self-contained and clear

        **CRITERIA FOR KEY POINTS:**
        - Each point should be specific and concrete
        - Avoid redundancy and overlap
        - Include quantitative data when available
        - Focus on insights that add value
        - Maximum 8-10 key points

        **OUTPUT FORMAT:**
        Return as valid JSON:
        {{
            "key_points": [
                "First key point with specific details",
                "Second key point with context",
                "Third key point with actionable insight",
                "..."
            ],
            "categories": ["category1", "category2", "..."],
            "complexity_level": "beginner/intermediate/advanced"
        }}

        **DOCUMENT:**
        {content[:4000]}...

        **ANALYSIS:**
        """

    def get_qa_cards_prompt(self, content: str, summary: str) -> str:
        """Generate interactive Q&A cards for learning"""

        return f"""
        You are an educational content designer. Create engaging Q&A cards that help users understand and interact with the document content.

        **CARD DESIGN PRINCIPLES:**
        1. Questions should test understanding, not just memory
        2. Include different types of questions (factual, analytical, application)
        3. Answers should be informative but concise
        4. Add difficulty levels for progressive learning
        5. Include follow-up questions to encourage deeper thinking

        **QUESTION TYPES TO INCLUDE:**
        - Factual: "What is...?" "When did...?"
        - Analytical: "Why does...?" "How does...?"
        - Application: "What would happen if...?" "How can this be applied...?"
        - Synthesis: "What's the relationship between...?"

        **OUTPUT FORMAT:**
        Return as valid JSON:
        {{
            "qa_cards": [
                {{
                    "id": 1,
                    "question": "Well-crafted question here?",
                    "answer": "Comprehensive but concise answer",
                    "type": "factual/analytical/application/synthesis",
                    "difficulty": "easy/medium/hard",
                    "follow_up": "Optional follow-up question for deeper learning",
                    "keywords": ["key", "terms", "related"]
                }},
                ...
            ],
            "total_cards": 6,
            "learning_objectives": ["objective1", "objective2", "..."]
        }}

        **DOCUMENT SUMMARY:**
        {summary}

        **FULL CONTENT:**
        {content[:3000]}...

        **Q&A CARDS:**
        """

    def get_chat_prompt(self, question: str, context: List[str], document_summary: str) -> str:
        """Generate contextual chat response"""

        context_text = "\n".join([f"Context {i + 1}: {ctx}" for i, ctx in enumerate(context)])

        return f"""
        You are an intelligent document assistant. Answer the user's question using the provided context and document summary.

        **RESPONSE GUIDELINES:**
        1. Base your answer primarily on the provided context
        2. Be accurate and cite relevant information
        3. If information is not in the context, say so clearly
        4. Provide helpful, detailed responses
        5. Maintain a conversational but professional tone
        6. Include confidence level in your response

        **CONTEXT INFORMATION:**
        {context_text}

        **DOCUMENT SUMMARY:**
        {document_summary}

        **USER QUESTION:**
        {question}

        **RESPONSE FORMAT:**
        Return as valid JSON:
        {{
            "response": "Your detailed answer here...",
            "confidence": 0.85,
            "source_references": ["Context 1", "Context 2"],
            "additional_info": "Any relevant additional context or suggestions",
            "related_questions": ["What about...?", "How does this relate to...?"]
        }}

        **ANSWER:**
        """

    def get_content_analysis_prompt(self, content: str) -> str:
        """Analyze content structure and quality"""

        return f"""
        Analyze this document's structure, quality, and characteristics as a content expert.

        **ANALYSIS DIMENSIONS:**
        1. Content Structure and Organization
        2. Writing Quality and Clarity
        3. Information Density and Depth
        4. Target Audience and Purpose
        5. Strengths and Areas for Improvement

        **OUTPUT FORMAT:**
        {{
            "structure_analysis": {{
                "organization": "Description of how content is organized",
                "flow": "Assessment of logical flow",
                "sections": ["main", "sections", "identified"]
            }},
            "quality_metrics": {{
                "clarity_score": 0.85,
                "depth_score": 0.75,
                "engagement_score": 0.70
            }},
            "audience_analysis": {{
                "target_audience": "Identified target audience",
                "expertise_level": "beginner/intermediate/advanced",
                "purpose": "informational/instructional/persuasive/etc"
            }},
            "recommendations": [
                "Specific improvement suggestion 1",
                "Specific improvement suggestion 2"
            ]
        }}

        **CONTENT:**
        {content[:3000]}...

        **ANALYSIS:**
        """

    def get_sentiment_analysis_prompt(self, content: str) -> str:
        """Analyze sentiment and emotional tone"""

        return f"""
        Analyze the emotional tone and sentiment of this document.

        **ANALYSIS FRAMEWORK:**
        - Overall sentiment (positive/negative/neutral)
        - Emotional tone and mood
        - Confidence level in statements
        - Bias indicators
        - Persuasive techniques used

        **OUTPUT FORMAT:**
        {{
            "sentiment": {{
                "overall": "positive/negative/neutral",
                "confidence": 0.85,
                "emotional_tone": "descriptive tone analysis"
            }},
            "key_emotions": ["emotion1", "emotion2"],
            "bias_indicators": ["indicator1", "indicator2"],
            "persuasive_elements": ["element1", "element2"]
        }}

        **CONTENT:**
        {content[:2000]}...

        **SENTIMENT ANALYSIS:**
        """

    def get_roadmap_prompt(self, goal: str, context_chunks: list) -> str:
        """Build a comprehensive prompt for roadmap generation with validation"""

        context_text = "\n\n".join([
            f"Context {i + 1}:\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        ])

        return f"""You are an expert learning advisor that creates personalized learning roadmaps.

IMPORTANT INSTRUCTIONS:
1. ONLY create learning roadmaps for genuine learning goals and educational queries
2. If the user query is NOT about learning, studying, or skill development, politely decline and ask for a learning-related query
3. Look for learning intent in queries like: "learn X", "how to become Y", "guide to Z", "roadmap for A", etc.
4. If the query is just a greeting, casual chat, or unclear request, do NOT create a roadmap

USER QUERY: "{goal}"

RELEVANT CONTEXT:
{context_text}

TASK:
First, determine if this is a genuine learning request. If it's not clearly about learning or skill development, respond with:
"I'm designed to help create learning roadmaps. Please ask me about something you'd like to learn, such as:
- 'I want to learn Python programming'
- 'How to become a web developer'  
- 'Machine learning roadmap for beginners'
- 'Guide to digital marketing'

What would you like to learn?"

If it IS a learning request, create a comprehensive learning roadmap with:

1. **Learning Goal**: Clearly state what the user wants to achieve
2. **Prerequisites**: What knowledge/skills are needed before starting
3. **Learning Path**: Step-by-step phases with:
   - Phase name and duration estimate
   - Key concepts to learn
   - Practical projects or exercises
   - Recommended resources
4. **Milestones**: How to measure progress
5. **Next Steps**: What to do after completing this roadmap

Make the roadmap:
- Specific and actionable
- Realistic with time estimates
- Progressive (building from basics to advanced)
- Include both theory and hands-on practice
- Tailored to the user's apparent skill level

Use the provided context to enhance your recommendations with specific resources and detailed guidance.

RESPONSE:"""

    def get_query_classification_prompt(self, query: str) -> str:
        """Build a prompt to classify if a query is learning-related"""

        return f"""You are a query classifier. Determine if the following user input is a request for learning guidance or educational content.

USER INPUT: "{query}"

Respond with only one of these options:
- "LEARNING" if the query is about learning, studying, education, skill development, career guidance, or asking for tutorials/roadmaps
- "NOT_LEARNING" if the query is a greeting, casual conversation, unclear request, or not related to learning

Examples of LEARNING queries:
- "I want to learn Python"
- "How to become a data scientist"
- "JavaScript"
- "Machine learning roadmap"
- "Guide to web development"

Examples of NOT_LEARNING queries:
- "Hi"
- "Hello"
- "Test"
- "Thanks"
- "Random text"

Classification:"""
        """Analyze sentiment and emotional tone"""

        return f"""
        Analyze the emotional tone and sentiment of this document.

        **ANALYSIS FRAMEWORK:**
        - Overall sentiment (positive/negative/neutral)
        - Emotional tone and mood
        - Confidence level in statements
        - Bias indicators
        - Persuasive techniques used

        **OUTPUT FORMAT:**
        {{
            "sentiment": {{
                "overall": "positive/negative/neutral",
                "confidence": 0.85,
                "emotional_tone": "descriptive tone analysis"
            }},
            "key_emotions": ["emotion1", "emotion2"],
            "bias_indicators": ["indicator1", "indicator2"],
            "persuasive_elements": ["element1", "element2"]
        }}

        **CONTENT:**
        {content[:2000]}...

        **SENTIMENT ANALYSIS:**
        """
