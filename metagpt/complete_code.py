# complete_code.py
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


class CreateEmpathyMap(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Create an empathy map based on user interview data."

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def save_empathy_map(self, docs_path, empathy_map):
        empathy_map_file = docs_path / "empathy_map.md"
        logger.info(f"Saving Summarized Insights to {empathy_map_file}")

        if isinstance(empathy_map, str):
            empathy_map_file.write_text(empathy_map)
        else:
            empathy_map_file.write_text(json_to_markdown(empathy_map.dict()))
        empathy_map_image_path = docs_path / "empathy_map.png"
        self.create_empathy_map_image(empathy_map_file, empathy_map_image_path)

    def create_empathy_map_image(self, md_filepath, output_path):
        empathy_map_data = self.parse_markdown(md_filepath)
        self.generate_empathy_map_image(empathy_map_data, output_path)

    def parse_markdown(self, md_filepath):
        with open(md_filepath, 'r') as file:
            content = file.readlines()

        empathy_map = {}
        current_section = None
        for line in content:
            if line.startswith('Thoughts:') or line.startswith('Feelings:') or line.startswith('Pain Points:') or line.startswith('Goals:'):
                current_section = line.strip().split(':')[0]
                empathy_map[current_section] = ''
            elif current_section and line.startswith('- '):
                empathy_map[current_section] += line[2:].strip() + '\n'

        return empathy_map

    def generate_empathy_map_image(self, empathy_map, output_path):
        # Define image size and background color
        img = Image.new('RGB', (1024, 768), color='white')
        d = ImageDraw.Draw(img)

        # Define font
        try:
            font = ImageFont.truetype("arial.ttf", size=14)
        except IOError:
            font = ImageFont.load_default()

        # Define positions for the section titles
        title_positions = {
            "Thoughts": (10, 10),
            "Feelings": (10, 384),
            "Pain Points": (512, 10),
            "Goals": (512, 384)
        }

        # Define starting positions for the section contents just below the titles
        content_positions = {
            "Thoughts": (10, 50),
            "Feelings": (10, 420),
            "Pain Points": (512, 50),
            "Goals": (512, 420)
        }

        # Fixed increment for line spacing, may require adjustment
        line_height = 20

        # Function to draw wrapped text
        def draw_wrapped_text(draw, text, position, font, line_height):
            x, y = position
            for line in text.split('\n'):
                draw.text((x, y), line, font=font, fill="black")
                y += line_height

        # Draw the section titles and contents
        for section, position in title_positions.items():
            # Draw the title
            d.text(position, section, font=font, fill="black")
            # Draw the content with fixed line height increments
            draw_wrapped_text(d, empathy_map[section], content_positions[section], font, line_height)

        # Save the image
        img.save(output_path)

    async def run(self, interview_output, *args, **kwargs) -> ActionOutput:
        # Logic for creating the empathy map
        prompt_template, format_example = get_template(template0, CONFIG.prompt_format)
        prompt = prompt_template.format(context=interview_output, format_example=format_example)

        logger.info(f"Creating an empathy map")
        empathy_map = await ai_func(prompt)

        if isinstance(empathy_map, ActionOutput):
            ws_name = empathy_map.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=empathy_map)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_empathy_map(docs_path, empathy_map)

        class InstructContent(BaseModel):
            instructions: str = "Follow the interview output to create an empathy map."

        return ActionOutput(content=empathy_map, instruct_content=InstructContent())


class UserInterview(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Generate interview questions and simulate an interview based on a service design problem."

    def select_participants(self):
        # Broad categories of stakeholders typically relevant in various service design contexts
        participants = [
            "industry expert",
            "end-user or customer",
            "service staff or employee",
            "business strategist",
            "design and usability expert"
        ]
        return participants

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def save_interview_transcript(self, docs_path, interview_transcript):
        interview_transcript_file = docs_path / "interview_transcript.md"
        logger.info(f"Saving Interview Transcript to {interview_transcript_file}")
        if isinstance(interview_transcript, str):
            interview_transcript_file.write_text(interview_transcript)
        else:
            interview_transcript_file.write_text(json_to_markdown(interview_transcript.dict()))

    async def run(self, service_design_problem, *args, **kwargs) -> ActionOutput:
        selected_participants = self.select_participants()
        selected_participants_str = ', '.join(selected_participants)
        prompt_template, format_example = get_template(templates, CONFIG.prompt_format)
        prompt = prompt_template.format(service_design_problem=service_design_problem,
                                        selected_participants=selected_participants_str,
                                        format_example=format_example)
        logger.info(f"Conducting user interview for service design problem")
        interview_transcript = await ai_func(prompt)
        if isinstance(interview_transcript, ActionOutput):
            ws_name = interview_transcript.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=interview_transcript)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_interview_transcript(docs_path, interview_transcript)

        class InstructContent(BaseModel):
            instructions: str = "Follow the interview format to gather user insights."

        return ActionOutput(content=interview_transcript, instruct_content=InstructContent())


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


class SummarizeInsights(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Summarize key insights from user interviews."

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def save_summarized_insights(self, docs_path, summarized_insights):
        summarized_insights_file = docs_path / "summarized_insights.md"
        logger.info(f"Saving Summarized Insights to {summarized_insights_file}")

        if isinstance(summarized_insights, str):
            summarized_insights_file.write_text(summarized_insights)
        else:
            summarized_insights_file.write_text(json_to_markdown(summarized_insights.dict()))

    async def run(self, interview_content, *args, **kwargs) -> ActionOutput:
        prompt_template, format_example = get_template(templates1, CONFIG.prompt_format)
        prompt = prompt_template.format(context=interview_content, format_example=format_example)

        logger.info(f"Summarizing insights from interview content")
        summarized_insights = await ai_func(prompt)

        if isinstance(summarized_insights, ActionOutput):
            ws_name = summarized_insights.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=summarized_insights)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_summarized_insights(docs_path, summarized_insights)

        class InstructContent(BaseModel):
            instructions: str = "Provide a summary that captures the essence of the user's feedback."

        return ActionOutput(content=summarized_insights, instruct_content=InstructContent())

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


