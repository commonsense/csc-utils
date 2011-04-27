# Import everything from conceptnet.models for backwards compatibility.
globals().update(__import__('conceptnet.models', [], [], 'hack').__dict__)
