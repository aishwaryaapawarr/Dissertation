import asyncio
from PIL import Image, ImageDraw, ImageFont
from metagpt.roles import Role
import shutil
from pathlib import Path
from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.llm import ai_func
from pydantic import BaseModel
import textwrap
from actions import UserInterview, CreateEmpathyMap, SummarizeInsights, DefineProblemStatements, IdeateSolutions, PrototypeSolutions, DevelopFeaturePlan
from metagpt.main_role import Role

class UserResearcher(Role):
    """
    Represents a User Researcher role in a service design process.

    Attributes:
        name (str): Name of the user researcher.
        profile (str): Role profile, default is 'User Researcher'.
        goal (str): Primary goal or responsibility of the user researcher.
        constraints (str): Constraints or guidelines for the user researcher.
    """

    def __init__(
        self,
        name: str = "Alice",
        profile: str = "User Researcher",
        goal: str = "Understand user needs and behaviors",
        constraints: str = "Follow ethical guidelines for user interviews",
    ) -> None:
        """Initializes the User Researcher with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self.empathy_map = None
        self.interview_output = None

    async def run_actions(self, service_design_problem):
        user_interview = UserInterview(name="User Interview", context=service_design_problem, llm=ai_func)
        self.interview_output = await user_interview.run(service_design_problem)
        create_empathy_map = CreateEmpathyMap(name="Create Empathy Map", context=self.interview_output.content,
                                              llm=ai_func)
        empathy_map_output = await create_empathy_map.run(self.interview_output.content)
        self.empathy_map = empathy_map_output.content  # Extracting content from ActionOutput

class DesignStrategist(Role):
    """
    Represents a Design Strategist role in the Define stage of a service design process.
    """
    def __init__(
        self,
        name: str = "Bob",
        profile: str = "Design Strategist",
        goal: str = "Define clear problem statements based on user insights",
    ) -> None:
        super().__init__(name, profile, goal)
        self.problem_statements_output = None

    async def run_actions(self, user_insights):
        summarize_insights = SummarizeInsights(name="summarised insights", context=user_insights, llm=ai_func)
        define_problem_statements = DefineProblemStatements()

        summarized_insights = await summarize_insights.run(user_insights)
        self.problem_statements_output = await define_problem_statements.run(summarized_insights.content)

class ServiceDesigner(Role):
    """
    Represents a Service Designer role in the Ideation and Prototyping stages of a service design process.

    Attributes:
        name (str): Name of the service designer.
        profile (str): Role profile, default is 'Service Designer'.
        goal (str): Primary goal or responsibility of the service designer.
    """

    def __init__(
            self,
            name: str = "Charlie",
            profile: str = "Service Designer",
            goal: str = "Develop and prototype solutions based on defined problems and insights",
    ) -> None:
        """Initializes the Service Designer with given attributes."""
        super().__init__(name, profile, goal)
        self.prototyping_output = None
        self.ideation_output = None

    async def run_actions(self, problem_statements):
        self.ideation_output = await IdeateSolutions().run(problem_statements)
        self.prototyping_output = await PrototypeSolutions().run(self.ideation_output.content)

class InteractionDesigner(Role):
    """
    Represents an Interaction Designer role in the Prototyping and Testing stages of a service design process.

    Attributes:
        name (str): Name of the interaction designer.
        profile (str): Role profile, default is 'Interaction Designer'.
        goal (str): Primary goal or responsibility of the interaction designer.
    """

    def __init__(
            self,
            name: str = "Dana",
            profile: str = "Interaction Designer",
            goal: str = "Develop prototypes to visualize service solutions and prepare them for testing",
            ideas: str = None
    ) -> None:
        """Initializes the Interaction Designer with given attributes."""
        super().__init__(name, profile, goal)
        self.prototyping_details_output = None

    async def run_actions(self, ideas):
        self.prototyping_details_output = await DevelopPrototypes().run(ideas)

class UsabilityAnalyst(Role):
    """
    Represents a Usability Analyst role in the Testing stage of a service design process.

    Attributes:
        name (str): Name of the usability analyst.
        profile (str): Role profile, default is 'Usability Analyst'.
        goal (str): Primary goal or responsibility of the usability analyst.
    """

    def __init__(
            self,
            name: str = "Evan",
            profile: str = "Usability Analyst",
            goal: str = "Test prototypes with users, gather feedback, and refine solutions",
    ) -> None:
        """Initializes the Usability Analyst with given attributes."""
        super().__init__(name, profile, goal)
        self.refinements_output = None
        self.feedback_output = None
        self.testing_output = None

    """async def run_actions(self, prototype_details):
        self.testing_output = await TestPrototypes().run(prototype_details)
        self.feedback_output = await GatherFeedback().run(self.testing_output.content)
        self.refinements_output = await RefineSolutions().run(self.feedback_output.content)"""


class ProductManager(Role):
    """
    Represents a Product Manager role in the service design process, focusing on aligning product features with user needs and business goals.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Primary goal or responsibility of the product manager.
    """

    def __init__(
            self,
            name: str = "Fiona",
            profile: str = "Product Manager",
            goal: str = "Align product features with user needs and business objectives",
    ) -> None:
        """Initializes the Product Manager with given attributes."""
        super().__init__(name, profile, goal)
        self.feature_plan_output = None

    async def choose_idea(self, ideation_results):
        while True:
            print("\nIdeas from Ideation Results:")
            for i, idea in enumerate(ideation_results, start=1):
                print(f"{i}. {idea['Idea']}")

            choice = input("\nChoose an idea to elaborate (enter the number) or type 'exit' to finish: ")
            if choice.lower() == 'exit':
                break

            try:
                selected_idea_index = int(choice) - 1
                if 0 <= selected_idea_index < len(ideation_results):
                    selected_idea = ideation_results[selected_idea_index]['Idea']
                    print(f"\nSelected Idea: {selected_idea}\n")

                    # AI to elaborate on the selected idea
                    elaboration_prompt = f"Elaborate on the idea: '{selected_idea}'. Provide a detailed explanation and potential implementation steps."
                    elaboration = await ai_func(elaboration_prompt)
                    print(f"\nAI's Elaboration on the Idea:\n{elaboration}")

                else:
                    print("Invalid choice. Please enter a number from the list.")
            except ValueError:
                print("Please enter a valid number.")

    async def run_actions(self, ideation_results):
        self.feature_plan_output = await DevelopFeaturePlan().run(ideation_results)
