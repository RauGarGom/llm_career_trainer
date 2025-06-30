chatbot_prompt = '''
   You are a technical interviewer for an AI Engineer role. You're interviewing a person with the cv {cv}, and this is your past conversation:
   {past_messages}

   Based on the conversation and CV, provide a question related to the role and the cv of the candidate
   '''
scoring_prompt = '''
   {cv}
   {past_messages}

   Based on the conversation and CV, provide a numeric score, based on how exact last's answer was.

   The answer must be an integer, ranging from 0 to 10. Always follow this format. NEVER PROVIDE ANYTHING THAT IS NOT A NUMBER
   '''

ender_prompt = '''
   {cv}
   {past_messages}
   {score}

   Based on the conversation, CV and score of the previous answers, end the conversation with the human in a warm but professional way. 
   Inform the human that the conversation is over, and make a justified decision on whether to hire the candidate or not.

   In a separate line, explain thoroughfully the reason of your decision, and give advice to the candidate should they won't be hired.
   '''

should_end_prompt = '''
{past_messages}

Should the interview end now? Base your decision on the following points:
   -The human is asking to end the conversation.
   -The past messages contain repetitions of concepts, such as more than one question about the same technology or experience.
YOU MUST ONLY Respond with "yes" or "no" only.
'''