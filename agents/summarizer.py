from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


def summarizer(state,detailed: bool = False) -> str:
    """
    Generate fitness and nutrition summary report using LLM after complete consultation.

    Args:
        state: Current conversation state with structured agent data
        detailed: Boolean flag for summary length (False=concise, True=detailed)

    Returns:
        Formatted summary string
    """
    # structured data from agents
    messages = state.get("messages", [])
    fitness_plan = state.get("fitness_plan", {})
    nutrition_plan = state.get("nutrition_plan", {})
    supplement_recommendations = state.get("supplements", {})
    user_goals = state.get("user_goals", {})

    if not messages and not any(
        [fitness_plan, nutrition_plan, supplement_recommendations]
    ):
        return "No consultation data to summarize."

    consultation_context = ""

    # Add user goals and constraints
    if user_goals:
        consultation_context += f"User Goals: {user_goals}\n\n"

    # Add agent recommendations
    if fitness_plan:
        consultation_context += f"Fitness Plan: {fitness_plan}\n\n"

    if nutrition_plan:
        consultation_context += f"Nutrition Plan: {nutrition_plan}\n\n"

    if supplement_recommendations:
        consultation_context += (
            f"Supplement Recommendations: {supplement_recommendations}\n\n"
        )

    # Add conversation messages if available
    if messages:
        conversation_text = ""
        for msg in messages:
            conversation_text += f"{msg.get('content', '')}\n"
        consultation_context += f"Conversation Details: {conversation_text}"

    if not consultation_context.strip():
        return "No consultation content to summarize."

    # System prompt for summarization
    summary_length = (
        "detailed and comprehensive" if detailed else "concise but complete"
    )

    system_prompt = f"""
        You are a professional fitness and nutrition coach creating a {summary_length} summary for your client.

        Your summary should include:

        1. CLIENT GOALS & TIMELINE
        - Primary fitness objectives
        - Target timeline and milestones
        - Any constraints or limitations mentioned

        2. WORKOUT PLAN ACTION ITEMS
        - Weekly schedule and structure  
        - Key exercises and progression
        - Specific modifications if any

        3. NUTRITION PLAN ACTION ITEMS
        - Daily calorie and macro targets
        - Meal timing and structure
        - Key dietary recommendations

        4. SUPPLEMENT RECOMMENDATIONS
        - Recommended supplements and dosages
        - Purpose/benefits of each
        - Any timing instructions

        Format as clear, actionable items that the user can easily follow and reference.
        Use an encouraging, professional coaching tone.
        Make it practical for text output with clear headers and bullet points.
    """

    user_prompt = f"""
        Here's the complete consultation data:

        {consultation_context}

        Please provide a {'detailed' if detailed else 'concise'} summary of this fitness and nutrition consultation that the client can use as their action plan.
    """

    try:
        # Call LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )

        if isinstance(response.content, list):
            summary = " ".join(str(item) for item in response.content).strip()
        else:
            summary = str(response.content).strip()

        # Format with header and disclaimer
        formatted_summary = f"""
            {'=' * 60} LIVE WELL AI - YOUR PERSONALIZED ACTION PLAN {'=' * 60}
            {summary}
            {'=' * 60} DISCLAIMER {'=' * 60}
            This plan is for informational purposes only. Please consult with healthcare professionals before starting any new fitness program or 
            taking supplements, especially if you have pre-existing conditions.
            {'=' * 60}
        """

        return formatted_summary

    except Exception as e:
        # Fallback to basic summary if LLM fails
        goal_count = len(user_goals) if user_goals else 0
        plan_items = sum(
            [
                1 if fitness_plan else 0,
                1 if nutrition_plan else 0,
                1 if supplement_recommendations else 0,
            ]
        )

        return f"""
            {'=' * 60} LIVE WELL AI - CONSULTATION SUMMARY {'=' * 60}

            Goals Identified: {goal_count}
            Plans Generated: {plan_items}

            Unable to generate detailed summary at this time.
            Your consultation data has been saved for review.

            {'=' * 60} DISCLAIMER {'=' * 60}
            This plan is for informational purposes only. Please consult with 
            healthcare professionals before starting any new fitness program or 
            taking supplements, especially if you have pre-existing conditions.
            {'=' * 60}
        """


# Usage examples:
# concise_summary = summarizer(state, detailed=False)
# detailed_summary = summarizer(state, detailed=True)
