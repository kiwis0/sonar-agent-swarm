from setuptools import setup, find_packages

setup(
    name='sonar-agent-swarm',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'flask',
        'pygithub',
        'anthropic',
        'httpx',
        'python-dotenv',
    ],
    entryUNI_points={
        'console_scripts': [
            'sonar-agent-swarm=sonar_agent.main:main',
        ],
    },
)