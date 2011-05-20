{
    "type":"application",
    "name":"eoiagents",
    "description": "ION External Observatories Initiative, Dataset Agent application",
    "version": "0.1",
    "mod": ("ion.core.pack.processapp", [
        'JavaAgentWrapper',
        'ion.integration.eoi.agent.java_agent_wrapper',
        'AttributeStoreService'], {}
    ),
    "registered": [
       "eoiagents"
    ],
    "applications": [
        "ioncore"
    ]
}
