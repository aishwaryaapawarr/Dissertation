from utils import get_template, json_to_markdown
from metagpt.actions import Action, ActionOutput
from temp import template0, templates, templates1, templates2, templates3, templates4, templates5
from PIL import Image, ImageDraw, ImageFont
from metagpt.roles import Role
import shutil
from pathlib import Path
from main_action import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.llm import ai_func
from pydantic import BaseModel
import textwrap

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
        formatted_transcript = "Interview Transcript:\n" + interview_transcript
        if isinstance(formatted_transcript, ActionOutput):
            ws_name = formatted_transcript.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=formatted_transcript)
        workspace = WORKSPACE_ROOT / ws_name
        docs_path = workspace / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        await self.save_interview_transcript(docs_path, interview_transcript)

        class InstructContent(BaseModel):
            instructions: str = "Follow the interview format to gather user insights."

        return ActionOutput(content=interview_transcript, instruct_content=InstructContent())

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
