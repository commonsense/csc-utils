# Import everything from conceptnet.webapi.urls for backwards compatibility.
globals().update(__import__('conceptnet.webapi.urls', [], [], 'hack').__dict__)
