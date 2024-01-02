template0 = {
    "json": {
        "PROMPT_TEMPLATE": """
        Create a detailed empathy map based on the following interview output.
        Structure the empathy map into four key areas: Thoughts, Feelings, Pain Points, Goals.
        Do NOT name who said what in the thoughts, feelings, pain points and goals section. Write generalised short points.

        Interview Output:
        {context}
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        {
            "Empathy Map": {
                "Thoughts": "...",
                "Feelings": "...",
                "Pain Points": "...",
                "Goals": "..."
            }
        }
        [/CONTENT]
        """
    }
}

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
        Given a service design problem:
        {service_design_problem}

        Conduct interviews with participants from the following categories: {selected_participants}.
        Focus the interviews on gathering insights relevant to various aspects of the service design problem and then generate a summarised paragraph.
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        [/CONTENT]
        """
    }
}

templates1 = {
    "json": {
        "PROMPT_TEMPLATE": """
        Identify and list the key insights as short bullet points from the following user interview transcript, providing only the headings for each point without further explanation:
        Focus on capturing:
        - Main difficulties encountered by the user
        - Frustrations the user has with the service
        - User's suggestions for improvements
        Interview Transcript:
        {context}
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        {
            "Summarized Insights": "..."
            ...
        }
        [/CONTENT]
        """
    }
}

templates2 = {
    "json": {
        "PROMPT_TEMPLATE": """
        Based on the following user insights:
        {context}

        Transform the following user insights into 5 concise problem statements formatted as an ordered list of bullet points. Each point should briefly describe a unique problem identified during the interview and identify the opportunities for service design improvement.
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        {
            "Problem Statements": [
                "Problem 1: ...",
                "Problem 2: ...",
                ...
            ]
        }
        [/CONTENT]
        """
    }
}

templates3 = {
    "json": {
        "PROMPT_TEMPLATE": """
        Given the following problem statements:
        {context}

        Generate a series of creative ideas that could potentially solve these problems. For each idea, provide a short explanation of why it is a good solution, considering its feasibility, impact, and alignment with user needs and service goals. The ideas should be short, concise, and accompanied by a rationale.

        Example:
        Idea: [Idea description]
        Reason: [Explanation why it's a good solution]
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        {
            "Ideation Results": [
                {
                    "Idea": "...",
                    "Reason": "..."
                },
                {
                    "Idea": "...",
                    "Reason": "..."
                },
                ...
            ]
        }
        [/CONTENT]
        """
    }
}

templates4 = {
    "json": {
        "PROMPT_TEMPLATE": """
        From the following ideas:
        {context}

        Select the most doable and promising ideas and outline a plan for prototyping them in a brief paragraph.
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        {
            "Prototyping Plan": "..."
            ...
        }
        [/CONTENT]
        """
    }
}

templates5 = {
    "json": {
        "PROMPT_TEMPLATE": """
        Based on the following ideation results:
        {context}

        Develop a feature plan that aligns with both user needs and business goals. The plan should prioritize features, outline their potential impact, and suggest a roadmap for implementation. Include reasons for feature prioritization and expected outcomes.

        Example:
        Feature: [Feature description]
        Reason for Prioritization: [Reason]
        Expected Outcome: [Outcome]
        """,
        "FORMAT_EXAMPLE": """
        [CONTENT]
        {
            "Feature Plan": [
                {
                    "Feature": "...",
                    "Reason for Prioritization": "...",
                    "Expected Outcome": "..."
                },
                ...
            ]
        }
        [/CONTENT]
        """
    }
}

