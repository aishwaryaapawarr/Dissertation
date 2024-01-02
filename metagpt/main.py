import asyncio
from roles import UserResearcher, DesignStrategist, ServiceDesigner, ProductManager

async def main():
    user_input = input("Please enter your service design problem: ")

    user_researcher = UserResearcher(name="Alice")
    await user_researcher.run_actions(user_input)
    print(f"Empathy Map: {user_researcher.empathy_map}")

    design_strategist = DesignStrategist(name="Bob")
    await design_strategist.run_actions(user_researcher.interview_output.content)

    service_designer = ServiceDesigner(name="Charlie")
    await service_designer.run_actions(design_strategist.problem_statements_output.content)

    product_manager = ProductManager(name="Fiona")
    await product_manager.run_actions(service_designer.ideation_output.content)
    await product_manager.choose_idea(service_designer.ideation_output.content)

    """interaction_designer = InteractionDesigner(name="Dana")
    await interaction_designer.run_actions(service_designer.ideation_output.content)

    usability_analyst = UsabilityAnalyst(name="Evan")
    await usability_analyst.run_actions(interaction_designer.prototyping_details_output.content)

    print(f"Refinements based on user feedback: {usability_analyst.refinements_output.content}")"""


# Run the async function in the event loop
if __name__ == "__main__":
    asyncio.run(main())
