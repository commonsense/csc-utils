# Import everything from conceptnet.admin for backwards compatibility.
globals().update(__import__('conceptnet.admin', [], [], 'hack').__dict__)
