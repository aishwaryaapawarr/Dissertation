import asyncio
from metagpt.roles import UserResearcher
from metagpt.schema import Message

async def test_user_researcher():
    # Instantiate the UserResearcher
    user_researcher = UserResearcher(name="Alice", profile="User Researcher",
                                     goal="Understand user needs and behaviors",
                                     constraints="Follow ethical guidelines")

    # Create a mock message
    # Adjust the message content to fit your requirements
    mock_message = Message(role="BOSS", content="Improve online banking for elderly")

    # Run the UserResearcher's run method with the mock message
    await user_researcher.run(mock_message)

    # Add additional checks or print statements if needed

# Run the test
asyncio.run(test_user_researcher())