class DefineProblemStatements(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Transform user insights into concise problem statements for service design improvement."

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass
        workspace.mkdir(parents=True, exist_ok=True)

    async def save_problem_statements(self, docs_path, problem_statements):
        problem_statements_file = docs_path / "problem_statements.md"
        logger.info(f"Saving problem statements to {problem_statements_file}")

        if isinstance(problem_statements, str):
            problem_statements_file.write_text(problem_statements)
        else:
            problem_statements_file.write_text(json_to_markdown(problem_statements.dict()))

    async def run(self, context):
        prompt_template, format_example = get_template(templates2, CONFIG.prompt_format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        problem_statements = await ai_func(prompt)
        if isinstance(problem_statements, ActionOutput):
            ws_name = problem_statements.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=problem_statements)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_problem_statements(docs_path, problem_statements)

        class InstructContent(BaseModel):
            instructions: str = "Transform user insights into clear and actionable problem statements that highlight areas for service design improvement."

        return ActionOutput(content=problem_statements, instruct_content=InstructContent())


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


class IdeateSolutions(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Generate creative ideas based on defined problem statements."

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def save_ideation_results(self, docs_path, ideation_results):
        ideation_results_file = docs_path / "ideation_results.md"
        logger.info(f"Saving ideation results to {ideation_results_file}")

        if isinstance(ideation_results, str):
            ideation_results_file.write_text(ideation_results)
        else:
            ideation_results_file.write_text(json_to_markdown(ideation_results.dict()))

    async def run(self, problem_statements, *args, **kwargs) -> ActionOutput:
        prompt_template, format_example = get_template(templates3, CONFIG.prompt_format)
        prompt = prompt_template.format(context=problem_statements, format_example=format_example)

        logger.info(f"Generating ideation based on problem statements")
        ideation_results = await ai_func(prompt)
        if isinstance(ideation_results, ActionOutput):
            ws_name = ideation_results.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=ideation_results)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_ideation_results(docs_path, ideation_results)

        class InstructContent(BaseModel):
            instructions: str = "Think outside the box and propose innovative ideas."

        return ActionOutput(content=ideation_results, instruct_content=InstructContent())

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



class PrototypeSolutions(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Develop a prototyping plan for selected ideas."

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def save_prototyping_plan(self, docs_path, prototyping_plan):
        prototyping_plan_file = docs_path / "prototyping_plan.md"
        logger.info(f"Saving prototyping_plan to {prototyping_plan_file}")

        if isinstance(prototyping_plan, str):
            prototyping_plan_file.write_text(prototyping_plan)
        else:
            prototyping_plan_file.write_text(json_to_markdown(prototyping_plan.dict()))

    async def run(self, ideas, *args, **kwargs) -> ActionOutput:
        prompt_template, format_example = get_template(templates4, CONFIG.prompt_format)
        prompt = prompt_template.format(context=ideas, format_example=format_example)

        logger.info(f"Developing a prototyping plan based on ideas")
        prototyping_plan = await ai_func(prompt)

        if isinstance(prototyping_plan, ActionOutput):
            ws_name = prototyping_plan.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=prototyping_plan)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_prototyping_plan(docs_path, prototyping_plan)

        class InstructContent(BaseModel):
            instructions: str = "Draft a clear and actionable prototyping plan."

        return ActionOutput(content=prototyping_plan, instruct_content=InstructContent())

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


class DevelopPrototypes(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, ideas, *args, **kwargs) -> ActionOutput:
        prototyping_prompt = f"""
        From the following ideas:
        {ideas}

        Create a detailed plan for developing interactive prototypes that visualize the service solutions. Include the tools and processes you would use and how you would prepare the prototypes for user testing.
        """
        prototyping_details = await ai_func(prototyping_prompt)

        class InstructContent(BaseModel):
            instructions: str = "Detail the prototyping process with a focus on interaction design and preparation for testing."

        return ActionOutput(content=prototyping_details, instruct_content=InstructContent())


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


class DevelopFeaturePlan(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Develop a feature plan based on ideation results and business objectives."

    async def run(self, ideation_results, *args, **kwargs) -> ActionOutput:
        prompt_template, format_example = get_template(templates5, CONFIG.prompt_format)
        prompt = prompt_template.format(context=ideation_results, format_example=format_example)

        logger.info(f"Developing feature plan based on ideation results")
        feature_plan_details = await ai_func(prompt)

        if isinstance(feature_plan_details, ActionOutput):
            ws_name = feature_plan_details.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=feature_plan_details)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_feature_plan(docs_path, feature_plan_details)

        class InstructContent(BaseModel):
            instructions: str = "Detail the feature plan with a focus on aligning with user needs and business objectives."

        return ActionOutput(content=feature_plan_details, instruct_content=InstructContent())

    async def save_feature_plan(self, docs_path, feature_plan):
        feature_plan_file = docs_path / "feature_plan.md"
        logger.info(f"Saving feature plan to {feature_plan_file}")

        if isinstance(feature_plan, str):
            feature_plan_file.write_text(feature_plan)
        else:
            feature_plan_file.write_text(json_to_markdown(feature_plan.dict()))


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
