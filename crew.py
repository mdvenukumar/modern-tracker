import os
GEMINI_API_KEY = "AIzaSyCFIrdaamYwTpNm2JLtpYRsQmB8Ik6y09g"


from crewai import Agent, Task, Crew, Process

# Requirement Analyst Agent
requirements_agent = Agent(
    role='Requirement Analyst',
    goal='Gather and refine requirements for the landing page based on user input.',
    backstory='A skilled strategist who ensures clear and actionable requirements.',
    verbose=True
)

# Validation Specialist Agent
validation_agent = Agent(
    role='Validation Specialist',
    goal='Validate the interpreted requirements with the user to confirm accuracy.',
    backstory='An expert in communication, clarifying user expectations.',
    verbose=True
)

# Wireframing Agent
wireframing_agent = Agent(
    role='Wireframer',
    goal='Develop a basic layout using HTML and TailwindCSS based on requirements.',
    backstory='A layout designer skilled in structuring intuitive web pages.',
    verbose=True
)

# Designer Agent
design_agent = Agent(
    role='Designer',
    goal='Apply design principles to the wireframe, including color and typography.',
    backstory='A creative designer focused on user-centered aesthetics.',
    verbose=True
)

# Developer Agent
development_agent = Agent(
    role='Developer',
    goal='Transform the wireframe into an interactive page using HTML, TailwindCSS, and JavaScript.',
    backstory='An expert in coding high-quality and responsive web pages.',
    verbose=True
)

# CEO for Final Review
ceo_agent = Agent(
    role='CEO',
    goal='Review the final landing page and provide final feedback or approval.',
    backstory='An executive ensuring quality and brand alignment in the final product.',
    verbose=True
)

# Define each task
requirements_task = Task(
    description='Gather and clarify requirements for the landing page.',
    expected_output='A detailed list of user requirements for the landing page.',
    agent=requirements_agent
)

validation_task = Task(
    description='Validate the refined requirements with the user.',
    expected_output='User confirmation of the requirements to proceed to wireframing.',
    agent=validation_agent
)

wireframing_task = Task(
    description='Create a basic HTML/TailwindCSS wireframe based on user-approved requirements.',
    expected_output='A skeleton layout with placeholders and basic structure.',
    agent=wireframing_agent
)

design_task = Task(
    description='Apply design elements to the wireframe.',
    expected_output='An aesthetically pleasing design with color, typography, and visual elements.',
    agent=design_agent
)

development_task = Task(
    description='Complete the landing page with HTML, TailwindCSS, and JavaScript.',
    expected_output='A responsive and interactive landing page.',
    agent=development_agent
)

final_review_task = Task(
    description='Review the completed landing page and provide final feedback or approval.',
    expected_output='CEO approval or final feedback on the landing page.',
    agent=ceo_agent
)

# Assemble the crew
landing_page_crew = Crew(
    agents=[requirements_agent, validation_agent, wireframing_agent, design_agent, development_agent, ceo_agent],
    tasks=[requirements_task, validation_task, wireframing_task, design_task, development_task, final_review_task],
    process=Process.sequential,
    verbose=True,
    memory=True,
    manager_llm="gemini-ai",  # Assuming Gemini AI is the manager LLM
    planning=True  # Enable planning for structured execution
)

# Start the crew
result = landing_page_crew.kickoff(inputs={'website_description': 'A landing page for a modern tech startup.'})
print(result)
