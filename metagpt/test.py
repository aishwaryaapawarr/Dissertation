# DataAnalystRole.py
from metagpt.actions import Action
from llm import ai_func
import asyncio
# This template can be modified based on how you want the LLM to respond.
PROMPT_TEMPLATE = """
Data Analyst Role:
{context}

# Task: Analyze the given data and provide insights.
# Note: Make sure to validate data integrity before analysis.
"""


class DataAnalystAction(Action):
    async def run(self, context):
        prompt = """
        Data Analyst Role:
        {context}

        # Task: Analyze the given data and provide insights.
        # Note: Make sure to validate data integrity before analysis.
        """.format(context=context)
        analysis_result = await ai_func(prompt)
        return analysis_result


async def handle_data_analysis_query(user_query: str):
    data_analyst_action = DataAnalystAction(name="DataAnalysis", context=user_query)
    analysis_result = await data_analyst_action.run(user_query)
    return analysis_result


# Entry point for the script
async def main(user_query: str):
    result = await handle_data_analysis_query(user_query)
    print(f"Analysis Result: {result}")


# User input outside of async function
user_input = input("Please enter your data analysis query: ")

# Run the async function in the event loop
if __name__ == "__main__":
    asyncio.run(main(user_input))
    