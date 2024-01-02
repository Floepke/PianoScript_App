

class Beam:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the slur tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            ...

        elif event_type == 'leftclick+move':
            ...
        
        elif event_type == 'leftrelease':
            ...

        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...

        # right mouse button handling:
        elif event_type == 'rightclick':
            ...

        elif event_type == 'rightclick+move':
            ...
        
        elif event_type == 'rightrelease':
            ...