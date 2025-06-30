from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.messages import AnyMessage


class OverallState(BaseModel):
    messages: list[AnyMessage] = Field(description="A list of Langchain messages from the past conversation")
    cv: Optional[str] = Field(descrixption="A string containing professional and academic background of a candidate")
    score: Optional[int] = Field(description="A number ranging from 0 to 10, depending on how good the las answer from the human was")
    num_questions: int = Field(description="Number of questions asked to the human")
    should_end: bool = Field(default=False, description="Whether the LLM thinks the interview should end")
    