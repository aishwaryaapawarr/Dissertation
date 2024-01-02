#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""
import re
from abc import ABC
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_fixed

from typing import Dict, Type

from pydantic import BaseModel, create_model, root_validator, validator


from metagpt.actions.action_output import ActionOutput
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt.utils.custom_decoder import CustomDecoder


class Action(ABC):
    def __init__(self, name: str = "", context=None, llm: LLM = None):
        self.name: str = name
        if llm is None:
            llm = LLM()
        self.llm = llm
        self.context = context
        self.prefix = ""
        self.profile = ""
        self.desc = ""
        self.content = ""
        self.instruct_content = None

    def set_prefix(self, prefix, profile):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.profile = profile

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        return await self.llm.aask(prompt, system_msgs)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def _aask_v1(
        self,
        prompt: str,
        output_class_name: str,
        output_data_mapping: dict,
        system_msgs: Optional[list[str]] = None,
        format="markdown",  # compatible to original format
    ) -> ActionOutput:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        content = await self.llm.aask(prompt, system_msgs)
        logger.debug(content)
        output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)

        if format == "json":
            pattern = r"\[CONTENT\](\s*\{.*?\}\s*)\[/CONTENT\]"
            matches = re.findall(pattern, content, re.DOTALL)

            for match in matches:
                if match:
                    content = match
                    break

            parsed_data = CustomDecoder(strict=False).decode(content)

        else:  # using markdown parser
            parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)

        logger.debug(parsed_data)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(content, instruct_content)

    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")


# !/usr/bin/env python
# coding: utf-8
"""
@Time    : 2023/7/11 10:03
@Author  : chengmaoyu
@File    : action_output
"""

class ActionOutput:
    content: str
    instruct_content: BaseModel

    def __init__(self, content: str, instruct_content: BaseModel):
        self.content = content
        self.instruct_content = instruct_content

    @classmethod
    def create_model_class(cls, class_name: str, mapping: Dict[str, Type]):
        new_class = create_model(class_name, **mapping)

        @validator('*', allow_reuse=True)
        def check_name(v, field):
            if field.name not in mapping.keys():
                raise ValueError(f'Unrecognized block: {field.name}')
            return v

        @root_validator(pre=True, allow_reuse=True)
        def check_missing_fields(values):
            required_fields = set(mapping.keys())
            missing_fields = required_fields - set(values.keys())
            if missing_fields:
                raise ValueError(f'Missing fields: {missing_fields}')
            return values

        new_class.__validator_check_name = classmethod(check_name)
        new_class.__root_validator_check_missing_fields = classmethod(check_missing_fields)
        return new_class
